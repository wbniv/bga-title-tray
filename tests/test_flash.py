"""Only relevant selected-tab title transitions should flash the panel text."""
import json
import os
import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from native_host import host


def snapshot(tab_id, title, selected_id=None, selected_visible=None,
             offer_visible=None, lobby_visible=None):
    return {'type': 'snapshot', 'version': 1, 'selectedId': selected_id or tab_id,
            'selectedVisible': selected_visible, 'selectedOfferVisible': offer_visible,
            'selectedLobbyVisible': lobby_visible,
            'tabs': [{'id': tab_id, 'windowId': 1, 'title': title, 'paused': False}]}


class FakeHost:
    def __init__(self):
        self.tabs = []
        self.selected = None
        self.selected_visible = None
        self.selected_offer_visible = None
        self.selected_lobby_visible = None
        self.flashes = []
        self.flash_id = 0
        self.flash_active = False
        self.flash_tab_id = None
        self.flash_until = 0
        self.flash_title = ''
        self.flash_visible_at_event = None
        self.flash_preview = False
        self.flash_kind = None
        self.flash_state = None
        self.play_offer_seen = False

    def refresh_menu(self):
        pass

    def flash_text(self, title, visible_at_event=None, preview=False):
        host.Host.flash_text(self, title, visible_at_event, preview)
        self.flashes.append(title)

    def clear_flash(self):
        host.Host.clear_flash(self)

    def flash_state_is_current(self, title):
        return host.Host.flash_state_is_current(self, title)


class FlashTest(unittest.TestCase):
    def test_empty_tabs_and_unselected_multiple_tabs_have_clear_labels(self):
        fake = FakeHost()
        with patch.object(host, 'incoming', queue.SimpleQueue()):
            host.Host.drain(fake)
        self.assertEqual(host.Host.status(fake)['title'], 'BGA · no open tab')

        events = queue.SimpleQueue()
        events.put({'type': 'snapshot', 'version': 1, 'selectedId': None,
                    'selectedVisible': None, 'tabs': [
                        {'id': 42, 'windowId': 1, 'title': 'Hearts • Board Game Arena'},
                        {'id': 43, 'windowId': 2, 'title': 'Chess • Board Game Arena'}]})
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(host.Host.status(fake)['title'], 'BGA · choose tab')

    def test_host_bounds_long_titles_and_reports_disconnected_widget_fallback(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        events.put(snapshot(42, 'x' * 1100))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertEqual(len(state['title']), 1024)
        self.assertEqual(len(state['tabs'][0]['title']), 1024)
        status_script = Path(__file__).resolve().parents[1] / 'bin/bga-title-tray-status'
        with tempfile.TemporaryDirectory() as runtime_dir:
            env = os.environ.copy()
            env['XDG_RUNTIME_DIR'] = runtime_dir
            result = subprocess.run([str(status_script)], env=env, check=True,
                                    capture_output=True, text=True)
        disconnected = json.loads(result.stdout)
        self.assertFalse(disconnected['connected'])
        self.assertEqual(disconnected['title'], 'BGA · disconnected')

    def test_selected_search_to_observed_play_title_stays_active(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for 1 player... • Board Game Arena'
        playing = '◣ Play • Board Game Arena'
        events.put(snapshot(42, waiting))
        events.put(snapshot(42, playing))
        events.put(snapshot(42, playing))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [playing])
        state = host.Host.status(fake)
        self.assertEqual(state['flashTitle'], playing)
        self.assertTrue(state['flashActive'])
        self.assertEqual(state['flashUntil'], 0)
        self.assertEqual(state['flashKind'], 'play')

    def test_no_flash_on_initial_snapshot_tab_change_or_return_to_lobby(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        events.put(snapshot(42, '◣ Play • Board Game Arena'))
        events.put(snapshot(43, 'Searching for players... • Board Game Arena'))
        events.put(snapshot(43, 'Board Game Arena'))
        events.put(snapshot(44, '◣ Play • Board Game Arena'))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [])

    def test_title_match_requires_game_start(self):
        waiting = 'Searching for 2 players... • Board Game Arena'
        self.assertTrue(host.game_started_after_search(waiting, 'Starting a game • Board Game Arena'))
        self.assertTrue(host.game_started_after_search(
            waiting, '◢ You must choose 3 cards • Hearts • Board Game Arena'))
        self.assertFalse(host.game_started_after_search(waiting, '1 more player • Board Game Arena'))
        self.assertFalse(host.game_started_after_search(waiting, 'Play now • Board Game Arena'))
        self.assertFalse(host.game_started_after_search('Board Game Arena', '◣ Play • Board Game Arena'))

    def test_new_you_prompt_flashes_but_status_symbol_does_not(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        other = 'Josianne must play a card • Hearts • Board Game Arena'
        your_turn = '◢ You must play a card • Hearts • Board Game Arena'
        changed_symbol = '◣ You must play a card • Hearts • Board Game Arena'
        new_action = '◣ You must choose a card • Hearts • Board Game Arena'
        for title in (other, your_turn, changed_symbol, new_action, new_action):
            events.put(snapshot(42, title))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [your_turn, new_action])

    def test_background_you_prompt_flashes_on_initial_snapshot_and_tab_change(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        first = '◢ You must play a card • Hearts • Board Game Arena'
        second = '◢ You must choose a card • Hearts • Board Game Arena'
        events.put(snapshot(42, first, selected_visible=False))
        events.put(snapshot(43, second, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [first, second])

    def test_you_alert_resumes_each_time_focus_leaves_while_turn_remains(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        other = 'Josianne must play a card • Hearts • Board Game Arena'
        your_turn = '◢ You must play a card • Hearts • Board Game Arena'
        events.put(snapshot(42, other, selected_visible=True))
        events.put(snapshot(42, your_turn, selected_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [])

        events.put(snapshot(42, your_turn, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [your_turn])
        first_flash_id = fake.flash_id

        events.put(snapshot(42, your_turn, selected_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertFalse(fake.flash_active)

        events.put(snapshot(42, your_turn, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [your_turn, your_turn])
        self.assertGreater(fake.flash_id, first_flash_id)

        events.put(snapshot(42, other, selected_visible=True))
        events.put(snapshot(42, other, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertFalse(fake.flash_active)
        self.assertEqual(fake.flashes, [your_turn, your_turn])

    def test_play_offer_resumes_after_focus_only_while_offer_is_visible(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for 1 player... • Board Game Arena'
        playing = '◣ Play • Board Game Arena'
        events.put(snapshot(42, waiting, selected_visible=True, offer_visible=False))
        events.put(snapshot(42, playing, selected_visible=True, offer_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [])

        events.put(snapshot(42, playing, selected_visible=False, offer_visible=True))
        events.put(snapshot(42, playing, selected_visible=True, offer_visible=True))
        events.put(snapshot(42, playing, selected_visible=False, offer_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [playing, playing])

        events.put(snapshot(42, playing, selected_visible=False, offer_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertFalse(fake.flash_active)

    def test_confirmed_background_starts_alert_after_unknown_focus(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        your_turn = '◢ You must play a card • Hearts • Board Game Arena'
        events.put(snapshot(42, your_turn, selected_visible=None))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [])

        events.put(snapshot(42, your_turn, selected_visible=False))
        events.put(snapshot(42, your_turn, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [your_turn])
        self.assertIs(fake.flash_visible_at_event, False)

    def test_flash_id_increases_for_consecutive_actions(self):
        fake = FakeHost()
        fake.flash_text('◢ You must play a card • Hearts • Board Game Arena')
        first = fake.flash_id
        fake.flash_text('◢ You must choose a card • Hearts • Board Game Arena')
        self.assertGreater(fake.flash_id, first)
        self.assertTrue(fake.flash_active)
        self.assertEqual(fake.flash_until, 0)

    def test_focus_by_any_means_clears_alert_after_transition(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for 1 player... • Board Game Arena'
        playing = '◣ Play • Board Game Arena'
        events.put(snapshot(42, waiting, selected_visible=True))
        events.put(snapshot(42, playing, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertTrue(state['flashActive'])
        self.assertIs(state['flashVisibleAtEvent'], False)
        events.put(snapshot(42, playing, selected_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertTrue(state['selectedVisible'])
        self.assertFalse(state['flashActive'])
        self.assertFalse(state['flashPreview'])

    def test_play_alert_survives_symbol_change_and_unknown_focus(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        events.put(snapshot(42, 'Searching for 3 player(s)... • Board Game Arena',
                            selected_visible=False))
        events.put(snapshot(42, '◣ Play • Board Game Arena', selected_visible=False))
        events.put(snapshot(42, '◢ Play • Board Game Arena', selected_visible=None))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertTrue(host.Host.status(fake)['flashActive'])
        self.assertEqual(fake.flashes, ['◣ Play • Board Game Arena'])

    def test_play_alert_stops_when_offer_disappears(self):
        for replacement in ('Searching for players... • Board Game Arena',
                            'Board Game Arena', 'Hearts • Board Game Arena'):
            with self.subTest(replacement=replacement):
                fake = FakeHost()
                events = queue.SimpleQueue()
                events.put(snapshot(42, 'Searching for 1 player... • Board Game Arena',
                                    selected_visible=False))
                events.put(snapshot(42, '◣ Play • Board Game Arena', selected_visible=False))
                events.put(snapshot(42, replacement, selected_visible=False))
                with patch.object(host, 'incoming', events):
                    host.Host.drain(fake)
                state = host.Host.status(fake)
                self.assertEqual(state['title'], replacement)
                self.assertFalse(state['flashActive'])
                self.assertEqual(fake.flashes, ['◣ Play • Board Game Arena'])

    def test_play_alert_stops_when_offer_screen_disappears_with_stale_title(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for players... • Board Game Arena'
        playing = 'Play • Board Game Arena'
        events.put(snapshot(42, waiting, selected_visible=False, offer_visible=False))
        events.put(snapshot(42, playing, selected_visible=False, offer_visible=False))
        events.put(snapshot(42, playing, selected_visible=False, offer_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertTrue(host.Host.status(fake)['flashActive'])
        self.assertTrue(fake.play_offer_seen)

        events.put(snapshot(42, playing, selected_visible=False, offer_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertEqual(state['title'], playing)
        self.assertFalse(state['flashActive'])
        self.assertFalse(state['playOfferSeen'])

        events.put(snapshot(42, playing, selected_visible=False, offer_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertTrue(host.Host.status(fake)['flashActive'])
        self.assertEqual(fake.flashes, [playing, playing])

    def test_lobby_label_follows_page_state_without_losing_raw_title(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for 1 player... • Board Game Arena'
        playing = 'Play • Board Game Arena'
        events.put(snapshot(42, waiting, selected_visible=False,
                            offer_visible=False, lobby_visible=False))
        events.put(snapshot(42, playing, selected_visible=False,
                            offer_visible=True, lobby_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertTrue(fake.flash_active)
        self.assertEqual(host.Host.status(fake)['title'], playing)

        events.put(snapshot(42, playing, selected_visible=False,
                            offer_visible=False, lobby_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertEqual(state['title'], 'Play now! • Board Game Arena')
        self.assertEqual(state['rawTitle'], playing)
        self.assertFalse(state['flashActive'])

        events.put(snapshot(42, waiting, selected_visible=False,
                            offer_visible=False, lobby_visible=False))
        events.put(snapshot(42, playing, selected_visible=False,
                            offer_visible=True, lobby_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(host.Host.status(fake)['title'], playing)
        self.assertTrue(fake.flash_active)
        self.assertEqual(fake.flashes, [playing, playing])

    def test_play_alert_is_replaced_by_new_you_instruction(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        waiting = 'Searching for 1 player... • Board Game Arena'
        playing = '◣ Play • Board Game Arena'
        action = '◢ You must play a card • Hearts • Board Game Arena'
        for title in (waiting, playing, action):
            events.put(snapshot(42, title, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        state = host.Host.status(fake)
        self.assertEqual(fake.flashes, [playing, action])
        self.assertTrue(state['flashActive'])
        self.assertEqual(state['flashKind'], 'you')

    def test_you_alert_ends_when_instruction_disappears(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        for title in ('Josianne must play • Hearts • Board Game Arena',
                      '◢ You must play a card • Hearts • Board Game Arena',
                      'Dougler must play • Hearts • Board Game Arena'):
            events.put(snapshot(42, title, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertFalse(host.Host.status(fake)['flashActive'])

    def test_direct_game_title_alert_ends_when_title_changes(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        for title in ('Searching for 1 player... • Board Game Arena',
                      'Hearts • Table 123 • Board Game Arena',
                      'Board Game Arena'):
            events.put(snapshot(42, title, selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, ['Hearts • Table 123 • Board Game Arena'])
        self.assertFalse(host.Host.status(fake)['flashActive'])

    def test_selected_tab_change_clears_alert(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        events.put(snapshot(42, 'Searching for 1 player... • Board Game Arena',
                            selected_visible=False))
        events.put(snapshot(42, '◣ Play • Board Game Arena', selected_visible=False))
        events.put(snapshot(43, 'Board Game Arena', selected_visible=False))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertFalse(host.Host.status(fake)['flashActive'])

    def test_no_alert_when_selected_tab_already_focused(self):
        fake = FakeHost()
        events = queue.SimpleQueue()
        events.put(snapshot(42, 'Searching for 1 player... • Board Game Arena',
                            selected_visible=True))
        events.put(snapshot(42, '◣ Play • Board Game Arena', selected_visible=True))
        with patch.object(host, 'incoming', events):
            host.Host.drain(fake)
        self.assertEqual(fake.flashes, [])

    def test_manual_preview_bypasses_focus_gate(self):
        fake = FakeHost()
        fake.flash_text('◣ Play • Board Game Arena', preview=True)
        state = host.Host.status(fake)
        self.assertTrue(state['flashPreview'])
        self.assertTrue(state['flashActive'])
        self.assertGreater(state['flashUntil'], 0)
        with patch.object(host.time, 'time_ns', return_value=(state['flashUntil'] + 1) * 1_000_000):
            self.assertFalse(host.Host.status(fake)['flashActive'])


if __name__ == '__main__':
    unittest.main()

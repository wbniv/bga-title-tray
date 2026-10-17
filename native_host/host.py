#!/usr/bin/env python3
"""Chrome native messaging host, local control socket, and KDE tray entry."""
import json
import os
import queue
import re
import socket
import struct
import sys
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QSocketNotifier, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

SOCKET_PATH = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')) / 'bga-title-tray.sock'
MAX_MESSAGE = 1024 * 1024
incoming = queue.SimpleQueue()
SEARCHING_FOR_PLAYERS = re.compile(r'^\s*Searching for\b[^•]*\bplayers?\b', re.IGNORECASE)
GAME_START_TITLE = re.compile(r'^\W*(?:Play\s*$|Starting (?:a |the )?game\b|Game starting\b)',
                              re.IGNORECASE)
YOUR_ACTION = re.compile(r'^\W*(You\b.*)', re.IGNORECASE)
PLAY_TITLE = re.compile(r'^\W*Play\s*$', re.IGNORECASE)


def game_started_after_search(previous_title, current_title):
    """Recognize a game title replacing the selected tab's player search."""
    if not SEARCHING_FOR_PLAYERS.search(previous_title):
        return False
    parts = [part.strip() for part in current_title.split('•')]
    page_title = parts[0]
    game_page = (len(parts) >= 3 and parts[-1].casefold() == 'board game arena'
                 and not SEARCHING_FOR_PLAYERS.search(current_title))
    return bool(GAME_START_TITLE.match(page_title) or game_page)


def your_action(title):
    """Return the actionable title without BGA's changing status symbol."""
    page_title = title.split('•', 1)[0].strip()
    match = YOUR_ACTION.match(page_title)
    return match.group(1).strip().casefold() if match else None


def new_your_action(previous_title, current_title):
    action = your_action(current_title)
    return bool(action and action != your_action(previous_title))


def is_play_title(title):
    """Ignore BGA's changing leading status symbol and site suffix."""
    return bool(PLAY_TITLE.match(title.split('•', 1)[0].strip()))


def game_title_state(title):
    """Stable identity for a direct search-to-game title alert."""
    return re.sub(r'^\W*', '', title.strip()).casefold()


def read_messages():
    stream = sys.stdin.buffer
    while True:
        header = stream.read(4)
        if len(header) != 4:
            incoming.put({'type': 'quit'})
            return
        length = struct.unpack('=I', header)[0]
        if length > MAX_MESSAGE:
            incoming.put({'type': 'quit'})
            return
        payload = stream.read(length)
        if len(payload) != length:
            incoming.put({'type': 'quit'})
            return
        try:
            incoming.put(json.loads(payload))
        except (ValueError, UnicodeError):
            continue


def send(message):
    data = json.dumps(message, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(data)) + data)
    sys.stdout.buffer.flush()


class Host:
    def __init__(self, app):
        self.app = app
        self.tabs = []
        self.selected = None
        self.selected_visible = None
        self.selected_offer_visible = None
        self.selected_lobby_visible = None
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
        self.menu = QMenu()
        icon = QIcon.fromTheme('applications-games')
        if icon.isNull():
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor('#2563a6'))
            painter = QPainter(pixmap)
            painter.setPen(QColor('white'))
            painter.setFont(QFont('Sans Serif', 19, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), 0x84, 'B')
            painter.end()
            icon = QIcon(pixmap)
        self.tray = QSystemTrayIcon(icon)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.activated)
        self.tray.show()
        self.server = socket.socket(socket.AF_UNIX)
        if SOCKET_PATH.exists():
            try:
                probe = socket.socket(socket.AF_UNIX)
                probe.settimeout(.2)
                probe.connect(str(SOCKET_PATH))
                probe.close()
                raise RuntimeError('Another BGA title host is already running')
            except (ConnectionRefusedError, FileNotFoundError):
                SOCKET_PATH.unlink(missing_ok=True)
        self.server.bind(str(SOCKET_PATH))
        os.chmod(SOCKET_PATH, 0o600)
        self.server.listen(8)
        self.server.setblocking(False)
        self.notifier = QSocketNotifier(self.server.fileno(), QSocketNotifier.Type.Read)
        self.notifier.activated.connect(self.accept)
        self.timer = QTimer()
        self.timer.timeout.connect(self.drain)
        self.timer.start(50)
        self.refresh_menu()
        send({'type': 'hello', 'version': 1})

    def status(self):
        if self.flash_preview and time.time_ns() // 1_000_000 >= self.flash_until:
            self.clear_flash()
        item = next((t for t in self.tabs if t['id'] == self.selected), None)
        if item:
            raw_title = item['title'] or 'BGA · untitled tab'
            title = ('Play now! • Board Game Arena'
                     if self.selected_lobby_visible is True and is_play_title(raw_title)
                     else raw_title)
        elif self.tabs:
            title = raw_title = 'BGA · choose tab'
        else:
            title = raw_title = 'BGA · no open tab'
        return {'connected': True, 'title': title, 'rawTitle': raw_title,
                'selectedId': self.selected,
                'tabs': self.tabs, 'paused': bool(item and item['paused']),
                'selectedVisible': self.selected_visible,
                'selectedOfferVisible': self.selected_offer_visible,
                'selectedLobbyVisible': self.selected_lobby_visible,
                'flashId': self.flash_id, 'flashActive': self.flash_active,
                'flashUntil': self.flash_until, 'flashTitle': self.flash_title,
                'flashVisibleAtEvent': self.flash_visible_at_event,
                'flashPreview': self.flash_preview,
                'flashKind': self.flash_kind,
                'playOfferSeen': self.play_offer_seen}

    def refresh_menu(self):
        self.menu.clear()
        state = self.status()
        title = state['title']
        self.tray.setToolTip(title[:200])
        heading = self.menu.addAction(title)
        heading.setEnabled(False)
        self.menu.addSeparator()
        for tab in self.tabs:
            label = ('✓ ' if tab['id'] == self.selected else '') + (tab['title'] or 'Untitled BGA tab')
            action = self.menu.addAction(label[:150])
            action.triggered.connect(lambda checked=False, tab_id=tab['id']: self.select(tab_id))
        self.menu.addSeparator()
        focus = self.menu.addAction('Bring Board Game Arena to front')
        focus.setEnabled(self.selected is not None)
        focus.triggered.connect(self.focus)
        self.menu.addAction('Refresh tabs').triggered.connect(lambda: send({'type': 'refresh'}))

    def select(self, tab_id):
        send({'type': 'select', 'id': tab_id})

    def focus(self):
        if self.selected is not None:
            send({'type': 'focus', 'id': self.selected})

    def activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.focus()

    def clear_flash(self):
        self.flash_active = False
        self.flash_tab_id = None
        self.flash_until = 0
        self.flash_title = ''
        self.flash_visible_at_event = None
        self.flash_preview = False
        self.flash_kind = None
        self.flash_state = None
        self.play_offer_seen = False

    def flash_text(self, title, visible_at_event=None, preview=False):
        now = time.time_ns() // 1_000_000
        self.flash_id = max(now, self.flash_id + 1)
        self.flash_active = True
        self.flash_tab_id = self.selected
        self.flash_until = now + 3500 if preview else 0
        self.flash_title = title
        self.flash_visible_at_event = visible_at_event if type(visible_at_event) is bool else None
        self.flash_preview = preview
        self.play_offer_seen = False
        if preview:
            self.flash_kind, self.flash_state = 'preview', None
        elif is_play_title(title):
            self.flash_kind, self.flash_state = 'play', 'play'
            self.play_offer_seen = self.selected_offer_visible is True
        elif your_action(title):
            self.flash_kind, self.flash_state = 'you', your_action(title)
        else:
            self.flash_kind, self.flash_state = 'game', game_title_state(title)

    def flash_state_is_current(self, title):
        if self.flash_kind == 'play':
            return is_play_title(title)
        if self.flash_kind == 'you':
            return your_action(title) == self.flash_state
        if self.flash_kind == 'game':
            return game_title_state(title) == self.flash_state
        return True

    def drain(self):
        for _ in range(100):
            try:
                message = incoming.get_nowait()
            except queue.Empty:
                return
            if message.get('type') == 'quit':
                self.app.quit()
                return
            if message.get('type') != 'snapshot' or message.get('version') != 1:
                continue
            tabs = message.get('tabs')
            if not isinstance(tabs, list):
                continue
            cleaned = []
            for tab in tabs[:100]:
                if isinstance(tab, dict) and type(tab.get('id')) is int and type(tab.get('windowId')) is int:
                    cleaned.append({'id': tab['id'], 'windowId': tab['windowId'],
                                    'title': str(tab.get('title', ''))[:1024],
                                    'paused': bool(tab.get('paused'))})
            previous = next((t for t in self.tabs if t['id'] == self.selected), None)
            previous_selected = self.selected
            previous_offer_visible = self.selected_offer_visible
            self.tabs = cleaned
            self.selected = message.get('selectedId') if any(t['id'] == message.get('selectedId') for t in cleaned) else None
            visible = message.get('selectedVisible')
            self.selected_visible = visible if type(visible) is bool else None
            offer_visible = message.get('selectedOfferVisible')
            self.selected_offer_visible = offer_visible if type(offer_visible) is bool else None
            lobby_visible = message.get('selectedLobbyVisible')
            self.selected_lobby_visible = lobby_visible if type(lobby_visible) is bool else None
            if self.selected != previous_selected:
                previous_offer_visible = None
            current = next((t for t in self.tabs if t['id'] == self.selected), None)
            if self.flash_active and self.flash_kind == 'play' and self.selected_offer_visible is True:
                self.play_offer_seen = True
            if self.flash_active and (self.selected != self.flash_tab_id or
                                      (not self.flash_preview and
                                       (self.selected_visible is True or
                                        not current or not self.flash_state_is_current(current['title']) or
                                        (self.flash_kind == 'play' and self.play_offer_seen and
                                         self.selected_offer_visible is False) or
                                        (self.flash_kind == 'play' and
                                         self.selected_lobby_visible is True)))):
                self.clear_flash()
            self.refresh_menu()
            if previous and current and self.selected == previous['id']:
                if new_your_action(previous['title'], current['title']):
                    if self.selected_visible is not True:
                        self.flash_text(current['title'], self.selected_visible)
                elif game_started_after_search(previous['title'], current['title']):
                    if (self.selected_visible is not True and
                            not (is_play_title(current['title']) and
                                 self.selected_lobby_visible is True)):
                        self.flash_text(current['title'], self.selected_visible)
                elif (not self.flash_active and is_play_title(current['title']) and
                      previous_offer_visible is False and self.selected_offer_visible is True and
                      self.selected_visible is not True):
                    self.flash_text(current['title'], self.selected_visible)
            # A focused turn stays eligible; confirmed focus loss can restart it.
            # Keep an existing background flash ID stable across repeated snapshots.
            if (current and not self.flash_preview and self.selected_visible is False and
                    (not self.flash_active or self.flash_visible_at_event is not False) and
                    (your_action(current['title']) or
                     (is_play_title(current['title']) and
                      self.selected_offer_visible is True and
                      self.selected_lobby_visible is not True))):
                self.flash_text(current['title'], self.selected_visible)

    def accept(self):
        while True:
            try:
                connection, _ = self.server.accept()
            except BlockingIOError:
                return
            with connection:
                connection.settimeout(.2)
                try:
                    request = json.loads(connection.recv(4096))
                    command = request.get('command')
                    if command == 'status':
                        response = self.status()
                    elif command == 'focus':
                        self.focus()
                        response = {'ok': True}
                    elif command == 'select' and type(request.get('id')) is int:
                        self.select(request['id'])
                        response = {'ok': True}
                    elif command == 'refresh':
                        send({'type': 'refresh'})
                        response = {'ok': True}
                    elif command == 'flash' and self.selected is not None:
                        self.flash_text(self.status()['title'], preview=True)
                        response = {'ok': True}
                    else:
                        response = {'error': 'unknown command'}
                    connection.sendall(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                except (ValueError, OSError) as error:
                    print(error, file=sys.stderr)


def main():
    app = QApplication(['bga-title-tray'])
    app.setQuitOnLastWindowClosed(False)
    threading.Thread(target=read_messages, daemon=True).start()
    host = Host(app)
    try:
        return app.exec()
    finally:
        host.tray.hide()
        host.server.close()
        SOCKET_PATH.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())

"""Measure live BGA focus-stop timing while restoring the original window."""
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / 'bin/bga-title-tray'


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def status():
    return json.loads(command(str(STATUS), 'status'))


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = status()
        if predicate(state):
            return state
        time.sleep(.02)
    raise TimeoutError('BGA tray did not reach the expected live state')


def main():
    before = status()
    if not before.get('connected') or before.get('selectedId') is None:
        raise SystemExit('BGA browser connection and selected tab are required')
    if not before.get('flashActive'):
        raise SystemExit('A live BGA alert must be active to measure stop and resume timing')
    result = {'initialTitle': before['title'], 'initialFlashActive': before['flashActive']}
    try:
        command(str(STATUS), 'focus')
        started = time.monotonic()
        wait_for(lambda state: state.get('selectedVisible') is True)
        result['focusConfirmedMs'] = round((time.monotonic() - started) * 1000)
        stop_started = time.monotonic()
        stopped = wait_for(lambda state: not state.get('flashActive'))
        result['flashStopAfterFocusMs'] = round((time.monotonic() - stop_started) * 1000)
        result['flashStopped'] = not stopped['flashActive']
    finally:
        if status().get('selectedVisible') is True:
            # Chrome was raised from the previously active window; Alt+Tab restores it.
            command('ydotool', 'key', '56:1', '15:1', '15:0', '56:0')
    resumed = wait_for(lambda state: state.get('selectedVisible') is False and
                       state.get('flashActive'))
    result['restoredSelectedVisible'] = resumed['selectedVisible']
    result['flashResumed'] = resumed['flashActive']
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

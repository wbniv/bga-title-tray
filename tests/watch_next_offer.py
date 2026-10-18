#!/usr/bin/env python3
"""Record one real BGA Play-offer transition, then exit."""

import argparse
import json
import os
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path


def status(socket_path):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(1)
        connection.connect(str(socket_path))
        connection.sendall(b'{"command":"status"}')
        return json.loads(connection.recv(65536))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--hours', type=float, default=24)
    args = parser.parse_args()
    socket_path = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')) / 'bga-title-tray.sock'
    deadline = time.monotonic() + args.hours * 3600
    previous = None
    saw_play = False
    saw_offer = False
    quiet_since = None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as output:
        while time.monotonic() < deadline:
            try:
                state = status(socket_path)
                row = {key: state.get(key) for key in (
                    'connected', 'rawTitle', 'title', 'selectedOfferVisible',
                    'selectedLobbyVisible', 'selectedVisible', 'flashActive', 'flashKind')}
            except (OSError, ValueError):
                row = {'connected': False}
            if row != previous:
                row['at'] = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                output.write(json.dumps(row, ensure_ascii=False) + '\n')
                output.flush()
                previous = {key: value for key, value in row.items() if key != 'at'}
            play = bool(re.match(r'^\W*Play\s*(?:•|$)', row.get('rawTitle') or '', re.I))
            saw_play |= play
            saw_offer |= row.get('selectedOfferVisible') is True
            ended = saw_play and not row.get('flashActive') and (
                (saw_offer and row.get('selectedOfferVisible') is False) or
                (not play and row.get('connected')))
            if ended:
                break
            if saw_play and not saw_offer and play and row.get('selectedOfferVisible') is False:
                quiet_since = quiet_since or time.monotonic()
                if time.monotonic() - quiet_since >= 30:
                    break
            else:
                quiet_since = None
            time.sleep(0.1)


if __name__ == '__main__':
    main()

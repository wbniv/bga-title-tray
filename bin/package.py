#!/usr/bin/env python3
"""Build a reproducible source-and-runtime archive for end users."""

import gzip
import hashlib
import io
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = (ROOT / "VERSION").read_text().strip()
NAME = f"bga-title-tray-{VERSION}"
FILES = (
    "START_HERE.html", "START_HERE.txt", "LICENSE", "VERSION",
    "screenshots/chrome-developer-mode-off.png", "screenshots/chrome-load-unpacked.png",
    "screenshots/bga-title-tray-working.png",
    "screenshots/chrome-bga-installed.png",
    "bin/install.sh", "bin/uninstall.sh", "bin/setup.py", "bin/package.py",
    "bin/bga-title-tray", "bin/bga-title-tray-status",
    "extension/manifest.json", "extension/background.js", "extension/offer_state.js", "extension/id.txt",
    "native_host/host.py",
    "plasmoid/metadata.json", "plasmoid/contents/ui/main.qml", "plasmoid/contents/ui/configGeneral.qml",
    "plasmoid/contents/config/config.qml", "plasmoid/contents/config/main.xml",
)


def main():
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / f"{NAME}.tar.gz"
    if (ROOT / "extension/manifest.json").read_text().find(f'"version": "{VERSION}"') < 0:
        raise SystemExit("VERSION and extension manifest disagree")
    with archive.open("wb") as output, gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for relative in sorted(FILES):
                source = ROOT / relative
                if not source.is_file() or source.is_symlink():
                    raise SystemExit(f"Missing or unsafe package input: {source}")
                payload = source.read_bytes()
                info = tarfile.TarInfo(f"{NAME}/{relative}")
                info.size = len(payload)
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode = 0o755 if relative.startswith("bin/") or relative == "native_host/host.py" else 0o644
                tar.addfile(info, io.BytesIO(payload))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = destination / f"{archive.name}.sha256"
    checksum.write_text(f"{digest}  {archive.name}\n")
    print(archive)
    print(checksum)


if __name__ == "__main__":
    main()

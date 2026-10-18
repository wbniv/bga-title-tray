#!/usr/bin/env python3
"""Install or remove the BGA title tray in the current user's XDG directories."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HOST_NAME = "com.will.bga_title_tray"
WIDGET_ID = "com.will.bga.title"
OWNER = "bga-title-tray-package-v1"
PAYLOAD = ("bin", "extension", "native_host", "plasmoid", "screenshots")

ADD_WIDGET = r'''
for (const id of panelIds) {
  const panel = panelById(id);
  const widgets = panel.widgets();
  const tray = widgets.find(w => w.type === "org.kde.plasma.systemtray");
  if (!tray) continue;
  let title = widgets.find(w => w.type === "com.will.bga.title");
  if (!title) title = panel.addWidget("com.will.bga.title");
  panel.currentConfigGroup = ["General"];
  const order = String(panel.readConfig("AppletOrder")).split(";").filter(x => x !== String(title.id));
  const at = order.indexOf(String(tray.id));
  order.splice(at < 0 ? order.length : at, 0, String(title.id));
  panel.writeConfig("AppletOrder", order.join(";"));
  panel.reloadConfig();
  break;
}
'''
REMOVE_WIDGET = r'''
for (const id of panelIds) {
  const panel = panelById(id);
  const title = panel.widgets().find(w => w.type === "com.will.bga.title");
  if (!title) continue;
  const titleId = title.id;
  title.remove();
  panel.currentConfigGroup = ["General"];
  const order = String(panel.readConfig("AppletOrder")).split(";").filter(x => x !== String(titleId));
  panel.writeConfig("AppletOrder", order.join(";"));
  panel.reloadConfig();
}
'''


def data_dir():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share").expanduser().resolve() / "bga-title-tray"


def config_dir():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config").expanduser().resolve()


def manifest_path(browser):
    return config_dir() / ("google-chrome" if browser == "chrome" else "chromium") / "NativeMessagingHosts" / f"{HOST_NAME}.json"


def extension_id(source):
    value = (source / "extension/id.txt").read_text().strip()
    if len(value) != 32 or any(char not in "abcdefghijklmnop" for char in value):
        raise RuntimeError("The packaged extension ID is invalid")
    return value


def manifest_data(destination, id_value):
    return {
        "name": HOST_NAME,
        "description": "Board Game Arena title tray host",
        "path": str(destination / "native_host/host.py"),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{id_value}/"],
    }


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Cannot read {path}: {error}") from error


def package_owned(destination):
    marker = destination / ".bga-title-tray-owner.json"
    return marker.is_file() and read_json(marker).get("owner") == OWNER


def check_existing_manifest(path, expected, allow_legacy=False):
    if path.is_symlink():
        raise RuntimeError(f"Refusing to replace a symlinked native host manifest: {path}")
    if not path.exists():
        return
    current = read_json(path)
    same_identity = all(current.get(key) == expected[key] for key in ("name", "type", "allowed_origins"))
    if current == expected:
        return
    if allow_legacy and same_identity and str(current.get("path", "")).endswith("/native_host/host.py"):
        return
    raise RuntimeError(f"Refusing to replace an unrelated native host manifest: {path}")


def require_commands():
    missing = [name for name in ("socat", "kpackagetool6", "qdbus6") if not shutil.which(name)]
    if missing:
        raise RuntimeError("Missing required commands: " + ", ".join(missing))
    probe = subprocess.run([sys.executable, "-c", "from PyQt6 import QtCore, QtDBus"], capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError("Python 3 PyQt6 Core and D-Bus modules are required (install your distro's python3-pyqt6 package)")


def qdbus_script(script):
    probe = subprocess.run(["qdbus6", "org.kde.plasmashell", "/PlasmaShell"], capture_output=True)
    if probe.returncode:
        return False
    subprocess.run(
        ["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script],
        check=True,
    )
    return True


def install(source, destination, browser):
    require_commands()
    id_value = extension_id(source)
    expected = manifest_data(destination, id_value)
    manifest = manifest_path(browser)
    check_existing_manifest(manifest, expected, allow_legacy=True)
    if destination.exists() and not package_owned(destination):
        raise RuntimeError(f"Refusing to overwrite an unowned directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / ".bga-title-tray-owner.json").write_text(json.dumps({"owner": OWNER}) + "\n")
    if source != destination:
        for item in PAYLOAD:
            shutil.copytree(source / item, destination / item, dirs_exist_ok=True)
        for item in ("VERSION", "LICENSE", "START_HERE.html", "START_HERE.txt"):
            shutil.copy2(source / item, destination / item)

    qml_path = destination / "plasmoid/contents/ui/main.qml"
    qml = qml_path.read_text()
    replacements = {
        "@BGA_TOOL@": json.dumps(shlex.quote(str(destination / "bin/bga-title-tray"))),
        "@BGA_STATUS_TOOL@": json.dumps(shlex.quote(str(destination / "bin/bga-title-tray-status"))),
    }
    for marker, value in replacements.items():
        qml = qml.replace(marker, value)
    qml_path.write_text(qml)

    package = str(destination / "plasmoid")
    result = subprocess.run(["kpackagetool6", "--type", "Plasma/Applet", "--install", package], capture_output=True, text=True)
    if result.returncode:
        subprocess.run(["kpackagetool6", "--type", "Plasma/Applet", "--upgrade", package], check=True)

    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(expected, indent=2) + "\n")
    placed = qdbus_script(ADD_WIDGET)
    print(f"Installed BGA title tray for {browser}.")
    print(f"Offline guide: {destination / 'START_HERE.html'}")
    print(f"Load unpacked in {browser} from: {destination / 'extension'}")
    print(f"Check status with: {destination / 'bin/bga-title-tray'} status")
    if not placed:
        print("Plasma was not running; add the Board Game Arena title widget to your panel after login.")


def uninstall(source, destination, browser):
    id_value = extension_id(source)
    expected = manifest_data(destination, id_value)
    manifest = manifest_path(browser)
    if manifest.exists():
        check_existing_manifest(manifest, expected)
        manifest.unlink()
        print(f"Removed {browser} native host registration.")

    other = "chromium" if browser == "chrome" else "chrome"
    other_manifest = manifest_path(other)
    if other_manifest.exists() and read_json(other_manifest) == expected:
        print(f"Kept shared runtime and widget for {other}.")
        return
    if not destination.exists():
        print("No installed runtime remains. Remove the unpacked extension in the browser separately.")
        return
    if not package_owned(destination):
        raise RuntimeError(f"Refusing to remove an unowned directory: {destination}")
    if not shutil.which("kpackagetool6") or not shutil.which("qdbus6"):
        raise RuntimeError("kpackagetool6 and qdbus6 are required to remove the widget")
    qdbus_script(REMOVE_WIDGET)
    subprocess.run(["kpackagetool6", "--type", "Plasma/Applet", "--remove", WIDGET_ID], check=True)
    shutil.rmtree(destination)
    print("Removed the installed runtime and widget. Remove the unpacked extension in the browser separately.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--browser", choices=("chrome", "chromium"), default="chrome")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent
    destination = data_dir()
    if args.action == "install":
        install(source, destination, args.browser)
    else:
        uninstall(source, destination, args.browser)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f"BGA title tray setup: {error}")

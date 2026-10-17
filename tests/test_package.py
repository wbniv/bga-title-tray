"""Exercise a release archive through isolated per-user install and removal."""

import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackageTest(unittest.TestCase):
    def test_archive_install_update_and_uninstall(self):
        with tempfile.TemporaryDirectory(prefix="bga package ") as tmp:
            base = Path(tmp)
            fake_bin = base / "fake-bin"
            fake_bin.mkdir()
            for name in ("socat", "kpackagetool6", "qdbus6"):
                stub = fake_bin / name
                stub.write_text("#!/bin/sh\nexit 0\n")
                stub.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "HOME": str(base / "home"),
                "XDG_DATA_HOME": str(base / "user data"),
                "XDG_CONFIG_HOME": str(base / "user config"),
                "XDG_RUNTIME_DIR": str(base / "runtime"),
                "PATH": str(fake_bin) + os.pathsep + env["PATH"],
            })
            version = (ROOT / "VERSION").read_text().strip()
            archive = ROOT / f"dist/bga-title-tray-{version}.tar.gz"
            subprocess.run(["python3", str(ROOT / "bin/package.py")], check=True, capture_output=True)
            first_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
            subprocess.run(["python3", str(ROOT / "bin/package.py")], check=True, capture_output=True)
            self.assertEqual(first_hash, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertIn(first_hash, (archive.parent / f"{archive.name}.sha256").read_text())
            with tarfile.open(archive, "r:gz") as tar:
                members = tar.getnames()
                self.assertFalse(any("key.txt" in member or "/tests/" in member for member in members))
                self.assertFalse(any(member.startswith("/") or ".." in Path(member).parts for member in members))
                self.assertIn(f"bga-title-tray-{version}/START_HERE.html", members)
                self.assertIn(f"bga-title-tray-{version}/START_HERE.txt", members)
                self.assertIn(f"bga-title-tray-{version}/screenshots/chrome-developer-mode-off.png", members)
                self.assertIn(f"bga-title-tray-{version}/screenshots/chrome-load-unpacked.png", members)
                self.assertIn(f"bga-title-tray-{version}/screenshots/bga-title-tray-working.png", members)
                self.assertIn(f"bga-title-tray-{version}/screenshots/chrome-bga-installed.png", members)
                self.assertFalse(any(member.endswith(".md") for member in members))
                tar.extractall(base / "extracted with spaces", filter="data")
            source = base / f"extracted with spaces/bga-title-tray-{version}"
            guide = (source / "START_HERE.html").read_text()
            self.assertIn("./bin/install.sh --browser chrome", guide)
            self.assertIn("./bin/install.sh --browser chromium", guide)
            self.assertIn("chrome://extensions", guide)
            self.assertIn("Troubleshooting", guide)
            self.assertIn('id="reload-control"', guide)
            self.assertIn('class="mark mark-reload"', guide)
            self.assertIn('id="remove-control"', guide)
            self.assertIn('class="mark mark-remove"', guide)
            self.assertIn('href="https://boardgamearena.com/"', guide)
            self.assertNotIn('src="https://', guide)
            self.assertNotIn('src="http://', guide)
            for image in ("chrome-developer-mode-off.png", "chrome-load-unpacked.png", "chrome-bga-installed.png", "bga-title-tray-working.png"):
                self.assertIn(f'src="screenshots/{image}"', guide)
                self.assertTrue((source / "screenshots" / image).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            fallback = (source / "START_HERE.txt").read_text()
            for command in ("./bin/install.sh --browser chrome", "./bin/install.sh --browser chromium", "chrome://extensions"):
                self.assertIn(command, fallback)
            install = source / "bin/install.sh"
            installed = base / "user data/bga-title-tray"
            for browser in ("chrome", "chromium"):
                subprocess.run([str(install), "--browser", browser], env=env, check=True, capture_output=True)
                manifest_dir = "google-chrome" if browser == "chrome" else "chromium"
                manifest = base / f"user config/{manifest_dir}/NativeMessagingHosts/com.will.bga_title_tray.json"
                value = json.loads(manifest.read_text())
                self.assertEqual(value["path"], str(installed / "native_host/host.py"))
                self.assertEqual(value["allowed_origins"], ["chrome-extension://kfhpjlekkgkdagnnaimcjdmleboclopd/"])
                self.assertNotIn("/home/will", manifest.read_text())
            subprocess.run([str(install), "--browser", "chrome"], env=env, check=True, capture_output=True)
            qml = (installed / "plasmoid/contents/ui/main.qml").read_text()
            self.assertIn("user data/bga-title-tray", qml)
            self.assertNotIn("@BGA_", qml)
            self.assertNotIn(str(source), qml)
            self.assertNotIn("/home/will", qml)
            self.assertTrue((installed / "START_HERE.html").is_file())
            self.assertTrue((installed / "START_HERE.txt").is_file())
            self.assertTrue((installed / "screenshots/chrome-load-unpacked.png").is_file())
            status = subprocess.run([str(installed / "bin/bga-title-tray"), "status"], env=env, check=True, capture_output=True, text=True)
            self.assertFalse(json.loads(status.stdout)["connected"])
            subprocess.run([str(installed / "bin/uninstall.sh"), "--browser", "chrome"], env=env, check=True, capture_output=True)
            self.assertTrue(installed.exists())
            subprocess.run([str(installed / "bin/uninstall.sh"), "--browser", "chromium"], env=env, check=True, capture_output=True)
            self.assertFalse(installed.exists())

            installed.mkdir()
            refused = subprocess.run([str(install), "--browser", "chrome"], env=env, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("unowned directory", refused.stderr)
            installed.rmdir()

            manifest = base / "user config/google-chrome/NativeMessagingHosts/com.will.bga_title_tray.json"
            manifest.write_text('{"name":"another.extension"}\n')
            refused = subprocess.run([str(install), "--browser", "chrome"], env=env, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("unrelated native host manifest", refused.stderr)


if __name__ == "__main__":
    unittest.main()

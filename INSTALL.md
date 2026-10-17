# Installation and use

End-user packages include an illustrated [browser guide](START_HERE.html) and a [plain-text guide](START_HERE.txt).

## Supported setup

This package targets Linux with KDE Plasma 6 and Google Chrome or Chromium. The native host uses Python 3 and PyQt6. The Plasma widget needs `socat`, `kpackagetool6`, and `qdbus6`. The installer checks these dependencies before changing user files. Install missing packages with your distribution's package manager. The browser must support Manifest V3 extensions and native messaging.

The installer writes only to the current user's XDG data and configuration directories and the user's Plasma widget registry. It does not install system packages or need root. If `XDG_DATA_HOME` is unset, the application lives at `~/.local/share/bga-title-tray`; if `XDG_CONFIG_HOME` is unset, the native-host manifest goes under `~/.config/google-chrome/NativeMessagingHosts` or `~/.config/chromium/NativeMessagingHosts`. The manifest contains an absolute path to the installed host and admits only the packaged extension ID.

## Install

1. Check the checksum and extract the archive as shown in [QUICKSTART.md](QUICKSTART.md). Extraction from a directory with spaces is supported.
2. From the extracted package, run `./bin/install.sh --browser chrome` or `./bin/install.sh --browser chromium`. The command prints the permanent path to the extension.
3. In that browser, open [Chrome extensions](chrome://extensions/) (or paste `chrome://extensions/` into the address bar if the link is blocked), enable **Developer mode**, choose **Load unpacked**, and select the printed extension directory. Use the installed copy, not the extracted copy.
4. Open or refresh [Board Game Arena](https://boardgamearena.com/). The panel widget and tray icon should show its title. The panel text is clickable and focuses the existing BGA tab. The tray menu can also focus it.

If the title does not appear, run the `bga-title-tray status` command printed by the installer. `"connected": true` means the extension has reached the native host. The `selectedLobbyVisible` and `selectedOfferVisible` fields reflect the visible lobby and game-offer text. `rawTitle` preserves Chrome's title when the panel displays a more accurate “Play now!” lobby label.

The first install adds the widget beside the system tray if a Plasma panel and tray are available. If Plasma was not running, add **Board Game Arena title** through panel edit mode after login. A Plasma restart can be needed before a new widget appears in the panel menu.

## Options and behavior

The widget's **General** settings offer **Only flash when the selected BGA tab is not active**, enabled by default. Alerts flash the panel text with a white background until the triggering page state ends or Chrome confirms that BGA is focused. Clicking the text focuses the selected BGA tab. The tray icon remains steady; this application does not create desktop notifications. `bga-title-tray flash` gives a short local preview.

The extension reads BGA tab titles and whether the visible page contains the game-offer or “Play now!” lobby markers. Titles and state flags stay in memory; the application does not log game content or passwords by default. The extension's permissions are limited to native messaging, scripting, and Board Game Arena pages.

## Update and remove

To update, extract the new archive and run its `./bin/install.sh` with the browser option used originally. It replaces its installed files and upgrades the widget without adding another panel copy. On [Chrome extensions](chrome://extensions/), click the circular-arrow **Reload** control on the existing unpacked extension. The [illustrated guide](START_HERE.html#reload-control) marks it. If the extensions link is blocked, paste `chrome://extensions/` into the address bar. Keep using the installed extension directory; its ID is fixed across package versions.

To remove, run `~/.local/share/bga-title-tray/bin/uninstall.sh --browser chrome` (or `chromium`), adjusting for `XDG_DATA_HOME`. Remove the unpacked extension in the browser separately. If both browsers were registered, uninstall one at a time; the shared runtime and widget remain until the final browser registration is removed. The uninstaller checks ownership before removing its files and refuses to remove another application's manifest or data directory.

## Troubleshooting

- **Missing dependency:** install the named program or Python 3 PyQt6 package with your distribution's package manager, then re-run the installer.
- **Disconnected:** verify that the unpacked extension is enabled on [Chrome extensions](chrome://extensions/), its path is the installed `extension` directory, and the selected browser matches the installer option. Reload it, refresh [Board Game Arena](https://boardgamearena.com/), and run `bga-title-tray status` again.
- **No panel text:** verify Plasma 6 is running, look for **Board Game Arena title** in panel edit mode, and restart Plasma if a newly installed widget is not listed.
- **No alert:** the default setting suppresses alerts while the selected BGA tab is active in the focused browser window. For a harmless visual check, run `bga-title-tray flash`.
- **Native host has exited error:** check the extension's **Errors** view after clearing old entries and reloading. An actual new error may indicate a missing PyQt6 runtime or a stale native-host manifest. Re-run the installer and inspect its printed paths.

Chrome's [native messaging documentation](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging) explains the browser manifest and `allowed_origins`; KDE's [widget setup documentation](https://develop.kde.org/docs/plasma/widget/setup/) explains user widget installation.

Documentation prepared with Codex CLI 0.163.0, model `gpt-6-sol`, reasoning effort `high`, verified from session metadata.

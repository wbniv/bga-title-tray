# Board Game Arena title in the KDE tray area

Shows the title of an existing [Board Game Arena](https://boardgamearena.com/) tab beside the Plasma system tray. When BGA returns to its “Play now!” lobby but Chrome still reports a Play title, the label shows **Play now! • Board Game Arena** to reflect the visible page state. A BGA tray icon provides the displayed state and tab selection. The browser extension reads tab titles and the presence of the Play-offer and lobby text; the native host runs the tray icon and a local control socket; the widget displays the selected state.

![Board Game Arena title displayed beside the KDE system tray](screenshots/bga-title-tray-working.png)

The first release supports Linux with KDE Plasma 6 and Google Chrome or Chromium. Download the archive and checksum from the [latest GitHub release](https://github.com/wbniv/bga-title-tray/releases/latest). In the download folder, run:

```sh
sha256sum -c bga-title-tray-0.4.3.tar.gz.sha256
tar -xzf bga-title-tray-0.4.3.tar.gz
cd bga-title-tray-0.4.3
xdg-open START_HERE.html
```

The HTML guide has screenshots for installation, the Reload control, and the working panel. It opens locally in a browser and does not need a Markdown viewer. Follow its browser choice and **Load unpacked** steps to finish installation.

The widget checks the local host every 100 ms only while its text is flashing, so it stops on the next status read after Chrome confirms BGA focus or the triggering state ends. An explicit flash timer drives those reads; the Plasma data source's interval remains one second for normal title refresh. A lightweight `socat` status reader keeps active-alert polling inexpensive; `socat` must be installed before running `./bin/install.sh`. A click alone does not acknowledge focus: Chrome must report the selected tab as active in its focused window.

When the selected tab changes from “Searching for … player(s)” to BGA's game-start title (observed as “◣ Play • Board Game Arena”) or directly to a game-specific title, the title area alternates between its normal appearance and a white background with black text. A new selected-tab title beginning with “You…” does the same. The text always has 10 logical pixels of padding on both sides, including when no alert is active, so it does not shift during a flash. The white background and click target still fill the title area. A real alert has no timed cutoff: the Play alert stops when the selected tab no longer says Play, when its previously visible “You are going to play” offer text disappears, or when the “Play now!” lobby is visible. A later offer can alert again without a title change. A “You…” alert stops when that instruction goes away, and a direct game-title alert stops when that title changes. Any real alert also stops when the selected BGA tab is active in a focused Chrome window. The label follows Chrome's title except when the “Play now!” lobby is visible under a Play title; then it shows **Play now! • Board Game Arena**. The host's `rawTitle` status field preserves Chrome's reported title. The extension's page observer reports only whether the Play-offer and lobby text are visible; its `scripting` permission lets the updated extension attach that observer to an already-open BGA tab without reloading the page. **Only flash when the selected BGA tab is not active** is enabled by default in the widget's General settings: a title change is quiet when that tab is already focused. Uncheck it to allow a qualifying change to start an alert if focus is unknown; confirmed focus still ends it. If Chrome cannot report whether that tab is active, the default setting suppresses a new alert; an existing alert continues only while its triggering state remains current. Initial snapshots, a different selected tab, repeated updates to the same title, and changes only to the leading status symbol do not start a flash. No desktop notification appears and the tray icon stays steady. `./bin/bga-title-tray flash` gives a 3.5-second manual preview even when the tab is active; that preview duration does not apply to real alerts.

Click anywhere in the title area or choose **Bring Board Game Arena to front** from the tray menu to activate the selected existing tab and focus Chrome. Chrome checks that the tab still belongs to BGA before focusing it.

## Install

For a fresh installation, open the [illustrated guide](START_HERE.html) in any browser. It includes screenshots of Chrome’s setup controls, the installed extension card, and the working tray text. The [plain-text guide](START_HERE.txt) is a fallback. The release archive includes these guides; Markdown files are for source contributors. The package installs a permanent runtime and extension copy under the user's XDG data directory, registers the native host for Google Chrome or Chromium, and adds **Board Game Arena title** beside the Plasma system tray. Load the installed `extension` directory through the browser's **Load unpacked** control. The installer prints its exact path. Existing source-tree installations can run the new installer to move to the permanent copy, then reload the unpacked extension from that copy.

The extension ID is fixed in `extension/id.txt`. The native messaging manifest accepts only that ID. The page observer checks for the visible phrases “You are going to play” and “Play now!”; it does not collect game data or passwords. Titles and state flags stay in memory and are not logged by default.

Chrome may disconnect the native-messaging port when the host or unpacked extension is reloaded. Extension version 0.2.2 reads `chrome.runtime.lastError` in that disconnect callback and retries, so an expected host exit does not leave a new “Unchecked runtime.lastError: Native host has exited” entry. Chrome can retain entries recorded by older extension versions in its **Errors** view; the live connection is shown by the panel title and `./bin/bga-title-tray status`.

Use the installed `bin/bga-title-tray status` to inspect connection and selected tab. Its `refresh` command asks Chrome to rediscover tabs. To uninstall, click **Remove** on the extension card at [Chrome extensions](chrome://extensions/) as shown in the [guide](START_HERE.html#remove-control). Then run the installed `bin/uninstall.sh --browser chrome` or `--browser chromium` to remove this package's native-host registration and, after the last registered browser, its runtime and widget.

Code prepared with Codex CLI 0.163.0, model gpt-6-sol, reasoning effort high (verified from session metadata).

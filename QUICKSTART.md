# Quick start

Board Game Arena title tray shows the title or visible lobby state of an existing Board Game Arena tab beside the KDE Plasma system tray. The text flashes for a game offer or your turn while that tab is in the background, pauses when you focus BGA, and resumes if focus leaves before the state ends. Clicking the text focuses that tab.

Requirements: Linux with KDE Plasma 6, Google Chrome or Chromium, Python 3 with PyQt6, `socat`, `kpackagetool6`, and `qdbus6`. Install missing packages with your distribution's package manager; names vary by distribution. No root access is needed for this application's installer.

1. Open the illustrated [installation guide](START_HERE.html) in a browser. A [text-only guide](START_HERE.txt) is also included.
2. Verify the downloaded archive against its adjacent `.sha256` file using `sha256sum -c bga-title-tray-0.4.7.tar.gz.sha256`, then extract it with `tar -xzf bga-title-tray-0.4.7.tar.gz`.
3. Enter `bga-title-tray-0.4.7` and run `./bin/install.sh --browser chrome`. Use `--browser chromium` for Chromium. The installer prints the exact folder to select in the browser.
4. Open [Chrome extensions](chrome://extensions/) in the selected browser. If that link is blocked, paste `chrome://extensions/` into the address bar. Enable **Developer mode**, select **Load unpacked**, and choose the printed `extension` directory. Keep the installed directory; the downloaded archive and extraction directory can now be removed.
5. Open or refresh [Board Game Arena](https://boardgamearena.com/). Its title should appear beside the Plasma system tray when Plasma is running. Click the panel text to focus the tab. If no title appears, see the [troubleshooting section](START_HERE.html#troubleshooting).

To update, extract a newer archive and run its installer with the same `--browser` option, then click the circular-arrow **Reload** control on the existing extension at [Chrome extensions](chrome://extensions/). The [illustrated guide](START_HERE.html#reload-control) marks that control. If the browser blocks the extensions link, paste `chrome://extensions/` into its address bar. To remove, click **Remove** on the extension's card as shown in the [guide](START_HERE.html#remove-control), then run the installed `bin/uninstall.sh --browser chrome` (or `chromium`) to remove the native host and panel widget.

For browser registration, panel behavior, troubleshooting, and options, see [INSTALL.md](INSTALL.md). The application is licensed under [MIT](LICENSE).

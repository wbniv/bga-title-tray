// Report the player's own turn clock. BGA runs most games in an iframe, so this
// script runs in every frame and only the frame that holds the clock reports.
(() => {
  if (globalThis.__bgaTitleTrayClockV1) return;
  globalThis.__bgaTitleTrayClockV1 = true;

  const OWN_CLOCK = '.player-board.current-player-board .timeToThink';
  let lastSeconds = null;
  let pending = null;

  // "3:27", "-0:05" (overtime) and "1:02:03" become signed seconds.
  function parseClock(text) {
    const match = /^\s*(-?)(?:(\d+):)?(\d+):(\d{2})\s*$/.exec(text || '');
    if (!match) return null;
    const [, sign, hours, minutes, seconds] = match;
    const total = Number(hours || 0) * 3600 + Number(minutes) * 60 + Number(seconds);
    return sign ? -total : total;
  }

  function report() {
    pending = null;
    const seconds = parseClock(document.querySelector(OWN_CLOCK)?.textContent);
    if (seconds === lastSeconds) return;
    lastSeconds = seconds;
    try {
      chrome.runtime.sendMessage({type: 'bgaTurnClock', seconds}, () => {
        // A reload can invalidate this document's extension context.
        void chrome.runtime.lastError;
      });
    } catch { /* The replacement content script will report after reload. */ }
  }

  function schedule() {
    if (pending === null) pending = setTimeout(report, 80);
  }

  new MutationObserver(schedule).observe(document.documentElement, {
    subtree: true, childList: true, characterData: true
  });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule, {once: true});
  }
  schedule();
})();

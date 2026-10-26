// Report whether the selected BGA page shows a Play offer or its Play-now lobby.
(() => {
  if (globalThis.__bgaTitleTrayPageObserverV2) return;
  globalThis.__bgaTitleTrayPageObserverV2 = true;

  let lastState = null;
  let pending = null;

  function pageState() {
    if (!/^\W*Play\s*(?:•|$)/i.test(document.title)) {
      return {offerVisible: false, lobbyVisible: false};
    }
    const text = document.body?.innerText || '';
    const waitingForAnotherPlayer = /\bWaiting for:\s*\S+/i.test(text);
    const offerVisible = !waitingForAnotherPlayer && /\bYou are going to play\b/i.test(text);
    const lobbyVisible = !offerVisible && /\bPlay now!/i.test(text);
    return {offerVisible, lobbyVisible};
  }

  function report() {
    pending = null;
    const state = pageState();
    if (lastState && state.offerVisible === lastState.offerVisible &&
        state.lobbyVisible === lastState.lobbyVisible) return;
    lastState = state;
    try {
      chrome.runtime.sendMessage({type: 'bgaPageVisibility', ...state}, () => {
        // A reload can invalidate this document's extension context.
        void chrome.runtime.lastError;
      });
    } catch { /* The replacement content script will report after reload. */ }
  }

  function schedule() {
    if (pending === null) pending = setTimeout(report, 80);
  }

  const observer = new MutationObserver(schedule);
  observer.observe(document.documentElement, {
    subtree: true, childList: true, characterData: true, attributes: true,
    attributeFilter: ['style', 'class', 'hidden', 'aria-hidden']
  });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule, {once: true});
  }
  schedule();
})();

// BGA titles are read only from matching Chrome tabs and sent to the local bridge.
const HOST = 'com.will.bga_title_tray';
let port = null;
let retry = 1000;
let selectedId = null;
let snapshotGeneration = 0;
const pageVisibility = new Map();

function isBga(url) {
  try {
    const u = new URL(url);
    return u.protocol === 'https:' &&
      (u.hostname === 'boardgamearena.com' || u.hostname.endsWith('.boardgamearena.com'));
  } catch { return false; }
}

function clean(tab) {
  return {
    id: tab.id,
    windowId: tab.windowId,
    title: (tab.title || '').slice(0, 1024),
    paused: Boolean(tab.discarded || tab.frozen)
  };
}

async function snapshot() {
  const generation = ++snapshotGeneration;
  const all = await chrome.tabs.query({});
  const matches = all.filter(t => Number.isInteger(t.id) && isBga(t.url)).map(clean);
  let nextSelectedId = selectedId;
  if (!matches.some(t => t.id === nextSelectedId)) {
    nextSelectedId = matches.length === 1 ? matches[0].id : null;
  }
  const selectedTab = all.find(t => t.id === nextSelectedId);
  let selectedVisible = null;
  if (selectedTab && Number.isInteger(selectedTab.windowId)) {
    const window = await chrome.windows.get(selectedTab.windowId).catch(() => null);
    if (window && typeof window.focused === 'boolean' &&
        typeof selectedTab.active === 'boolean') {
      selectedVisible = window.focused && selectedTab.active;
    }
  }
  if (generation !== snapshotGeneration) return;
  selectedId = nextSelectedId;
  const selectedPage = pageVisibility.get(selectedId);
  const selectedOfferVisible = selectedPage?.offerVisible ?? null;
  const selectedLobbyVisible = selectedPage?.lobbyVisible ?? null;
  if (port) port.postMessage({type: 'snapshot', version: 1, tabs: matches,
                             selectedId, selectedVisible, selectedOfferVisible,
                             selectedLobbyVisible});
}

async function injectExistingBgaTabs() {
  const all = await chrome.tabs.query({});
  await Promise.allSettled(all.filter(t => Number.isInteger(t.id) && isBga(t.url))
    .map(t => chrome.scripting.executeScript({target: {tabId: t.id}, files: ['offer_state.js']})));
}

async function choose(id) {
  if (!Number.isInteger(id)) return;
  const tab = await chrome.tabs.get(id).catch(() => null);
  if (!tab || !isBga(tab.url)) { await snapshot(); return; }
  selectedId = id;
  await snapshot();
}

async function focus(id) {
  if (!Number.isInteger(id) || id !== selectedId) return;
  const tab = await chrome.tabs.get(id).catch(() => null);
  if (!tab || !isBga(tab.url)) { await snapshot(); return; }
  await chrome.tabs.update(id, {active: true});
  await chrome.windows.update(tab.windowId, {focused: true});
  await snapshot();
}

function connect() {
  if (port) return;
  try { port = chrome.runtime.connectNative(HOST); }
  catch { setTimeout(connect, retry); retry = Math.min(retry * 2, 30000); return; }
  port.onMessage.addListener(async message => {
    try {
      if (message.type === 'hello') {
        retry = 1000;
        await injectExistingBgaTabs();
        await snapshot();
      }
      if (message.type === 'select') await choose(message.id);
      if (message.type === 'focus') await focus(message.id);
      if (message.type === 'refresh') await snapshot();
    } catch (error) { console.error('BGA tray command failed:', error); await snapshot(); }
  });
  port.onDisconnect.addListener(() => {
    // Reading lastError acknowledges a native-host exit; reconnect below.
    const disconnectError = chrome.runtime.lastError;
    if (disconnectError) console.info('BGA tray native host disconnected; reconnecting:',
                                      disconnectError.message);
    port = null;
    setTimeout(connect, retry);
    retry = Math.min(retry * 2, 30000);
  });
}

chrome.tabs.onUpdated.addListener((id, change) => {
  if ('url' in change || change.status === 'loading') pageVisibility.delete(id);
  if ('title' in change || 'url' in change || 'status' in change) snapshot().catch(console.error);
});
chrome.tabs.onRemoved.addListener(id => {
  pageVisibility.delete(id);
  snapshot().catch(console.error);
});
chrome.tabs.onReplaced.addListener((_newId, oldId) => {
  pageVisibility.delete(oldId);
  snapshot().catch(console.error);
});
chrome.tabs.onActivated.addListener(() => snapshot().catch(console.error));
chrome.windows.onRemoved.addListener(() => snapshot().catch(console.error));
chrome.windows.onFocusChanged.addListener(() => snapshot().catch(console.error));
chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.type !== 'bgaPageVisibility' ||
      typeof message.offerVisible !== 'boolean' ||
      typeof message.lobbyVisible !== 'boolean' ||
      sender.frameId !== 0 ||
      !Number.isInteger(sender.tab?.id) || !isBga(sender.tab.url)) return;
  const previous = pageVisibility.get(sender.tab.id);
  if (previous?.offerVisible === message.offerVisible &&
      previous?.lobbyVisible === message.lobbyVisible) return;
  pageVisibility.set(sender.tab.id, {
    offerVisible: message.offerVisible, lobbyVisible: message.lobbyVisible
  });
  snapshot().catch(console.error);
});
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();

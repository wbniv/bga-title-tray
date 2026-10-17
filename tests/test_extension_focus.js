const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'extension', 'background.js'), 'utf8');
const messages = [];
let tabs = [{id: 42, windowId: 7, title: '◣ Play • Board Game Arena',
             url: 'https://boardgamearena.com/lobby', active: true}];
let focused = true;
let focusQueryFails = false;
let lastErrorReads = 0;
const injections = [];
const tabUpdates = [];
const windowUpdates = [];
const listeners = {};
const event = name => ({addListener(listener) { listeners[name] = listener; }});
const context = vm.createContext({
  URL,
  setTimeout,
  console,
  chrome: {
    scripting: {executeScript: async options => { injections.push(options); }},
    tabs: {
      query: async () => tabs,
      get: async id => tabs.find(tab => tab.id === id),
      update: async (id, properties) => {
        tabUpdates.push({id, properties});
        if (properties.active) {
          for (const tab of tabs) {
            if (tab.windowId === tabs.find(candidate => candidate.id === id)?.windowId) {
              tab.active = tab.id === id;
            }
          }
        }
      },
      onUpdated: event('tabUpdated'), onRemoved: event(), onReplaced: event(), onActivated: event()
    },
    windows: {
      get: async () => {
        if (focusQueryFails) throw new Error('focus unavailable');
        return {focused};
      },
      update: async (id, properties) => {
        windowUpdates.push({id, properties});
        if (typeof properties.focused === 'boolean') focused = properties.focused;
      },
      onRemoved: event(), onFocusChanged: event()
    },
    runtime: {
      connectNative: () => ({postMessage: message => messages.push(message),
                            onMessage: event('nativeMessage'), onDisconnect: event('nativeDisconnect')}),
      get lastError() { lastErrorReads++; return {message: 'Native host has exited.'}; },
      onStartup: event(), onInstalled: event(), onMessage: event('offerMessage')
    }
  }
});
vm.runInContext(source, context);

async function check(expected) {
  await vm.runInContext('snapshot()', context);
  assert.equal(messages.at(-1).selectedVisible, expected);
}

(async () => {
  await check(true);
  tabs[0].title = 'x'.repeat(1100);
  await check(true);
  assert.equal(messages.at(-1).tabs[0].title.length, 1024);
  tabs[0].title = '◣ Play • Board Game Arena';
  focused = false;
  await check(false);
  tabs[0].title = 'Searching for players... • Board Game Arena';
  listeners.tabUpdated(42, {title: tabs[0].title});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(messages.at(-1).tabs[0].title, tabs[0].title);
  focused = true;
  tabs[0].active = false;
  await check(false);
  listeners.offerMessage({type: 'bgaPageVisibility', offerVisible: true, lobbyVisible: false},
                         {frameId: 0, tab: tabs[0]});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(messages.at(-1).selectedOfferVisible, true);
  assert.equal(messages.at(-1).selectedLobbyVisible, false);
  listeners.offerMessage({type: 'bgaPageVisibility', offerVisible: false, lobbyVisible: true},
                         {frameId: 0, tab: tabs[0]});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(messages.at(-1).selectedOfferVisible, false);
  assert.equal(messages.at(-1).selectedLobbyVisible, true);
  listeners.nativeMessage({type: 'hello'});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(injections.length, 1);
  tabs = [
    {...tabs[0], id: 42, windowId: 7, active: true},
    {id: 43, windowId: 8, title: 'Searching • Board Game Arena',
     url: 'https://boardgamearena.com/search', active: false},
    {id: 44, windowId: 8, title: 'Unrelated', url: 'https://example.com/', active: false}
  ];
  await vm.runInContext('snapshot()', context);
  assert.equal(messages.at(-1).selectedId, 42);
  listeners.nativeMessage({type: 'select', id: 43});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(messages.at(-1).selectedId, 43);
  listeners.nativeMessage({type: 'focus', id: 43});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(tabUpdates.at(-1).id, 43);
  assert.equal(tabUpdates.at(-1).properties.active, true);
  assert.equal(windowUpdates.at(-1).id, 8);
  assert.equal(windowUpdates.at(-1).properties.focused, true);
  assert.equal(messages.at(-1).selectedVisible, true);
  const updatesBeforeStaleFocus = tabUpdates.length;
  listeners.nativeMessage({type: 'focus', id: 42});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(tabUpdates.length, updatesBeforeStaleFocus);
  tabs = [];
  await vm.runInContext('snapshot()', context);
  assert.equal(messages.at(-1).tabs.length, 0);
  assert.equal(messages.at(-1).selectedId, null);
  tabs = [{id: 42, windowId: 7, title: 'Play • Board Game Arena',
           url: 'https://boardgamearena.com/lobby', active: true}];
  tabs[0].active = true;
  focusQueryFails = true;
  await check(null);
  focusQueryFails = false;
  tabs = [{...tabs[0], url: 'https://boardgamearena.com.evil.example/lobby'}];
  await check(null);
  assert.equal(messages.at(-1).tabs.length, 0);
  listeners.nativeDisconnect();
  assert.equal(lastErrorReads, 1);
  console.log('Chrome focus snapshots: passed');
})().catch(error => { console.error(error); process.exitCode = 1; });

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
      update: async () => {},
      onUpdated: event('tabUpdated'), onRemoved: event(), onReplaced: event(), onActivated: event()
    },
    windows: {
      get: async () => {
        if (focusQueryFails) throw new Error('focus unavailable');
        return {focused};
      },
      update: async () => {}, onRemoved: event(), onFocusChanged: event()
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

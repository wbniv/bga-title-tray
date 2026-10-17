const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'extension', 'offer_state.js'), 'utf8');
const messages = [];
const timers = [];
let bodyText = 'You are going to play Hearts\nAccept\nDecline';
let changed;
const document = {
  title: 'Play • Board Game Arena',
  body: {get innerText() { return bodyText; }},
  documentElement: {},
  readyState: 'complete'
};
const context = vm.createContext({
  document,
  setTimeout: callback => { timers.push(callback); return timers.length; },
  MutationObserver: class {
    constructor(callback) { changed = callback; }
    observe() {}
  },
  chrome: {runtime: {
    sendMessage(message, callback) { messages.push(message); callback(); },
    get lastError() { return undefined; }
  }}
});
function flush() {
  while (timers.length) timers.shift()();
}

vm.runInContext(source, context);
flush();
assert.equal(messages.at(-1).offerVisible, true);
assert.equal(messages.at(-1).lobbyVisible, false);
bodyText = 'Simple game\nPlay now!\nFavorite games';
changed();
flush();
assert.equal(messages.at(-1).offerVisible, false);
assert.equal(messages.at(-1).lobbyVisible, true);
assert.equal(messages.length, 2);
changed();
flush();
assert.equal(messages.length, 2);
bodyText = 'You are going to play Hearts\nAccept';
changed();
flush();
assert.equal(messages.at(-1).offerVisible, true);
assert.equal(messages.at(-1).lobbyVisible, false);
vm.runInContext(source, context);
changed();
flush();
assert.equal(messages.length, 3);
document.title = 'Searching for 2 player(s)... • Board Game Arena';
changed();
flush();
assert.equal(messages.at(-1).offerVisible, false);
assert.equal(messages.at(-1).lobbyVisible, false);
console.log('BGA offer observer: passed');

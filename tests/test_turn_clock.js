const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'extension', 'turn_clock.js'), 'utf8');
const messages = [];
const timers = [];
let clockText = null;
let changed;
const document = {
  querySelector(selector) {
    assert.equal(selector, '.player-board.current-player-board .timeToThink');
    return clockText === null ? null : {textContent: clockText};
  },
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
function tick(text) {
  clockText = text;
  changed();
  flush();
}

// A frame without the clock (the top document) never reports.
vm.runInContext(source, context);
flush();
assert.equal(messages.length, 0);

tick(' 3:27 ');
assert.equal(messages.at(-1).type, 'bgaTurnClock');
assert.equal(messages.at(-1).seconds, 207);
tick('3:27');
assert.equal(messages.length, 1, 'an unchanged reading is not resent');
tick('0:09');
assert.equal(messages.at(-1).seconds, 9);
tick('-0:05');
assert.equal(messages.at(-1).seconds, -5, 'overtime is negative');
tick('1:02:03');
assert.equal(messages.at(-1).seconds, 3723);
tick('soon');
assert.equal(messages.at(-1).seconds, null, 'an unreadable clock clears the report');
tick(null);
assert.equal(messages.length, 5, 'null is not resent');

// A second injection into the same frame is ignored.
const count = messages.length;
vm.runInContext(source, context);
tick('0:30');
assert.equal(messages.length, count + 1);
console.log('BGA turn clock: passed');

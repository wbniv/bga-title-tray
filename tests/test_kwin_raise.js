// The generated KWin script must raise the Chrome window showing the selected BGA tab.
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const vm = require('node:vm');

function script(title) {
  return execFileSync('python3', ['-c',
    'import json, sys; sys.path.insert(0, "."); from native_host import host; print(host.raise_script(json.loads(sys.argv[1])))',
    JSON.stringify(title)], {cwd: path.join(__dirname, '..'), encoding: 'utf8'});
}

function run(title, windows) {
  const printed = [];
  const workspace = {windowList: () => windows, activeWindow: null};
  vm.runInNewContext(script(title), {workspace, print: text => printed.push(text)});
  return {active: workspace.activeWindow, printed};
}

const win = (caption, extra = {}) => ({caption, resourceClass: 'google-chrome', normalWindow: true,
                                       minimized: false, demandsAttention: false, ...extra});

// The tab title and the window caption differ only by BGA's status glyph and Chrome's suffix.
let bga = win('◣ Play • Board Game Arena - Google Chrome', {minimized: true});
let result = run('◢ Play • Board Game Arena', [win('README - Google Chrome'), bga]);
assert.equal(result.active, bga);
assert.equal(bga.minimized, false);
assert.match(result.printed[0], /raised/);

// A window of another application with the same caption is never raised.
const konsole = {...win('Play • Board Game Arena - Google Chrome'), resourceClass: 'org.kde.konsole'};
result = run('Play • Board Game Arena', [konsole]);
assert.equal(result.active, null);
assert.match(result.printed[0], /no Chrome window/);

// After Chrome's refused request, the BGA window that demands attention is raised even if
// its caption has moved on from the title the host knew.
bga = win('You must play a card • Hearts • Board Game Arena - Google Chrome', {demandsAttention: true});
result = run('Searching for players • Board Game Arena', [win('README - Google Chrome'), bga]);
assert.equal(result.active, bga);

// Quotes and backslashes in a title stay inside the string literal.
result = run('A "quoted" \\ title', [win('A "quoted" \\ title - Google Chrome')]);
assert.match(result.printed[0], /raised A "quoted"/);

console.log('KWin raise script tests passed');

/* 一次性分析脚本（_ 开头，已被 .gitignore 忽略）
   目的：确定 HELP_GAP 取多少，「帮我一把」才既有用、又不至于一点就通关。
   做法：把 game.js 源码里 HELP_GAP 那一行替换成待测值，建沙箱跑真代码，
         乱投到堆上警戒线（=卡住），然后反复点按钮，统计清理量和通关点击数。 */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = __dirname;
const gameSrc = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
const partsSrc = fs.readFileSync(path.join(root, 'assets/fruits', 'parts.js'), 'utf8');

function makeCtx() {
  const g = { addColorStop() {} };
  return {
    setTransform() {}, save() {}, restore() {}, scale() {}, rotate() {}, translate() {},
    clearRect() {}, fillRect() {}, beginPath() {}, closePath() {}, moveTo() {}, lineTo() {},
    arc() {}, ellipse() {}, clip() {}, stroke() {}, fill() {}, setLineDash() {},
    drawImage() {}, createLinearGradient: () => g, createRadialGradient: () => g,
    measureText: () => ({ width: 10 }), fillText() {}, strokeText() {},
    globalAlpha: 1, fillStyle: '', strokeStyle: '', lineWidth: 1,
    font: '', textAlign: '', textBaseline: '', lineCap: ''
  };
}

function buildGame(gap) {
  const listeners = new Map();
  function makeEl(id) {
    const el = {
      id, style: {}, textContent: '', width: 680, height: 160, _c: new Set(),
      classList: {
        add: c => el._c.add(c), remove: c => el._c.delete(c), contains: c => el._c.has(c),
        toggle: (c, on) => { const w = on === undefined ? !el._c.has(c) : !!on; w ? el._c.add(c) : el._c.delete(c); return w; }
      },
      getContext: () => el._ctx || (el._ctx = makeCtx()),
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 420, height: 700 }),
      addEventListener(t, fn) { if (!listeners.has(el)) listeners.set(el, {}); listeners.get(el)[t] = fn; },
      querySelector: () => ({ textContent: '', style: {}, classList: { add() {}, remove() {} } }),
      setAttribute() {}, offsetWidth: 100
    };
    return el;
  }
  const els = {};
  ['game', 'stage', 'overlay', 'score', 'best', 'finalScore', 'finalBest', 'next', 'chain',
   'soundBtn', 'resetBtn', 'restartBtn', 'helpBtn', 'dialog', 'overEmoji', 'overTitle',
   'winCelebrate', 'winPhoto'].forEach(id => els[id] = makeEl(id));

  const rafQueue = [];
  const sandbox = {
    console, Math, Date, JSON, Object, Array, Number, String, Boolean, Error, isNaN,
    performance: { now: () => Date.now() },
    requestAnimationFrame(fn) { rafQueue.push(fn); return 1; },
    setTimeout: () => 0, clearTimeout,
    document: { readyState: 'complete', getElementById: id => els[id] || null,
                addEventListener() {}, createElement: () => makeEl('tmp') },
    localStorage: { _d: {}, getItem(k) { return this._d[k] ?? null; }, setItem(k, v) { this._d[k] = String(v); } },
    addEventListener() {}, navigator: {},
    Image: class {
      constructor() { this.width = 512; this.height = 512; this.onload = null; this.onerror = null; }
      set src(v) { this._src = v; if (this.onload) this.onload(); }
      get src() { return this._src; }
    }
  };
  sandbox.window = sandbox; sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(partsSrc, sandbox, { filename: 'parts.js' });

  const patched = gameSrc.replace(/const HELP_GAP\s*=\s*\d+;/, 'const HELP_GAP = ' + gap + ';');
  if (patched === gameSrc && gap !== 34) throw new Error('HELP_GAP 替换失败，检查源码那一行的写法');
  vm.runInContext(patched, sandbox, { filename: 'game.js' });

  let t = Date.now();
  const pump = (frames) => {
    for (let f = 0; f < frames; f++) {
      t += 16.7;
      rafQueue.splice(0, rafQueue.length).forEach(fn => fn(t));
    }
  };
  return { U: sandbox.__DNW__, S: sandbox.__DNW__.state, pump,
           down: listeners.get(els.stage).pointerdown,
           helpClick: listeners.get(els.helpBtn).click };
}

function trial(gap, seed) {
  const { U, S, pump, down, helpClick } = buildGame(gap);
  let s = seed;
  const rnd = () => (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  U.reset(); pump(3);
  for (let i = 0; i < 400; i++) {
    if (S.over || (S.danger && i > 20)) break;
    down({ clientX: 40 + rnd() * 340, clientY: 120, pointerType: 'mouse' });
    pump(26);
  }
  const ballsBefore = S.balls.length;
  let clicks = 0, cleared = 0, deadClicks = 0, firstClickClear = -1;
  while (!S.over && clicks < 25) {
    const n0 = S.balls.length;
    helpClick(); pump(2);
    clicks++;
    const c = n0 - S.balls.length;
    cleared += c;
    if (c === 0) deadClicks++;
    if (firstClickClear < 0) firstClickClear = c;
  }
  return { won: S.win === true, clicks, ballsBefore, cleared, deadClicks, firstClickClear,
           tier: S.balls.reduce((m, b) => Math.max(m, b.tier), 0) };
}

/* 对照实验：同样乱投，一组卡住就点「帮我一把」，一组完全不点。
   看这个按钮到底让玩家多活多久、最高能合到几级。 */
function survival(gap, seed, useHelp) {
  const { U, S, pump, down, helpClick } = buildGame(gap);
  let s = seed;
  const rnd = () => (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  U.reset(); pump(3);
  let drops = 0, helpClicks = 0;
  for (let i = 0; i < 3000 && !S.over; i++) {
    if (useHelp && S.danger && helpClicks < 400) { helpClick(); helpClicks++; pump(3); if (S.over) break; }
    down({ clientX: 40 + rnd() * 340, clientY: 120, pointerType: 'mouse' });
    drops++;
    pump(26);
  }
  return { drops, won: S.win === true, tier: S.balls.reduce((m, b) => Math.max(m, b.tier), 0), helpClicks };
}

function compare(gap) {
  const off = [], on = [];
  for (let seed = 1; seed <= 10; seed++) { off.push(survival(gap, seed, false)); on.push(survival(gap, seed, true)); }
  const avg = (a, k) => (a.reduce((x, r) => x + r[k], 0) / a.length).toFixed(1);
  console.log('\n对照实验（每边 10 局，乱投到输）：');
  console.log('  不用按钮：平均活 ' + avg(off, 'drops') + ' 次投放，最高合到 tier ' + avg(off, 'tier') + '，通关 ' + off.filter(r => r.won).length + '/10');
  console.log('  用了按钮：平均活 ' + avg(on, 'drops') + ' 次投放，最高合到 tier ' + avg(on, 'tier') + '，通关 ' + on.filter(r => r.won).length + '/10');
  console.log('  （平均点了 ' + avg(on, 'helpClicks') + ' 次按钮）');
}

const GAPS = [34, 80, 120, 160, 220, 320, 9999];
console.log('HELP_GAP 扫描（每个值 12 局；乱投到警戒线后连点 25 次「帮我一把」）\n');
console.log('gap   | 首次点击清掉 | 单次点击没反应 | 整轮清掉占比 | 通关');
console.log('------+--------------+----------------+--------------+------');
for (const gap of GAPS) {
  const rs = [];
  for (let seed = 1; seed <= 12; seed++) rs.push(trial(gap, seed));
  const totalClicks = rs.reduce((a, r) => a + r.clicks, 0);
  const deadRate = rs.reduce((a, r) => a + r.deadClicks, 0) / totalClicks * 100;
  const firstAvg = (rs.reduce((a, r) => a + r.firstClickClear, 0) / rs.length).toFixed(1);
  const frac = (rs.reduce((a, r) => a + r.cleared / Math.max(1, r.ballsBefore), 0) / rs.length * 100).toFixed(0);
  const wins = rs.filter(r => r.won).length;
  console.log('%s | %s | %s | %s | %s',
    String(gap).padStart(5), String(firstAvg).padStart(12) + ' 颗',
    String(deadRate.toFixed(0) + '%').padStart(14), String(frac + '%').padStart(12),
    String(wins + '/12').padStart(5));
}

compare(160);

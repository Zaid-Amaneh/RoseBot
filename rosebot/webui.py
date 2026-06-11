

import json

from rosebot import domain as d

COLOR_HEX = {
    "red": "#e23b3b", "pink": "#ff8fb3", "white": "#fafafa", "crimson": "#8e1d2d",
    "yellow": "#f2d335", "violet": "#8a5cd1", "orange": "#f08a2e", "green": "#3fa34d",
    "mauve": "#b784a7", "purple": "#7d3cc1", "gold": "#d4af37", "lightpink": "#ffc6d9",
}
# Accent color per flower type (pavilion badge).
TYPE_HEX = {"Rose": "#e23b3b", "Tulip": "#7d3cc1", "Orchid": "#9b59b6", "Goliat": "#d4af37"}


def build_payload(states: list[dict]) -> dict:
    return {
        "levelName": d.LEVEL_NAME,
        "grid": {"w": d.GRID_W, "h": d.GRID_H},
        "warehouse": list(d.WAREHOUSE),
        "robotStart": list(d.ROBOT_START),
        "maxLoad": d.MAX_LOAD,
        "colorHex": COLOR_HEX,
        "typeHex": TYPE_HEX,
        "pavilions": [
            {
                "pid": p.pid,
                "type": p.ftype,
                "pos": list(p.pos),
                "needs": [[c, n] for c, n in sorted(p.needs.items())],
            }
            for p in d.PAVILIONS
        ],
        "steps": states,
    }


def render_html(states: list[dict]) -> str:
    data = json.dumps(build_payload(states))
    return _TEMPLATE.replace("/*__DATA__*/", data)


def write_html(states: list[dict], path: str = "rosebot_ui.html") -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html(states))
    return path


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RoseBot — Smart Flower Exhibition</title>
<style>
  :root { --cell: 104px; --gap: 6px; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, Segoe UI, Roboto, Arial, sans-serif;
         background: #0f1426; color: #e8ecf6; }
  header { padding: 16px 24px; border-bottom: 1px solid #232a44; }
  header h1 { margin: 0; font-size: 20px; }
  header p { margin: 4px 0 0; color: #9aa3c0; font-size: 13px; }
  .wrap { display: flex; gap: 24px; padding: 24px; flex-wrap: wrap; }
  .board { position: relative; background: #161c33; border: 1px solid #232a44;
           border-radius: 12px; padding: var(--gap); }
  .grid { position: relative; }
  .cell { position: absolute; width: var(--cell); height: var(--cell);
          background: #1c2440; border: 1px solid #2a335a; border-radius: 8px;
          display: flex; align-items: flex-start; justify-content: flex-end; }
  .cell .coord { font-size: 10px; color: #5a648c; padding: 4px 6px; }
  .cell.wh { background: #2a2438; border-color: #6b4f9e; }
  .marker { position: absolute; width: var(--cell); height: var(--cell);
            border-radius: 8px; padding: 6px; font-size: 11px; line-height: 1.25;
            pointer-events: none; }
  .pav { border: 2px solid; }
  .pav .pid { font-weight: 700; font-size: 13px; }
  .pav .needs { margin-top: 2px; display: flex; flex-wrap: wrap; gap: 3px; }
  .chip { display: inline-flex; align-items: center; gap: 3px; padding: 1px 5px;
          border-radius: 10px; background: #0d1224; font-size: 10px; }
  .chip.done { opacity: .35; text-decoration: line-through; }
  .dot { width: 9px; height: 9px; border-radius: 50%; border: 1px solid #00000055; }
  .whlabel { color: #d8c5ff; font-weight: 700; font-size: 12px; }
  .robot { position: absolute; width: calc(var(--cell) * .54); height: calc(var(--cell) * .54);
           border-radius: 50%; background: radial-gradient(circle at 35% 30%, #7ad0ff, #2f7fd6);
           border: 2px solid #bfe4ff; box-shadow: 0 0 14px #2f7fd6aa;
           display: flex; align-items: center; justify-content: center; font-size: 22px;
           transition: left .45s ease, top .45s ease; z-index: 5; }
  .panel { min-width: 300px; flex: 1; }
  .card { background: #161c33; border: 1px solid #232a44; border-radius: 12px;
          padding: 16px; margin-bottom: 16px; }
  .controls button { background: #2f7fd6; color: #fff; border: 0; border-radius: 8px;
          padding: 8px 14px; font-size: 14px; cursor: pointer; margin-right: 8px; }
  .controls button:hover { background: #3f8fe6; }
  .controls input[type=range] { width: 100%; margin-top: 12px; }
  .stat { display: flex; justify-content: space-between; padding: 4px 0;
          border-bottom: 1px dashed #2a335a; font-size: 13px; }
  .op { font-family: ui-monospace, Menlo, Consolas, monospace; color: #9fe0a0; }
  .load { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; min-height: 22px; }
  .muted { color: #9aa3c0; }
  .done-badge { color: #9fe0a0; font-weight: 700; }
</style>
</head>
<body>
<header>
  <h1>RoseBot — Smart Flower Exhibition 🌹🤖</h1>
  <p id="levelName">Optimal A* delivery plan.</p>
  <p>Animated on the grid. R = Robot, W = Warehouse, P# = Pavilion.</p>
</header>
<div class="wrap">
  <div class="board"><div class="grid" id="grid"></div></div>
  <div class="panel">
    <div class="card controls">
      <button id="prev">⏮ Prev</button>
      <button id="play">▶ Play</button>
      <button id="next">Next ⏭</button>
      <input type="range" id="slider" min="0" value="0">
      <div class="stat"><span>Step</span><span id="stepLabel">0 / 0</span></div>
      <div class="stat"><span>Cost so far (g)</span><span id="cost">0</span></div>
      <div class="stat"><span>Operation</span><span class="op" id="op">START</span></div>
    </div>
    <div class="card">
      <div class="muted">Robot is carrying</div>
      <div class="load" id="load"></div>
    </div>
    <div class="card">
      <div class="muted" id="goalState">Pavilion needs remaining</div>
      <div id="pavList"></div>
    </div>
  </div>
</div>

<script id="data" type="application/json">/*__DATA__*/</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const CELL = 104, GAP = 6;
const colorHex = c => DATA.colorHex[c] || '#888';

// show the level name in the header
if (DATA.levelName) document.getElementById('levelName').textContent =
  'Level: ' + DATA.levelName;

// ---- build the static grid -------------------------------------------------
const grid = document.getElementById('grid');
grid.style.width  = (DATA.grid.w * (CELL + GAP)) + 'px';
grid.style.height = (DATA.grid.h * (CELL + GAP)) + 'px';
function cellLeft(x){ return (x - 1) * (CELL + GAP); }
function cellTop(y){ return (y - 1) * (CELL + GAP); }

for (let y = 1; y <= DATA.grid.h; y++) {
  for (let x = 1; x <= DATA.grid.w; x++) {
    const c = document.createElement('div');
    c.className = 'cell';
    if (DATA.warehouse[0] === y && DATA.warehouse[1] === x) c.className += ' wh';
    c.style.left = cellLeft(x) + 'px';
    c.style.top  = cellTop(y) + 'px';
    c.innerHTML = '<span class="coord">Y' + y + ' X' + x + '</span>';
    grid.appendChild(c);
  }
}
// warehouse label
{
  const w = document.createElement('div');
  w.className = 'marker';
  w.style.left = cellLeft(DATA.warehouse[1]) + 'px';
  w.style.top  = cellTop(DATA.warehouse[0]) + 'px';
  w.innerHTML = '<div class="whlabel">🏬 W — Warehouse</div>';
  grid.appendChild(w);
}
// pavilion markers (needs filled in per step)
const pavEls = {};
DATA.pavilions.forEach(p => {
  const el = document.createElement('div');
  el.className = 'marker pav';
  el.style.left = cellLeft(p.pos[1]) + 'px';
  el.style.top  = cellTop(p.pos[0]) + 'px';
  el.style.borderColor = DATA.typeHex[p.type] || '#888';
  grid.appendChild(el);
  pavEls[p.pid] = el;
});
// robot
const robot = document.createElement('div');
robot.className = 'robot';
robot.textContent = '🤖';
grid.appendChild(robot);

// ---- per-step rendering ----------------------------------------------------
const steps = DATA.steps;
const slider = document.getElementById('slider');
slider.max = steps.length - 1;

function needsMap(step) {           // pid -> {color: remaining}
  const m = {};
  step.needs.forEach(([pid, color, n]) => { (m[pid] = m[pid] || {})[color] = n; });
  return m;
}

function render(i) {
  const step = steps[i];
  // robot
  robot.style.left = (cellLeft(step.pos[1]) + (CELL - CELL * 0.54) / 2) + 'px';
  robot.style.top  = (cellTop(step.pos[0]) + (CELL - CELL * 0.54) / 2) + 'px';
  // stats
  document.getElementById('stepLabel').textContent = i + ' / ' + (steps.length - 1);
  document.getElementById('cost').textContent = step.g;
  document.getElementById('op').textContent = step.op;
  slider.value = i;
  // load
  const load = document.getElementById('load');
  load.innerHTML = '';
  if (!step.load.length) {
    load.innerHTML = '<span class="muted">— empty —</span>';
  } else {
    step.load.forEach(([type, color, n]) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = '<span class="dot" style="background:' + colorHex(color) + '"></span>' +
                       type + ' ' + color + ' ×' + n;
      load.appendChild(chip);
    });
  }
  // pavilions remaining needs
  const nm = needsMap(step);
  let allDone = true;
  DATA.pavilions.forEach(p => {
    const rem = nm[p.pid] || {};
    const chips = p.needs.map(([color, base]) => {
      const left = rem[color] || 0;
      if (left > 0) allDone = false;
      const cls = left > 0 ? 'chip' : 'chip done';
      return '<span class="' + cls + '"><span class="dot" style="background:' +
             colorHex(color) + '"></span>' + color + ' ' + (base - left) + '/' + base + '</span>';
    }).join('');
    pavEls[p.pid].innerHTML =
      '<div class="pid" style="color:' + (DATA.typeHex[p.type] || '#fff') + '">' +
      p.pid + ' · ' + p.type + '</div><div class="needs">' + chips + '</div>';
  });
  // side list
  document.getElementById('pavList').innerHTML = DATA.pavilions.map(p => {
    const rem = nm[p.pid] || {};
    const total = Object.values(rem).reduce((a, b) => a + b, 0);
    const txt = total === 0 ? '<span class="done-badge">✓ done</span>'
                            : (total + ' left');
    return '<div class="stat"><span>' + p.pid + ' · ' + p.type +
           ' (Y' + p.pos[0] + ' X' + p.pos[1] + ')</span><span>' + txt + '</span></div>';
  }).join('');
  document.getElementById('goalState').textContent =
    allDone ? 'GOAL reached — all pavilions satisfied, robot empty 🎉'
            : 'Pavilion needs remaining';
}

// ---- controls --------------------------------------------------------------
let cur = 0, timer = null;
function go(i){ cur = Math.max(0, Math.min(steps.length - 1, i)); render(cur); }
document.getElementById('prev').onclick = () => { stop(); go(cur - 1); };
document.getElementById('next').onclick = () => { stop(); go(cur + 1); };
slider.oninput = e => { stop(); go(+e.target.value); };
function stop(){ if (timer){ clearInterval(timer); timer = null;
                 document.getElementById('play').textContent = '▶ Play'; } }
document.getElementById('play').onclick = () => {
  if (timer) { stop(); return; }
  document.getElementById('play').textContent = '⏸ Pause';
  if (cur >= steps.length - 1) cur = 0;
  timer = setInterval(() => {
    if (cur >= steps.length - 1) { stop(); return; }
    go(cur + 1);
  }, 650);
};
render(0);
</script>
</body>
</html>
"""

# RoseBot — Smart Flower Exhibition 🌹🤖

A **Rule-Based Expert System** built with **Python + [`experta`](https://github.com/nilp0inter/experta)**
that simulates a robot distributing flower bouquets from a central warehouse to exhibition
pavilions on a Grid, at the lowest possible cost — by modeling the problem as a search tree and
solving it with **A\***.

> Project for the **Knowledge-Based Systems** course — Damascus University, Faculty of Informatics
> Engineering, AI Department.

## ⚙️ Setup

> Requires **Python 3.10** (`experta` does not run on newer versions without patching).

```bash
uv python install 3.10   # if needed
uv sync                  # install dependencies (experta)
```

> Compatibility note: `rosebot/compat.py` is imported before `experta` to fix a `frozendict`
> incompatibility on Python 3.10.

## ▶️ Running

```bash
uv run python main.py astar           # optimal A* solution (f = g + h)  -> cost 27
uv run python main.py astar-strategy  # same, via the in-engine custom priority Strategy
uv run python main.py dfs             # default Recency/Depth-First search tree (Deliverable 5)
uv run python main.py ui              # Tkinter desktop visualization (animated; needs a display)
uv run python main.py web             # build rosebot_ui.html (animated, opens in any browser)
```

The **`ui`** mode opens a window with the 5×5 grid, the robot moving cell to cell, and a
side panel of each pavilion's remaining needs ticking to zero (Prev / Play / Next).
The **`web`** mode writes a self-contained `rosebot_ui.html` you can open in a browser.

## 🏗️ Status

All six deliverables are implemented, returning the optimal cost **27**:

1. Initial State (facts) · 2. Generate Path Rules (move / load / unload) ·
3. Constraint Violation Rules · 4. Find & Print Solution · 5. Print Search Tree (Recency/DFS) ·
6. Optimal A* (`f = g + h`) — the engine's agenda, ordered by a custom `experta` Strategy
   (`FStrategy`), *is* the A\* priority queue, so `engine.run()` itself performs best-first search.

The search control (which node to expand, when to stop) is fully rule-driven via salience +
the `FStrategy` agenda order — there is no hand-written search loop.

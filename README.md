# RoseBot — Smart Flower Exhibition 🌹🤖

A **Rule-Based Expert System** built with **Python + [`experta`](https://github.com/nilp0inter/experta)**
that simulates a robot distributing flower bouquets from a central warehouse to exhibition
pavilions on a Grid, at the lowest possible cost — by modeling the problem as a search tree and
solving it with **A\***.

> Project for the **Knowledge-Based Systems** course — Damascus University, Faculty of Informatics
> Engineering, AI Department.

## 📚 Documentation

| File | Contents |
|------|----------|
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | General requirements (overview). |
| [`docs/REQUIREMENTS_DETAILED.md`](docs/REQUIREMENTS_DETAILED.md) | Detailed requirements (all rules and deliverables). |
| [`docs/APPROACH.md`](docs/APPROACH.md) | Implementation plan, technical ideas, build stages. |
| [`docs/explain/index.html`](docs/explain/index.html) | Step-by-step interactive explanation of the project (Arabic, 9 pages). |
| [`docs/code/index.html`](docs/code/index.html) | Detailed code walkthrough — one page per source file (Arabic, 8 pages). |

## ⚙️ Setup

> Requires **Python 3.10** (`experta` does not run on newer versions without patching).

```bash
uv python install 3.10   # if needed
uv sync                  # install dependencies (experta)
```

> Compatibility note: `rosebot/compat.py` is imported before `experta` to fix a `frozendict`
> incompatibility on Python 3.10. Details in [`docs/APPROACH.md`](docs/APPROACH.md).

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

## ✅ Validation

Self-checking scripts (run from the project root):

```bash
uv run python verify_all.py      # one-shot: imports, both A* drivers, DFS, no-Arabic
uv run python check_stages.py    # initial state, generation rules, constraints
uv run python check_astar.py     # A* optimality vs. an independent Dijkstra oracle
uv run python check_strategy.py  # in-engine FStrategy reaches the same optimum
uv run python check_dfs.py       # search-tree generation
uv run python check_ui.py        # the visualization payload + HTML build
```

## 🏗️ Status

All six deliverables are implemented and verified:

1. Initial State (facts) · 2. Generate Path Rules · 3. Constraint Violation Rules ·
4. Find & Print Solution · 5. Print Search Tree (Recency/DFS) ·
6. Optimal A* (`f = g + h`) — both an external best-first loop and an in-engine custom
   `experta` Strategy, each returning the optimal cost **27** (confirmed against a
   Dijkstra oracle).

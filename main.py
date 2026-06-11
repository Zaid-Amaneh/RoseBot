"""RoseBot entry point.

Usage:
    uv run python main.py astar           # Deliverable 6: optimal A* (f = g + h)
    uv run python main.py astar-strategy  # Deliverable 6: A* via in-engine priority Strategy
    uv run python main.py dfs             # Deliverable 5: search tree (default Recency/DFS)
    uv run python main.py ui              # open the Tkinter desktop visualization (needs a display)
    uv run python main.py web             # build a self-contained animated HTML visualization

Level selection (which problem instance to solve):
    uv run python main.py astar --level 2              # loads levels/level2.json
    uv run python main.py ui --level levels/level3.json
    uv run python main.py astar                        # default = levels/level1.json

Default mode is ``astar``.
"""

import argparse
import os
import sys

import rosebot.compat  # noqa: F401  # must precede any experta import

from rosebot import domain, search

LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels")


def resolve_level_path(level: str | None) -> str:
    """Map a --level value to a JSON path.

    ``None`` -> levels/level1.json (default); a bare number N -> levels/levelN.json;
    anything ending in .json -> that path as given.
    """
    if level is None:
        return os.path.join(LEVELS_DIR, "level1.json")
    if level.endswith(".json"):
        return level
    if level.isdigit():
        return os.path.join(LEVELS_DIR, f"level{level}.json")
    # treat as a name stem under levels/
    return os.path.join(LEVELS_DIR, f"{level}.json")


def load_selected_level(level: str | None) -> int:
    """Load + validate + apply the chosen level. Return 0 on success, non-zero on error."""
    path = resolve_level_path(level)
    try:
        config = domain.load_level(path)
        domain.apply_level(config)
    except FileNotFoundError:
        print(f"Level file not found: {path}")
        print("Available levels are in the 'levels/' folder (e.g. --level 1).")
        return 1
    except ValueError as e:  # raised by validate_level
        print(str(e))
        return 1
    print(f"Level: {domain.LEVEL_NAME}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="main.py", description="RoseBot — bouquet-delivery robot (rule-based A*).")
    parser.add_argument(
        "mode", nargs="?", default="astar",
        choices=["astar", "astar-strategy", "dfs", "ui", "web"],
        help="what to run (default: astar)")
    parser.add_argument(
        "--level", default=None,
        help="level to solve: a number (1, 2, ...) or a path to a .json file "
             "(default: levels/level1.json)")
    args = parser.parse_args(argv[1:])

    rc = load_selected_level(args.level)
    if rc != 0:
        return rc
    mode = args.mode

    if mode == "dfs":
        print("=== Deliverable 5: Search Tree (default Recency / Depth-First) ===")
        print("(showing the first generated states; the full state space is large,")
        print(" so use 'astar' to find the optimal solution)\n")
        engine = search.run_dfs(max_nodes=150)  # prints the tree as it is generated
        search.print_solve_time(engine)
        if search.solution_node(engine) is not None:
            search.print_solution(engine)
        return 0

    if mode == "astar":
        print("=== Deliverable 6: Optimal A* search (f = g + h) ===")
        engine = search.run_astar(trace=False)
        print(f"(generated {engine._count} nodes)")
        search.print_solve_time(engine)
        search.print_solution(engine)
        return 0

    if mode == "astar-strategy":
        print("=== Deliverable 6: A* via custom priority Strategy (in-engine) ===")
        engine = search.run_astar_strategy(trace=False)
        print(f"(generated {engine._count} nodes)")
        search.print_solve_time(engine)
        search.print_solution(engine)
        return 0

    if mode == "ui":
        from rosebot import desktop_ui
        print("=== Opening Tkinter desktop visualization ===")
        try:
            return desktop_ui.launch()
        except tk_error() as e:
            print(f"Could not open a window (no graphical display?): {e}")
            print("Use 'uv run python main.py web' for the browser version instead.")
            return 1

    if mode == "web":
        from rosebot import webui
        print("=== Building animated HTML visualization from the optimal A* plan ===")
        engine = search.run_astar(trace=False)
        goal = search.solution_node(engine)
        if goal is None:
            print("No solution to visualize.")
            return 1
        states = search.reconstruct_states(engine, goal["nid"])
        path = webui.write_html(states, "rosebot_ui.html")
        search.print_solve_time(engine)
        print(f"Wrote {path} ({len(states)} steps, total cost {goal['g']}).")
        print("Open it in a browser:")
        print(f"  xdg-open {path}   # Linux")
        print(f"  open {path}       # macOS")
        return 0

    return 2  # unreachable (argparse 'choices' guards mode)


def tk_error():
    """Tcl/Tk error class (when a display is unavailable), import-safe."""
    import tkinter
    return tkinter.TclError


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

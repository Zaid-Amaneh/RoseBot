"""RoseBot entry point.

Usage:
    uv run python main.py astar           # Deliverable 6: optimal A* (f = g + h)
    uv run python main.py astar-strategy  # Deliverable 6: A* via in-engine priority Strategy
    uv run python main.py dfs             # Deliverable 5: search tree (default Recency/DFS)
    uv run python main.py ui              # open the Tkinter desktop visualization (needs a display)
    uv run python main.py web             # build a self-contained animated HTML visualization

Default mode is ``astar``.
"""

import sys

import rosebot.compat  # noqa: F401  # must precede any experta import

from rosebot import search


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "astar"

    if mode == "dfs":
        print("=== Deliverable 5: Search Tree (default Recency / Depth-First) ===")
        print("(showing the first generated states; the full state space is large,")
        print(" so use 'astar' to find the optimal solution)\n")
        engine = search.run_dfs(max_nodes=150)  # prints the tree as it is generated
        if search.solution_node(engine) is not None:
            search.print_solution(engine)
        return 0

    if mode == "astar":
        print("=== Deliverable 6: Optimal A* search (f = g + h) ===")
        engine = search.run_astar(trace=False)
        print(f"(generated {engine._count} nodes)")
        search.print_solution(engine)
        return 0

    if mode == "astar-strategy":
        print("=== Deliverable 6: A* via custom priority Strategy (in-engine) ===")
        engine = search.run_astar_strategy(trace=False)
        print(f"(generated {engine._count} nodes)")
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
        print(f"Wrote {path} ({len(states)} steps, total cost {goal['g']}).")
        print("Open it in a browser:")
        print(f"  xdg-open {path}   # Linux")
        print(f"  open {path}       # macOS")
        return 0

    print(f"Unknown mode: {mode!r}. Use 'astar', 'astar-strategy', 'dfs', 'ui' or 'web'.")
    return 2


def tk_error():
    """Tcl/Tk error class (when a display is unavailable), import-safe."""
    import tkinter
    return tkinter.TclError


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

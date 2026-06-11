"""Search orchestration and printing (Deliverables 4 & 5).

The search itself is rule-driven (see ``engine.py``); these functions just build an
engine, pick a conflict-resolution strategy, run it, and read/print the result. There is
no search algorithm here — ``engine.run()`` *is* the search.

- ``run_astar`` / ``run_astar_strategy`` : best-first A* via the custom ``FStrategy``
  (agenda ordered by f = g + h). Identical; two names for the two CLI modes.
- ``run_dfs`` : the engine under Experta's default Recency/Depth-First strategy.
- printing / path helpers read the resulting ``Node`` facts.
"""

import time

from rosebot import domain as d
from rosebot.facts import Node, Solution, ShowTree, ShowSolution
from rosebot.engine import RoseBotEngine
from rosebot.heuristics import h_needs


# --------------------------------------------------------------------------- #
# Reading results                                                              #
# --------------------------------------------------------------------------- #
def _nodes(engine) -> dict[int, Node]:
    return {f["nid"]: f for f in engine.facts.values() if isinstance(f, Node)}


def solution_node(engine):
    nodes = _nodes(engine)
    for f in engine.facts.values():
        if isinstance(f, Solution):
            return nodes.get(f["nid"])
    return None


def reconstruct_path(engine, goal_nid: int) -> list[tuple[str, int]]:
    """[(op, g), ...] from the root down to ``goal_nid``."""
    nodes = _nodes(engine)
    chain: list[tuple[str, int]] = []
    nid = goal_nid
    while nid != -1 and nid in nodes:
        n = nodes[nid]
        chain.append((n["op"], n["g"]))
        nid = n["parent"]
    chain.reverse()
    return chain


def reconstruct_states(engine, goal_nid: int) -> list[dict]:
    """Full per-step state from root to ``goal_nid`` (used by the UI)."""
    nodes = _nodes(engine)
    chain: list[dict] = []
    nid = goal_nid
    while nid != -1 and nid in nodes:
        n = nodes[nid]
        chain.append({
            "nid": n["nid"], "op": n["op"], "g": n["g"],
            "pos": [n["ry"], n["rx"]],
            "load": [list(x) for x in n["load"]],
            "needs": [list(x) for x in n["needs"]],
        })
        nid = n["parent"]
    chain.reverse()
    return chain


# --------------------------------------------------------------------------- #
# Printing                                                                     #
# --------------------------------------------------------------------------- #
def print_search_tree(engine) -> None:
    """Print every generated state — done by the ``print_node`` rule, not a loop.

    NOTE: in DFS mode the tree is printed *during* ``run_dfs`` (it declares ShowTree);
    this standalone helper resumes the engine, so prefer ``run_dfs`` for the tree.
    """
    engine.declare(ShowTree())
    engine.run()


def print_solution(engine) -> bool:
    """Print the solution path via the recursive ``sol_*`` rules (no Python loop)."""
    if solution_node(engine) is None:
        print("\nNo solution found.")
        return False
    engine.declare(ShowSolution())
    engine.run()
    return True


def print_solve_time(engine) -> None:
    elapsed = getattr(engine, "solve_seconds", None)
    if elapsed is not None:
        print(f"(solve time: {elapsed:.6f} seconds)")


def _run_timed(engine, max_nodes=None):
    started = time.perf_counter()
    if max_nodes is None:
        engine.run()
    else:
        engine.run(max_nodes)
    engine.solve_seconds = time.perf_counter() - started
    return engine


# --------------------------------------------------------------------------- #
# Run modes (no search algorithm here — the rules do the search)              #
# --------------------------------------------------------------------------- #
def run_astar(heuristic=h_needs, max_nodes=None, trace=False):
    """Deliverable 6: optimal A*. ``FStrategy`` orders the agenda by f = g + h, so the
    engine expands the lowest-f node first; ``goal_reached`` fires when the goal node's f is
    the agenda minimum (no cheaper path remains) => optimal.

    ``max_nodes`` / ``trace`` are accepted for call-site compatibility but unused: the search
    is bounded naturally by the finite, dedup'd state space, not by an external node cap.
    """
    from rosebot.strategy import FStrategy
    engine = RoseBotEngine(heuristic=heuristic)
    engine.strategy = FStrategy()
    engine.reset()
    return _run_timed(engine)


# The "in-engine custom Strategy" mode is now the primary A* itself.
run_astar_strategy = run_astar


def run_dfs(trace=False, max_nodes=2000):
    """Deliverable 5: run under Experta's default Recency/Depth-First strategy, bounded to
    ``max_nodes`` activations so the generated search tree stays printable.
    """
    engine = RoseBotEngine(heuristic=None)
    engine.reset()
    engine.declare(ShowTree())     # the print_node rule prints each state as it is generated
    # Experta's run(limit): fire at most this many activations
    return _run_timed(engine, max_nodes)

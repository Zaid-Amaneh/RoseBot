import time

from rosebot import domain as d
from rosebot.facts import Node, Solution, ShowTree, ShowSolution
from rosebot.engine import RoseBotEngine
from rosebot.heuristics import h_needs


def _nodes(engine) -> dict[int, Node]:
    return {f["nid"]: f for f in engine.facts.values() if isinstance(f, Node)}


def solution_node(engine):
    nodes = _nodes(engine)
    for f in engine.facts.values():
        if isinstance(f, Solution):
            return nodes.get(f["nid"])
    return None


def reconstruct_path(engine, goal_nid: int) -> list[tuple[str, int]]:
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

def print_search_tree(engine) -> None:
    
    engine.declare(ShowTree())
    engine.run()


def print_solution(engine) -> bool:
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


def run_astar(heuristic=h_needs, max_nodes=None, trace=False):
    
    from rosebot.strategy import FStrategy
    engine = RoseBotEngine(heuristic=heuristic)
    engine.strategy = FStrategy()
    engine.reset()
    return _run_timed(engine)


run_astar_strategy = run_astar


def run_dfs(trace=False, max_nodes=2000, max_depth=None):
    
    engine = RoseBotEngine(heuristic=None, max_depth=max_depth)
    engine.reset()
    engine.declare(ShowTree())     
    return _run_timed(engine, max_nodes)

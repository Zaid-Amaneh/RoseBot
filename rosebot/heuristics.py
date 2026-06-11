from rosebot import domain as d


def h_zero(pos, load, needs) -> int:
    """Trivial admissible heuristic. Turns A* into uniform-cost search."""
    return 0


def h_needs(pos, load, needs) -> int:
    """Admissible & consistent heuristic = lower bounds on the three cost types.

    * unloads: each pavilion that still has needs requires >= 1 unload.
    * loads:   ceil(undelivered_useful_bouquets / MAX_LOAD) more load operations.
    * moves:   the robot must at least travel to the nearest pavilion still in need.
    """
    if not needs:
        return 0

    pavilions_left = {pid for pid, _c, _n in needs}
    h_unload = len(pavilions_left)
    h_load = d.load_batches_lower_bound(needs, load)
    h_move = min(d.manhattan(pos, d.PAVILION_BY_ID[pid].pos)
                 for pid in pavilions_left)
    return h_unload + h_load + h_move

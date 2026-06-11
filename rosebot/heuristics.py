from rosebot import domain as d


def h_zero(pos, load, needs) -> int:
    return 0


def h_needs(pos, load, needs) -> int:
    
    if not needs:
        return 0

    pavilions_left = {pid for pid, _c, _n in needs}
    h_unload = len(pavilions_left)
    h_load = d.load_batches_lower_bound(needs, load)
    h_move = min(d.manhattan(pos, d.PAVILION_BY_ID[pid].pos)
                 for pid in pavilions_left)
    return h_unload + h_load + h_move

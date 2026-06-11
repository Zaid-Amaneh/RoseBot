from __future__ import annotations

import json
from math import ceil
from typing import Iterable

# --------------------------------------------------------------------------- #
# Flower types and their allowed colors                                        #
# --------------------------------------------------------------------------- #
FLOWER_COLORS: dict[str, frozenset[str]] = {
    "Rose": frozenset({"red", "pink", "white", "crimson"}),
    "Tulip": frozenset({"red", "yellow", "violet", "orange", "green", "mauve", "purple"}),
    "Orchid": frozenset({"purple", "white", "pink"}),
    "Goliat": frozenset({"gold", "lightpink", "yellow"}),
}

# --------------------------------------------------------------------------- #
# Grid and fixed positions (the authoritative instance)                       #
# --------------------------------------------------------------------------- #
GRID_W = 5  # columns: x in 1..GRID_W
GRID_H = 5  # rows:    y in 1..GRID_H
WAREHOUSE = (2, 3)  # (y, x)
ROBOT_START = (1, 3)  # (y, x)

# Movement deltas in (y, x): name -> (dy, dx)
MOVES: tuple[tuple[str, int, int], ...] = (
    ("up", -1, 0),
    ("down", +1, 0),
    ("left", 0, -1),
    ("right", 0, +1),
)


class PavilionSpec:
    """Static description of one pavilion."""

    __slots__ = ("pid", "ftype", "pos", "needs")

    def __init__(self, pid: str, ftype: str, pos: tuple[int, int],
                 needs: dict[str, int]) -> None:
        self.pid = pid
        self.ftype = ftype
        self.pos = pos  # (y, x)
        self.needs = needs  # {color: count}

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"PavilionSpec({self.pid}, {self.ftype}, {self.pos}, {self.needs})"


PAVILIONS: tuple[PavilionSpec, ...] = (
    PavilionSpec("P1", "Rose", (4, 2), {"red": 2, "pink": 1, "white": 1}),
    PavilionSpec("P2", "Tulip", (3, 4), {"red": 3, "yellow": 1}),
    PavilionSpec("P3", "Orchid", (5, 4), {"purple": 2, "pink": 1}),
    PavilionSpec("P4", "Goliat", (2, 5), {"gold": 2, "lightpink": 2}),
)

# Max load = the largest total need of any single pavilion.
MAX_LOAD = max(sum(p.needs.values()) for p in PAVILIONS)  # = 4

# Convenience lookups
PAVILION_BY_ID: dict[str, PavilionSpec] = {p.pid: p for p in PAVILIONS}
PAVILION_AT: dict[tuple[int, int], PavilionSpec] = {p.pos: p for p in PAVILIONS}

# Name of the instance currently loaded into the globals above. The hardcoded default
# (the original assignment instance) is Level 1; ``apply_level`` overwrites it.
LEVEL_NAME: str = "Level 1 — Original"


# --------------------------------------------------------------------------- #
# Geometry / legality helpers                                                  #
# --------------------------------------------------------------------------- #
def in_grid(y: int, x: int) -> bool:
    """True if (y, x) is inside the grid bounds."""
    return 1 <= y <= GRID_H and 1 <= x <= GRID_W


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Manhattan distance between two (y, x) positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def total_count(items: Iterable[tuple]) -> int:
    """Sum the ``count`` (last element) over (….., count) tuples."""
    return sum(it[-1] for it in items)


def is_legal_load(load: "Load") -> bool:
    """A load is legal iff it is empty, single-type (Option B), or single-color (Option A)."""
    types = {ft for ft, _c, _n in load}
    colors = {c for _ft, c, _n in load}
    return len(types) <= 1 or len(colors) <= 1


def within_max_load(load: "Load") -> bool:
    """True if the carried total does not exceed MAX_LOAD."""
    return total_count(load) <= MAX_LOAD


def is_valid_bouquet(ftype: str, color: str) -> bool:
    """True if ``color`` is a real color for ``ftype`` (a well-formed bouquet)."""
    return color in FLOWER_COLORS.get(ftype, frozenset())


def load_is_valid_bouquets(load: "Load") -> bool:
    """True if every carried bouquet is well-formed for its flower type."""
    return all(is_valid_bouquet(ft, c) for ft, c, _n in load)


# --------------------------------------------------------------------------- #
# Canonical state pieces                                                       #
# --------------------------------------------------------------------------- #
# A "load" is a sorted tuple of (ftype, color, count); () means empty.
# A "needs" set is a sorted tuple of (pid, color, count) for remaining needs only.
Load = tuple
Needs = tuple


def make_load(items: Iterable[tuple[str, str, int]]) -> Load:
    """Canonicalize a load: drop zero/negative counts, merge, and sort."""
    merged: dict[tuple[str, str], int] = {}
    for ftype, color, count in items:
        if count > 0:
            merged[(ftype, color)] = merged.get((ftype, color), 0) + count
    return tuple(sorted((ft, c, n) for (ft, c), n in merged.items()))


def make_needs(items: Iterable[tuple[str, str, int]]) -> Needs:
    """Canonicalize remaining needs: drop satisfied (count<=0) entries and sort."""
    merged: dict[tuple[str, str], int] = {}
    for pid, color, count in items:
        if count > 0:
            merged[(pid, color)] = merged.get((pid, color), 0) + count
    return tuple(sorted((pid, c, n) for (pid, c), n in merged.items()))


def initial_needs() -> Needs:
    """Full needs of every pavilion as a canonical needs tuple."""
    return make_needs(
        (p.pid, color, count)
        for p in PAVILIONS
        for color, count in p.needs.items()
    )


def state_signature(pos: tuple[int, int], load: Load, needs: Needs) -> tuple:
    """Hashable canonical signature of a logical state (for dedup / closed set)."""
    return (pos[0], pos[1], load, needs)


# --------------------------------------------------------------------------- #
# Load enumeration (pruned, legal-by-construction)                            #
# --------------------------------------------------------------------------- #
def _colors_still_needed(needs: Needs) -> set[str]:
    return {color for _pid, color, _n in needs}


def _types_still_needed(needs: Needs) -> set[str]:
    return {PAVILION_BY_ID[pid].ftype for pid, _color, _n in needs}


def _outstanding_units(needs: Needs) -> dict[tuple[str, str], int]:
    """Map (ftype, color) -> total outstanding units across pavilions."""
    out: dict[tuple[str, str], int] = {}
    for pid, color, count in needs:
        ftype = PAVILION_BY_ID[pid].ftype
        out[(ftype, color)] = out.get((ftype, color), 0) + count
    return out


def enumerate_loads(needs: Needs) -> list[Load]:
    """Return the candidate (legal, useful, max-load-capped) loads from empty.

    Only two legal load shapes exist:
      * Option A: a single color, mixed flower types that still need that color.
      * Option B: a single flower type, mixed colors that this type's pavilion still needs.
    Every included unit must be still-needed, and the total must not exceed MAX_LOAD.
    We prefer maximal useful loads (truncating to MAX_LOAD when necessary).
    """
    outstanding = _outstanding_units(needs)
    candidates: set[Load] = set()

    # Option A: fix a color, take one unit-group per type needing that color.
    for color in _colors_still_needed(needs):
        groups = sorted(
            ((ft, c, n) for (ft, c), n in outstanding.items() if c == color),
            key=lambda g: (g[0], g[1]),
        )
        load = _cap_to_max_load(groups)
        if load:
            candidates.add(load)

    # Option B: fix a type, take the colors that type's pavilion still needs.
    for ftype in _types_still_needed(needs):
        groups = sorted(
            ((ft, c, n) for (ft, c), n in outstanding.items() if ft == ftype),
            key=lambda g: (g[0], g[1]),
        )
        load = _cap_to_max_load(groups)
        if load:
            candidates.add(load)

    return sorted(candidates)


def _cap_to_max_load(groups: list[tuple[str, str, int]]) -> Load:
    """Take groups in order until MAX_LOAD is reached, truncating the last group."""
    chosen: list[tuple[str, str, int]] = []
    remaining = MAX_LOAD
    for ftype, color, count in groups:
        if remaining <= 0:
            break
        take = min(count, remaining)
        chosen.append((ftype, color, take))
        remaining -= take
    return make_load(chosen)


# --------------------------------------------------------------------------- #
# Unloading                                                                   #
# --------------------------------------------------------------------------- #
def unloadable(load: Load, pav: PavilionSpec, needs: Needs) -> list[tuple[str, int]]:
    """Colors (and amounts) the robot can drop at ``pav`` from its current load.

    A bouquet is deliverable iff its type matches the pavilion's type and the
    pavilion still needs that color. The amount delivered is
    ``min(carried_of_color, remaining_need_of_color)``.
    Returns a list of (color, amount) with amount > 0.
    """
    remaining_for_pav = {
        color: count for pid, color, count in needs if pid == pav.pid
    }
    carried_of = {
        color: count for ftype, color, count in load if ftype == pav.ftype
    }
    drops: list[tuple[str, int]] = []
    for color, need in remaining_for_pav.items():
        have = carried_of.get(color, 0)
        amount = min(have, need)
        if amount > 0:
            drops.append((color, amount))
    return sorted(drops)


def apply_unload(load: Load, pav: PavilionSpec,
                 drops: list[tuple[str, int]]) -> Load:
    """Return the new load after dropping ``drops`` (of ``pav.ftype``) at a pavilion."""
    drop_map = dict(drops)
    new_items: list[tuple[str, str, int]] = []
    for ftype, color, count in load:
        if ftype == pav.ftype and color in drop_map:
            count -= drop_map[color]
        if count > 0:
            new_items.append((ftype, color, count))
    return make_load(new_items)


def reduce_needs(needs: Needs, pid: str,
                 drops: list[tuple[str, int]]) -> Needs:
    """Return the new needs after satisfying ``drops`` at pavilion ``pid``."""
    drop_map = dict(drops)
    new_items: list[tuple[str, str, int]] = []
    for p, color, count in needs:
        if p == pid and color in drop_map:
            count -= drop_map[color]
        if count > 0:
            new_items.append((p, color, count))
    return make_needs(new_items)


def fmt_load(load: Load) -> str:
    """Human-readable load string, e.g. 'Rose:red x2 + Rose:pink x1'."""
    if not load:
        return "empty"
    return " + ".join(f"{ft}:{c} x{n}" for ft, c, n in load)


def fmt_drops(pid: str, drops: list[tuple[str, int]]) -> str:
    """Human-readable unload string, e.g. 'P1: red x2 + pink x1'."""
    return f"{pid}: " + " + ".join(f"{c} x{n}" for c, n in drops)


def remaining_total(needs: Needs) -> int:
    """Total number of bouquets still required across all pavilions."""
    return sum(n for _pid, _color, n in needs)


def load_batches_lower_bound(needs: Needs, load: Load) -> int:
    """Lower bound on the number of additional load operations still required."""
    outstanding = remaining_total(needs)
    already_useful = total_count(load)
    deficit = max(0, outstanding - already_useful)
    return ceil(deficit / MAX_LOAD) if deficit > 0 else 0


# --------------------------------------------------------------------------- #
# Levels: load a problem instance from a JSON file at startup                  #
# --------------------------------------------------------------------------- #
# The globals above (GRID_W, GRID_H, WAREHOUSE, ROBOT_START, PAVILIONS, and the
# derived MAX_LOAD / PAVILION_BY_ID / PAVILION_AT) describe ONE instance. Every
# consumer reads them via ``domain.X`` at call time, so ``apply_level`` can swap
# the whole instance once at startup (before any engine/UI is built).
#
# Layout-only: a level may change grid size, warehouse, robot start, and each
# pavilion's type/position/needs. Flower TYPES and their valid COLORS stay fixed
# (FLOWER_COLORS), so the UI color mapping never breaks.

def load_level(path: str) -> dict:
    """Read a level JSON file and return it as a plain dict (no validation yet)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_level(config: dict) -> None:
    """Raise ValueError with a clear message if the level is malformed or illegal.

    Checks (layout-only): grid sizes, in-grid positions, known flower types, valid
    colors per type, positive integer counts, unique pavilion ids and positions, and
    that no pavilion sits on the warehouse cell.
    """
    def err(msg: str):
        raise ValueError(f"Invalid level: {msg}")

    # --- grid -------------------------------------------------------------- #
    grid = config.get("grid")
    if not isinstance(grid, dict) or "w" not in grid or "h" not in grid:
        err("missing 'grid' with integer 'w' and 'h'")
    w, h = grid["w"], grid["h"]
    if not (isinstance(w, int) and isinstance(h, int) and w >= 1 and h >= 1):
        err(f"grid 'w' and 'h' must be integers >= 1 (got w={w!r}, h={h!r})")

    def check_pos(label, value):
        if (not isinstance(value, (list, tuple)) or len(value) != 2
                or not all(isinstance(c, int) for c in value)):
            err(f"{label} must be a [y, x] pair of integers (got {value!r})")
        y, x = value
        if not (1 <= y <= h and 1 <= x <= w):
            err(f"{label} {list(value)} is outside the {w}x{h} grid")
        return (y, x)

    wh = check_pos("warehouse", config.get("warehouse"))
    check_pos("robot_start", config.get("robot_start"))

    # --- pavilions --------------------------------------------------------- #
    pavs = config.get("pavilions")
    if not isinstance(pavs, list) or not pavs:
        err("'pavilions' must be a non-empty list")

    seen_ids: set = set()
    seen_pos: set = set()
    for i, p in enumerate(pavs):
        where = f"pavilion #{i + 1}"
        if not isinstance(p, dict):
            err(f"{where} must be an object")
        pid = p.get("id")
        if not isinstance(pid, str) or not pid:
            err(f"{where} needs a non-empty string 'id'")
        if pid in seen_ids:
            err(f"duplicate pavilion id {pid!r}")
        seen_ids.add(pid)

        ftype = p.get("type")
        if ftype not in FLOWER_COLORS:
            err(f"{pid}: unknown flower type {ftype!r} "
                f"(known: {', '.join(sorted(FLOWER_COLORS))})")

        pos = check_pos(f"{pid} pos", p.get("pos"))
        if pos == wh:
            err(f"{pid} sits on the warehouse cell {list(wh)}")
        if pos in seen_pos:
            err(f"two pavilions share the position {list(pos)}")
        seen_pos.add(pos)

        needs = p.get("needs")
        if not isinstance(needs, dict) or not needs:
            err(f"{pid} needs a non-empty 'needs' object")
        for color, count in needs.items():
            if color not in FLOWER_COLORS[ftype]:
                err(f"{pid}: color {color!r} is not valid for {ftype} "
                    f"(valid: {', '.join(sorted(FLOWER_COLORS[ftype]))})")
            if not (isinstance(count, int) and count >= 1):
                err(f"{pid}: count for {color!r} must be an integer >= 1 (got {count!r})")


def apply_level(config: dict) -> None:
    """Validate ``config`` and overwrite the module's instance globals from it.

    Must be called BEFORE building any engine/UI. Rebuilds the derived globals
    (MAX_LOAD, PAVILION_BY_ID, PAVILION_AT) so everything stays consistent.
    """
    validate_level(config)
    global GRID_W, GRID_H, WAREHOUSE, ROBOT_START, PAVILIONS
    global MAX_LOAD, PAVILION_BY_ID, PAVILION_AT, LEVEL_NAME

    GRID_W = config["grid"]["w"]
    GRID_H = config["grid"]["h"]
    WAREHOUSE = tuple(config["warehouse"])
    ROBOT_START = tuple(config["robot_start"])
    PAVILIONS = tuple(
        PavilionSpec(p["id"], p["type"], tuple(p["pos"]), dict(p["needs"]))
        for p in config["pavilions"]
    )
    MAX_LOAD = max(sum(p.needs.values()) for p in PAVILIONS)
    PAVILION_BY_ID = {p.pid: p for p in PAVILIONS}
    PAVILION_AT = {p.pos: p for p in PAVILIONS}
    LEVEL_NAME = config.get("name", "custom")

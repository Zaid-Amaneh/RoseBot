"""Rule engine (KnowledgeEngine) and all problem rules - pure rule-based (KBS) style.

The search is driven entirely by **rules + conflict resolution**, not by a hand-written
algorithm. The engine's **agenda is the A* frontier**: ``FStrategy`` keeps it ordered by
``f = g + h`` (see strategy.py), so the lowest-f node's rules fire next - best-first
search. The engine's own forward-chaining ``run()`` *is* the search loop; there is no
external loop and no Python closed-set.

Control rules and their salience (higher fires first):

    violation_*          40   remove illegal nodes (guards / self-check)
    move_* / load / unload + goal_reached
                         20   generate successors / recognise the goal
    print_node            1   print a generated state (only when ShowTree exists)
    sol_seed/mark/print  50/40/30  print the solution path (only when ShowSolution exists)

``goal_reached`` sits at the SAME salience as the generation rules on purpose. Salience is
the agenda's primary sort key, so a higher salience would let a goal fire as soon as one is
generated - even a sub-optimal one. At equal salience ``FStrategy`` orders by ``f``, so
``goal_reached`` fires only when the goal node's ``f`` is the minimum on the agenda, i.e.
no cheaper path can remain => the goal is optimal.

Duplicate states are pruned by the ``_best_g`` index (a node is created only if its state
has not already been reached at an equal-or-lower ``g``). With a consistent heuristic this
keeps the node count finite and preserves optimality, so no closed-set fact is needed.

Decisions live in the **LHS** (patterns + ``TEST`` + ``NOT``); rule bodies only declare
successors via small expression-only helpers. State canonicalisation, distance and load
enumeration are pure data utilities in ``domain.py`` (each search state is packed into one
self-contained ``Node`` fact, which is what allows a branching search tree).
"""

import rosebot.compat  # noqa: F401  # must precede experta import

from experta import KnowledgeEngine, DefFacts, Rule, AS, MATCH, TEST, NOT

from rosebot import domain as d
from rosebot.facts import (Config, Pavilion, Node, Solution,
                           ShowTree, TreeShown, ShowSolution, OnPath, Shown)

# Salience tiers (see module docstring).
S_VIOLATION = 40
S_GEN = 20       # generation rules AND goal_reached share this tier (FStrategy breaks ties by f)
S_GOAL = 20


class RoseBotEngine(KnowledgeEngine):
    """Forward-chaining, rule-driven A* search for bouquet delivery.

    The agenda (ordered by FStrategy = f) is the frontier; ``run()`` is the search loop.
    """

    def __init__(self, heuristic=None):
        super().__init__()
        self.heuristic = heuristic  # callable(pos, load, needs) -> int, or None (h = 0)

    # ------------------------------------------------------------------ #
    # Bookkeeping (ids / counters / dedup index; not part of reasoning)   #
    # ------------------------------------------------------------------ #
    def reset(self, **kwargs):
        self._id = 0
        self._count = 0        # nodes created (incl. root) - for reporting only
        # Best-g index (bookkeeping, like the id counter): the lowest g at which each state
        # signature has been reached. It only prevents creating a redundant Node fact for a
        # state already reached at no greater cost. Optimality holds because the heuristic
        # is consistent, so the first time a state is reached is via an optimal path.
        self._best_g = {}
        super().reset(**kwargs)

    def _next_id(self):
        i = self._id
        self._id += 1
        return i

    def _h(self, pos, load, needs):
        return 0 if self.heuristic is None else self.heuristic(pos, load, needs)

    # ------------------------------------------------------------------ #
    # Initial State (Deliverable 1) - assert the KB as facts             #
    # ------------------------------------------------------------------ #
    @DefFacts()
    def _initial_state(self):
        yield Config(grid_w=d.GRID_W, grid_h=d.GRID_H,
                     wh_y=d.WAREHOUSE[0], wh_x=d.WAREHOUSE[1], max_load=d.MAX_LOAD)
        for p in d.PAVILIONS:  # deffacts construction (data), not reasoning
            yield Pavilion(pid=p.pid, ftype=p.ftype, py=p.pos[0], px=p.pos[1],
                           base_needs=tuple(sorted(p.needs.items())))
        needs = d.initial_needs()
        h = self._h(d.ROBOT_START, (), needs)
        self._count = 1
        root_sig = d.state_signature(d.ROBOT_START, (), needs)
        self._best_g[root_sig] = 0
        yield Node(nid=self._next_id(), parent=-1, op="INIT", g=0, h=h, f=h, depth=0,
                   ry=d.ROBOT_START[0], rx=d.ROBOT_START[1], load=(), needs=needs,
                   sig=root_sig, status="open")

    # ------------------------------------------------------------------ #
    # Successor declaration (expression-only helpers, no if/for control) #
    # ------------------------------------------------------------------ #
    def _child(self, parent, op, pos, load, needs):
        load = d.make_load(load)
        needs = d.make_needs(needs)
        g = parent["g"] + 1
        sig = d.state_signature(pos, load, needs)
        # Skip if this state was already reached at an equal or lower cost (see _best_g).
        if self._best_g.get(sig, 1 << 30) <= g:
            return
        self._best_g[sig] = g
        h = self._h(pos, load, needs)
        self._count += 1
        self.declare(Node(nid=self._next_id(), parent=parent["nid"], op=op,
                          g=g, h=h, f=g + h, depth=parent["depth"] + 1,
                          ry=pos[0], rx=pos[1], load=load, needs=needs,
                          sig=sig, status="open"))

    def _spawn_loads(self, parent, pos, needs):
        # Enumerating the legal/useful loads is a data utility; one child per option, then
        # FStrategy orders the resulting nodes by f on the agenda.
        for combo in d.enumerate_loads(needs):
            self._child(parent, f"load {d.fmt_load(combo)}", pos, combo, needs)

    # ------------------------------------------------------------------ #
    # GOAL (Deliverable 4) - same salience as generation; FStrategy makes #
    # it fire only when the goal node's f is the agenda minimum => optimal #
    # ------------------------------------------------------------------ #
    @Rule(AS.n << Node(status="open", load=(), needs=()),
          NOT(Solution()),
          salience=S_GOAL)
    def goal_reached(self, n):
        self.declare(Solution(nid=n["nid"]))

    # ------------------------------------------------------------------ #
    # GENERATE PATH RULES (Deliverable 2) - one rule per operator.        #
    #                                                                     #
    # Each operator is its own production with its legality in the LHS     #
    # (TEST / a Pavilion join), so *which* operator applies is decided by  #
    # pattern matching, not by `if` in a body. One activation per (rule,    #
    # node); experta fires it once, and FStrategy makes the lowest-f node   #
    # fire next (best-first = A*). Nodes are NOT retracted: an activation   #
    # fires once anyway, and the facts must persist for path reconstruction #
    # and tree printing; the frontier is the set of not-yet-fired nodes.    #
    #                                                                     #
    # The move rules carry a not-goal guard so a satisfied goal node is     #
    # handled only by goal_reached. (load_bouquets needs `needs != ()` and  #
    # unload_bouquets needs `load != ()`, so neither can match a goal.)     #
    # ------------------------------------------------------------------ #
    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=MATCH.load, needs=MATCH.needs),
          NOT(Solution()),
          TEST(lambda load, needs: load != () or needs != ()),
          TEST(lambda ry, rx: d.in_grid(ry - 1, rx)),
          salience=S_GEN)
    def move_up(self, n, ry, rx, load, needs):
        self._child(n, "move up", (ry - 1, rx), load, needs)

    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=MATCH.load, needs=MATCH.needs),
          NOT(Solution()),
          TEST(lambda load, needs: load != () or needs != ()),
          TEST(lambda ry, rx: d.in_grid(ry + 1, rx)),
          salience=S_GEN)
    def move_down(self, n, ry, rx, load, needs):
        self._child(n, "move down", (ry + 1, rx), load, needs)

    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=MATCH.load, needs=MATCH.needs),
          NOT(Solution()),
          TEST(lambda load, needs: load != () or needs != ()),
          TEST(lambda ry, rx: d.in_grid(ry, rx - 1)),
          salience=S_GEN)
    def move_left(self, n, ry, rx, load, needs):
        self._child(n, "move left", (ry, rx - 1), load, needs)

    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=MATCH.load, needs=MATCH.needs),
          NOT(Solution()),
          TEST(lambda load, needs: load != () or needs != ()),
          TEST(lambda ry, rx: d.in_grid(ry, rx + 1)),
          salience=S_GEN)
    def move_right(self, n, ry, rx, load, needs):
        self._child(n, "move right", (ry, rx + 1), load, needs)

    # load: only at the warehouse, only when empty, only useful legal loads.
    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=(), needs=MATCH.needs),
          NOT(Solution()),
          TEST(lambda ry, rx: (ry, rx) == d.WAREHOUSE),
          TEST(lambda needs: needs != ()),
          salience=S_GEN)
    def load_bouquets(self, n, ry, rx, needs):
        self._spawn_loads(n, (ry, rx), needs)

    # unload: only on a pavilion cell (the Pavilion join binds the cell + pid) and only when
    # the carried load has colors that pavilion still needs.
    @Rule(AS.n << Node(status="open", ry=MATCH.ry, rx=MATCH.rx,
                       load=MATCH.load, needs=MATCH.needs),
          Pavilion(py=MATCH.ry, px=MATCH.rx, pid=MATCH.pid),
          NOT(Solution()),
          TEST(lambda load: load != ()),
          TEST(lambda load, needs, pid:
               bool(d.unloadable(load, d.PAVILION_BY_ID[pid], needs))),
          salience=S_GEN)
    def unload_bouquets(self, n, ry, rx, load, needs, pid):
        pav = d.PAVILION_BY_ID[pid]
        drops = d.unloadable(load, pav, needs)
        self._child(n, f"unload {d.fmt_drops(pid, drops)}", (ry, rx),
                    d.apply_unload(load, pav, drops),
                    d.reduce_needs(needs, pid, drops))

    # ------------------------------------------------------------------ #
    # CONSTRAINT VIOLATION RULES (Deliverable 3) - guards + self-check.   #
    # Generation is correct-by-construction, so these normally fire on    #
    # nothing; if a guard regressed they retract the offending node.      #
    # ------------------------------------------------------------------ #
    def _violation(self, n, reason):
        print(f"[VIOLATION] node {n['nid']} ({n['op']}): {reason} -> removed")
        self.retract(n)

    @Rule(AS.n << Node(ry=MATCH.ry, rx=MATCH.rx),
          TEST(lambda ry, rx: not d.in_grid(ry, rx)),
          salience=S_VIOLATION)
    def violate_off_grid(self, n, ry, rx):
        self._violation(n, f"off-grid position ({ry},{rx})")

    @Rule(AS.n << Node(load=MATCH.load),
          TEST(lambda load: not d.within_max_load(load)),
          salience=S_VIOLATION)
    def violate_over_max_load(self, n, load):
        self._violation(n, f"load exceeds MAX_LOAD ({d.total_count(load)} > {d.MAX_LOAD})")

    @Rule(AS.n << Node(load=MATCH.load),
          TEST(lambda load: not d.is_legal_load(load)),
          salience=S_VIOLATION)
    def violate_illegal_load(self, n, load):
        self._violation(n, "illegal load (mixes different types AND colors)")

    @Rule(AS.n << Node(load=MATCH.load),
          TEST(lambda load: not d.load_is_valid_bouquets(load)),
          salience=S_VIOLATION)
    def violate_wrong_unload(self, n, load):
        self._violation(n, "invalid bouquet (color not valid for its flower type)")

    # ------------------------------------------------------------------ #
    # PRINTING (Deliverables 4 & 5) - recursive rules, not Python loops.  #
    # Active only when a ShowTree / ShowSolution trigger fact exists.     #
    # ------------------------------------------------------------------ #
    # Print every generated state (search tree). Marks each node TreeShown so it prints once.
    @Rule(ShowTree(),
          AS.n << Node(nid=MATCH.id),
          NOT(TreeShown(nid=MATCH.id)),
          salience=1)
    def print_node(self, n, id):
        indent = "  " * n["depth"]
        print(f"{indent}[{id}] <- {n['parent']}  {n['op']:<30} "
              f"g={n['g']} h={n['h']} f={n['f']} pos=({n['ry']},{n['rx']}) "
              f"load=[{d.fmt_load(n['load'])}] needs_left={d.remaining_total(n['needs'])}")
        self.declare(TreeShown(nid=id))

    # Seed the solution path from the goal node, and print the header.
    @Rule(ShowSolution(),
          Solution(nid=MATCH.gid),
          Node(nid=MATCH.gid, g=MATCH.cost),
          NOT(OnPath(nid=MATCH.gid)),
          salience=50)
    def sol_seed(self, gid, cost):
        print(f"\n=== Solution (total cost = {cost}) ===")
        self.declare(OnPath(nid=gid))
        self.declare(Shown(nid=-1))  # sentinel: the root's parent is "already shown"

    # Walk parent links upward, marking each node on the path (recursion via chaining).
    @Rule(OnPath(nid=MATCH.c),
          Node(nid=MATCH.c, parent=MATCH.p),
          TEST(lambda p: p != -1),
          NOT(OnPath(nid=MATCH.p)),
          salience=40)
    def sol_mark(self, c, p):
        self.declare(OnPath(nid=p))

    # Print path nodes in root -> goal order (a node prints once its parent has printed).
    @Rule(Shown(nid=MATCH.p),
          OnPath(nid=MATCH.c),
          Node(nid=MATCH.c, parent=MATCH.p, op=MATCH.op, g=MATCH.g),
          NOT(Shown(nid=MATCH.c)),
          salience=30)
    def sol_print(self, p, c, op, g):
        print(f"  {g:>2}. {op:<34} (cost so far g={g})")
        self.declare(Shown(nid=c))

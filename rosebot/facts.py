"""Fact definitions for experta's working memory.

All nested values are immutable (tuples) so experta can match and dedup them.
See docs/APPROACH.md section 2.
"""

import rosebot.compat  # noqa: F401  # must precede experta import

from experta import Fact, Field


class Config(Fact):
    """Static problem configuration (declared once)."""

    grid_w = Field(int, mandatory=True)
    grid_h = Field(int, mandatory=True)
    wh_y = Field(int, mandatory=True)   # warehouse row
    wh_x = Field(int, mandatory=True)   # warehouse column
    max_load = Field(int, mandatory=True)


class Pavilion(Fact):
    """Static reference data for one pavilion."""

    pid = Field(str, mandatory=True)          # "P1".."P4"
    ftype = Field(str, mandatory=True)        # flower type
    py = Field(int, mandatory=True)           # row
    px = Field(int, mandatory=True)           # column
    base_needs = Field(tuple, mandatory=True)  # ((color, count), ...)


class Node(Fact):
    """A search-tree node — fully describes one state.

    ``load``  : sorted tuple of (ftype, color, count); () = empty.
    ``needs`` : sorted tuple of (pid, color, count) for remaining needs only.
    ``sig``   : hashable canonical state signature (for dedup).
    ``status``: "open" — every node is on the frontier until its generation
                rules fire (each generation activation fires once, so a node is
                expanded exactly once; see the move_*/load/unload rules).
    """

    nid = Field(int, mandatory=True)
    parent = Field(int, mandatory=True)   # parent nid; -1 for the root
    op = Field(str, mandatory=True)       # operation that produced this node
    g = Field(int, mandatory=True)        # cost so far (ops)
    h = Field(int, mandatory=True)        # heuristic estimate
    f = Field(int, mandatory=True)        # g + h
    depth = Field(int, mandatory=True)    # tree depth (for indentation)
    ry = Field(int, mandatory=True)       # robot row
    rx = Field(int, mandatory=True)       # robot column
    load = Field(tuple, mandatory=True)
    needs = Field(tuple, mandatory=True)
    sig = Field(tuple, mandatory=True)   # the signature to detect similarity
    status = Field(str, default="open")


class Solution(Fact):
    """Declared by the goal rule when a goal node is found."""

    nid = Field(int, mandatory=True)


# --- printing (Deliverables 4 & 5), done with rules instead of Python loops --- #
class ShowTree(Fact):
    """Trigger: print every generated state (search tree)."""


class TreeShown(Fact):
    """Marker: this node has already been printed in the tree."""

    nid = Field(int, mandatory=True)


class ShowSolution(Fact):
    """Trigger: print the solution path."""


class OnPath(Fact):
    """A node that lies on the solution path (root -> goal)."""

    nid = Field(int, mandatory=True)


class Shown(Fact):
    """Marker: this path node has already been printed."""

    nid = Field(int, mandatory=True)



import rosebot.compat  # noqa: F401  # must precede experta import

from experta import Fact, Field


class Config(Fact):

    grid_w = Field(int, mandatory=True)
    grid_h = Field(int, mandatory=True)
    wh_y = Field(int, mandatory=True)   # warehouse row
    wh_x = Field(int, mandatory=True)   # warehouse column
    max_load = Field(int, mandatory=True)


class Pavilion(Fact):

    pid = Field(str, mandatory=True)          # "P1".."P4"
    ftype = Field(str, mandatory=True)        # flower type
    py = Field(int, mandatory=True)           # row
    px = Field(int, mandatory=True)           # column
    base_needs = Field(tuple, mandatory=True)  # ((color, count), ...)


class Node(Fact):

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

    nid = Field(int, mandatory=True)


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

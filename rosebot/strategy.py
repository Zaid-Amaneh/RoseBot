"""Custom experta conflict-resolution Strategy for A* (Deliverable 6).

``FStrategy`` orders the agenda by each activation's matched-node ``f = g + h`` so the
engine expands the lowest-f node next (best-first search = A*). This is the literal
"priority/salience" realization of A* requested by the assignment: instead of a static
salience, activations are ranked by the dynamic cost ``f`` of the node they match.

Implementation: experta keeps the agenda sorted by ``activation.key`` and runs the
**rightmost** (highest key) activation next (see ``experta.agenda.Agenda.get_next``).
``DepthStrategy`` builds that key from ``get_key``; we override only ``get_key`` to
return ``(salience, -f, factids)`` so the highest-priority / lowest-``f`` activation is
the one that runs next. Everything else (incremental, sorted insertion) is inherited.
"""

from experta.strategies import DepthStrategy

from rosebot.facts import Node


class FStrategy(DepthStrategy):
    """Best-first (A*) conflict resolution: lowest f = g + h runs next."""

    @staticmethod
    def _node_f(activation):
        """f = g + h of the Node this activation matched (0 if it matches none)."""
        for fact in activation.facts:
            if isinstance(fact, Node):
                return fact["f"]
        return 0

    def get_key(self, activation):
        salience = activation.rule.salience
        factids = sorted((f["__factid__"] for f in activation.facts), reverse=True)
        # Agenda runs the highest key first => higher salience, then LOWER f (so -f),
        # then most-recent facts (DepthStrategy's recency tie-break).
        return (salience, -self._node_f(activation), factids)

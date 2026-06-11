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

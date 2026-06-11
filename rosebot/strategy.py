from experta.strategies import DepthStrategy

from rosebot.facts import Node


class FStrategy(DepthStrategy):

    @staticmethod
    def _node_f(activation):
        for fact in activation.facts:
            if isinstance(fact, Node):
                return fact["f"]
        return 0

    def get_key(self, activation):
        salience = activation.rule.salience
        factids = sorted((f["__factid__"] for f in activation.facts), reverse=True)
        return (salience, -self._node_f(activation), factids)

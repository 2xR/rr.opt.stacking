from __future__ import unicode_literals
from past.builtins import basestring
from opt.treesearch.mcts import MCTS
from opt.solver.params import Parameter

from stacking.solvers.treenode import SP_TreeNode
from stacking.instance import Instance


class SP_MCTS(MCTS):
    @Parameter(name="remarshal",
               description="control whether remarshaling moves are included in the search tree",
               domain=(True, False),
               default=False)
    def remarshal(self):
        return self.do_remarshal

    @remarshal.setter
    def remarshal(self, enabled):
        self.do_remarshal = enabled

    @remarshal.adapter
    def remarshal(self, enabled):
        if isinstance(enabled, basestring):
            original = enabled
            enabled = enabled.lower().strip()
            if enabled in ("t", "true", "1"):
                return True
            elif enabled in ("f", "false", "0"):
                return False
            else:
                raise ValueError("invalid value for remarshal parameter: {}".format(original))
        else:
            return bool(enabled)

    version = "1.0a"
    default_root_fnc = SP_TreeNode.root
    instance_loader = staticmethod(Instance.load)
    params = MCTS.params + [remarshal]


mcts = SP_MCTS()
if __name__ == "__main__":
    exit(mcts.cli())

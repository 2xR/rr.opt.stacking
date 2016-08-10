from __future__ import unicode_literals
import sys

from rr.opt.stacking.instance import Instance
from rr.opt.stacking.solvers.treenode import SP_TreeNode
from rr.opt.stacking.solvers.mcts import SP_MCTS


instance_file = sys.argv[1] if len(sys.argv) > 1 else "instances/20-A.txt"
i = Instance.load(instance_file)

mcts = SP_MCTS()
mcts.init(i)

r = SP_TreeNode.root(mcts)
n = r.copy()
# n.semi_greedy_complete()
# print n.warehouse


def slots(x):
    return {s: getattr(x, s) for s in type(x).__slots__}

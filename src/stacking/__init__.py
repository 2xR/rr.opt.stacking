from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .instance import Instance, Item, Store, RELEASE, DELIVERY
from .solution import Solution
from .mcts import TreeNode


# --------------------------------------------------------------------------------------------------
from rr.opt.mcts import basic as mcts


def solve(instance="../instances/10-A.txt", niter=10):
    if isinstance(instance, str):
        instance = Instance.load(instance)
    root = TreeNode.root(instance)
    return mcts.run(root, iter_limit=niter)

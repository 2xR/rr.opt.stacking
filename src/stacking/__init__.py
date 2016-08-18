from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from .instance import Instance, Item, Store, RELEASE, DELIVERY
from .solution import Solution
from .mcts import TreeNode


# --------------------------------------------------------------------------------------------------
from rr.opt.mcts import basic as mcts


mcts.config_logging()


def solve(instance, **kwargs):
    if not isinstance(instance, Instance):
        instance = Instance.load(instance)
    root = TreeNode.root(instance)
    return mcts.run(root, **kwargs)


def main(time_limit=60):
    results = {}
    instances_dir = Path(__file__).parent.joinpath("../../instances").resolve()
    print(instances_dir)
    for instance in instances_dir.glob("*.txt"):
        print("_" * 100)
        print("Solving {}...".format(instance))
        results[instance.name] = solve(instance, time_limit=time_limit)
    return results

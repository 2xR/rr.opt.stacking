from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import rr.opt.mcts.basic as mcts

from ..instance import Instance
from .treenode import TreeNode


def solve(instance, **kwargs):
    if kwargs.pop("config_logging", False):
        mcts.config_logging()
    if not isinstance(instance, Instance):
        instance = Instance.load(instance)
    root = TreeNode.root(instance)
    return mcts.run(root, **kwargs)


def main(time_limit=60):
    results = {}
    instances_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        *(([os.path.pardir] * 5) + ["instances"]),
    ))
    mcts.config_logging()
    mcts.logger.info("Solving instances from {}".format(instances_dir))
    for instance in os.listdir(instances_dir):
        if instance.endswith(".txt"):
            mcts.logger.info("_" * 100)
            mcts.logger.info("Solving {}...".format(instance))
            instance_path = os.path.join(instances_dir, instance)
            results[instance] = solve(instance_path, time_limit=time_limit)
    return results

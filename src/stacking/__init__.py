from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random

from .instance import Instance, Item, Store, RELEASE
from .solution import Solution
from .mcts import TreeNode


s = Store(10, 10)
r = Solution()
r.record_from(s)

i = []
for x in range(20):
    rel = random.randint(0, 100)
    due = rel + random.randint(10, 100)
    i.append(Item(x, rel, due))


def random_move(store, items):
    item = random.choice(items)
    source = store.location(item)
    if source is not RELEASE:
        item = source.top
    candidates = store.nonequivalent_stacks()
    target = source
    while target is source:
        target = random.choice(candidates)
    return store.move(item, target)


mv = lambda n=1: [random_move(s, i) for _ in range(n)]


instance = Instance.load("../instances/10-A.txt")

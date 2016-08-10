from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .item import Item
from .stack import Stack, RELEASE, DELIVERY
from .store import Store
from .instance import Instance

import random


s = Store.Recording(10, 10)
i = []
for x in range(20):
    r = random.randint(0, 100)
    d = r + random.randint(10, 100)
    i.append(Item(x, r, d))


def random_move(store, items):
    item = random.choice(items)
    source = store.location(item)
    if source is not Stack.RELEASE:
        item = source.top
    return store.move(item, random.choice(store.nonequivalent_stacks()))


mv = lambda n=1: [random_move(s, i) for _ in range(n)]

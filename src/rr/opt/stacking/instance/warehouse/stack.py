from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import zip

from rr import pretty


INF = float("inf")


@pretty.klass
class Stack(object):
    def __init__(self, id):
        self.id = id
        self.items = []
        self.earliest = [INF]
        self.due = INF

    def __info__(self):
        items = " ".join("i{}".format(item.id) for item in self.items)
        return "{} [due={:<10}] <{}>".format(self.id, self.due, items)

    def copy(self):
        clone = type(self)(self.id)
        clone.items = list(self.items)
        clone.earliest = list(self.earliest)
        clone.due = self.due
        return clone

    @property
    def top(self):
        return self.items[-1]

    def append(self, item):
        inversions_delta = 0
        if len(self.items) == 0:
            self.earliest.append(item.due)
            self.due = item.due
        else:
            if item.due > self.due:
                inversions_delta = +1
                self.earliest.append(self.due)
            else:
                self.earliest.append(item.due)
                self.due = item.due
        self.items.append(item)
        return inversions_delta

    def pop(self):
        item = self.items.pop()
        self.earliest.pop()
        self.due = self.earliest[-1]
        inversions_delta = 0 if self.due >= item.due else -1
        return inversions_delta, item

    def depth(self, item):
        items = self.items
        return len(items) - 1 - items.index(item)

    def equivalent_to(self, stack):
        return (
            self.due == stack.due and
            len(self.items) == len(stack.items) and
            all(i.due == j.due for i, j in zip(self.items, stack.items))
        )


class DummyStack(object):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.id)


RELEASE = DummyStack("R")
DELIVERY = DummyStack("D")

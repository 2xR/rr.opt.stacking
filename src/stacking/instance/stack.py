from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object, zip


INF = float("inf")


class Stack(object):
    def __init__(self, id, max_height=INF):
        self.id = id  # stack identifier (index in store)
        self.max_height = max_height  # maximum number of items allowed
        self.items = []  # items in the stack (bottom-up)
        self.earliest = [INF]  # earliest due date stack
        self.inversions = 0  # number of due date inversions

    def __repr__(self):
        items = " ".join("i{}".format(item.id) for item in self.items)
        return "{}#{:<3} due={:<6} inv={:<6} <{}>".format(
            type(self).__name__, self.id, self.due, self.inversions, items)

    def copy(self):
        cls = type(self)
        clone = cls.__new__(cls)
        clone.id = self.id
        clone.max_height = self.max_height
        clone.items = list(self.items)
        clone.earliest = list(self.earliest)
        clone.inversions = self.inversions
        return clone

    @property
    def empty(self):
        return len(self.items) == 0

    @property
    def full(self):
        return len(self.items) >= self.max_height

    @property
    def top(self):
        """Item at the top of the stack."""
        return self.items[-1]

    @property
    def due(self):
        """Earliest due date of items currently in the stack."""
        return self.earliest[-1]

    def push(self, item):
        """Add an item to the top of the stack."""
        if self.full:
            raise Exception("stack is full, cannot add item")
        if len(self.items) == 0:
            self.earliest.append(item.due)
        else:
            stack_due = self.due
            if stack_due < item.due:
                self.inversions += 1
                self.earliest.append(stack_due)
            else:
                self.earliest.append(item.due)
        self.items.append(item)

    def pop(self):
        """Remove the top item from the stack."""
        item = self.items.pop()
        self.earliest.pop()
        if self.due < item.due:
            self.inversions -= 1
        return item

    def depth(self, item):
        """Number of items in the stack which are above the argument ``item``."""
        items = self.items
        return len(items) - 1 - items.index(item)

    def equivalent_to(self, stack):
        """Check if two stacks are equivalent.

        Two stacks are equivalent if they have the same number of items with the same due dates (
        release dates are irrelevant here) and in the same order. In the context of the SP, placing
        an item in any stack of a group of equivalent stacks results in the same solution, thereby
        we can consider only one candidate stack per equivalence group.

        Returns:
            bool: True iff the stacks are equivalent.
        """
        return (
            len(self.items) == len(stack.items) and
            all(i.due == j.due for i, j in zip(self.items, stack.items))
        )


class PseudoStack(Stack):
    """This Stack subclass is used only to represent the special stacks 'Release' and 'Delivery'."""
    def __init__(self, id, name):
        Stack.__init__(self, id)
        self.name = name

    def __repr__(self):
        return "{}#{} ({})".format(type(self).__name__, self.id, self.name)

    def copy(self):
        return self

    def push(self, item):
        raise RuntimeError("invalid method on pseudo-stack {}: push()".format(self.name))

    def pop(self):
        raise RuntimeError("invalid method on pseudo-stack {}: pop()".format(self.name))

    def depth(self, item):
        raise RuntimeError("invalid method on pseudo-stack {}: depth()".format(self.name))

    def equivalent_to(self, stack):
        raise RuntimeError("invalid method on pseudo-stack {}: equivalent_to()".format(self.name))


Stack.Pseudo = PseudoStack
Stack.RELEASE = RELEASE = PseudoStack(0, "R")
Stack.DELIVERY = DELIVERY = PseudoStack(-1, "D")

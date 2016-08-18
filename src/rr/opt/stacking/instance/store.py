from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object, map, range

from rr.opt.stacking import utils

from .stack import Stack, RELEASE, DELIVERY


INF = float("inf")


class Store(object):
    """A store simply represents a set of stacks together with 'release' and 'delivery'
    pseudo-stacks. This class provides a method to enumerate non-equivalent stacks in the store
    and build a list of stack groups, where a stack group is a set of equivalent stacks.
    """
    def __init__(self, nstacks, max_height=INF):
        self.stacks = [RELEASE]
        for i in range(1, nstacks+1):
            self.stacks.append(Stack(i, max_height=max_height))
        self.stacks.append(DELIVERY)
        self.loc_map = {}  # item location map :: {item: stack_index}
        self.move_callbacks = []  # :: [callable(store, item, source, target)]

    def __repr__(self):
        return "<{} \n\t{}\n@{:x}>".format(
            type(self).__name__,
            "\n\t".join(map(repr, self.stacks)),
            id(self),
        )

    def copy(self, clear_move_callbacks=True):
        cls = type(self)
        clone = cls.__new__(cls)
        clone.stacks = [stack.copy() for stack in self.stacks]
        clone.loc_map = dict(self.loc_map)
        if clear_move_callbacks:
            clone.move_callbacks = []
        else:
            clone.move_callbacks = list(self.move_callbacks)
        return clone

    @property
    def inversions(self):
        return sum(stack.inversions for stack in self.stacks)

    def inner_stacks(self):
        stacks = self.stacks
        for i in range(1, len(stacks)-1):
            yield stacks[i]

    def nonequivalent_stacks(self):
        return utils.nonequivalent_stacks(self.inner_stacks())

    def stack_groups(self):
        return utils.stack_groups(self.inner_stacks())

    def location(self, item):
        """Retrieve the stack where an item currently is located.

        Note:
            If the item has not yet been added to the store, it is considered to be in the
            RELEASE pseudo-stack.
        """
        stack_index = self.loc_map.get(item, 0)
        return self.stacks[stack_index]

    def depth(self, item):
        """See Stack.depth()."""
        return self.location(item).depth(item)

    def move(self, item, target):
        """Put `item` onto the `target` stack.

        The item is first `pop()`ed from its current location (*must* be the top item or not yet
        released), and then `push()`ed onto the target stack (or delivery).

        Returns:
            Stack: the item's previous location."""
        if isinstance(target, int):
            target = self.stacks[target]
        source = self.location(item)
        assert source is not target
        assert not target.full
        if source is not RELEASE:
            assert item is source.top
            source.pop()
        if target is not DELIVERY:
            target.push(item)
        self.loc_map[item] = target.id
        for callback in self.move_callbacks:
            callback(self, item, source, target)
        return source

    def register_move_callback(self, fnc):
        """Register `fnc` to be executed when this `store.move()` is called.

        The callback function is given four arguments: the store, item, source stack, and target
        stack. Its return value is ignored.
        """
        self.move_callbacks.append(fnc)
        return fnc

    def clear_move_callbacks(self):
        del self.move_callbacks[:]

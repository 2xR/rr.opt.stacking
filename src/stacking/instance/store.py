from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object, map, range

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

    def __repr__(self):
        return "<{} \n\t{}\n@{:x}>".format(
            type(self).__name__,
            "\n\t".join(map(repr, self.stacks)),
            id(self),
        )

    def copy(self):
        cls = type(self)
        clone = cls.__new__(cls)
        clone.stacks = [stack.copy() for stack in self.stacks]
        clone.loc_map = dict(self.loc_map)
        return clone

    @property
    def inversions(self):
        return sum(stack.inversions for stack in self.stacks)

    def inner_stacks(self):
        stacks = self.stacks
        for i in range(1, len(stacks)-1):
            yield stacks[i]

    def nonequivalent_stacks(self):
        nonequivalent = []
        for stack in self.inner_stacks():
            if not any(stack.equivalent_to(s) for s in nonequivalent):
                nonequivalent.append(stack)
        return nonequivalent

    def stack_groups(self):
        groups = []
        for stack in self.inner_stacks():
            for group in groups:
                if stack.equivalent_to(group[0]):
                    group.append(stack)
                    break
            else:
                groups.append([stack])
        return groups

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
        source = self.location(item)
        assert not target.full
        if source is not RELEASE:
            assert item is source.top
            source.pop()
        if target is not DELIVERY:
            target.push(item)
        self.loc_map[item] = target.id
        return source


class RecordingStore(Store):
    """A Store subclass which keeps a record of all moves it makes and counts relocations."""
    def __init__(self, *args, **kwargs):
        Store.__init__(self, *args, **kwargs)
        self.moves = []
        self.relocations = 0

    def copy(self):
        clone = Store.copy(self)
        clone.moves = list(self.moves)
        clone.relocations = self.relocations
        return clone

    def move(self, item, target):
        source = Store.move(self, item, target)
        self.moves.append("i{}: s{} -> s{}".format(
            item.id,
            "R" if source is RELEASE else source.id,
            "D" if target is DELIVERY else target.id,
        ))
        if source is not RELEASE and target is not DELIVERY:
            self.relocations += 1
        return source


Store.Recording = RecordingStore

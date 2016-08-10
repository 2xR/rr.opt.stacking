from __future__ import unicode_literals
from builtins import range
from builtins import object
from utils.prettyrepr import prettify_class

from stacking.instance.warehouse.stack import Stack, RELEASE, DELIVERY


@prettify_class
class Warehouse(object):
    def __init__(self, nstacks):
        self.item_map = None
        self.item_location = ItemLocator(self)
        self.location_map = {RELEASE.id: RELEASE, DELIVERY.id: DELIVERY}
        self.stacks = []
        for x in range(1, nstacks+1):
            stack = Stack(x)
            self.stacks.append(stack)
            self.location_map[stack.id] = stack
        self.inversions = 0
        self.relocations = 0

    def __info__(self):
        lines = ["inv=%d, reloc=%d" % (self.inversions, self.relocations)]
        lines.extend("\t%s" % (s,) for s in sorted(self.stacks, key=lambda s: s.id))
        lines.append("")
        return "\n".join(lines)

    def __getitem__(self, key):
        return self.location_map[key]

    def set_items(self, items):
        self.item_map = {item.id: item for item in items}
        for item in items:
            self.item_location[item] = RELEASE

    def depth(self, item):
        return self.item_location[item].depth(item)

    def move(self, item, target):
        source = self.item_location[item]
        if source is not RELEASE:
            inversions_delta, top = source.pop()
            assert top is item
            self.inversions += inversions_delta
        if target is not DELIVERY:
            inversions_delta = target.append(item)
            self.inversions += inversions_delta
        if source is not RELEASE and target is not DELIVERY:
            self.relocations += 1
        self.item_location[item] = target
        return source

    def stack_groups(self):
        """Create a list of stack groups, where equivalent stacks are placed in the same group."""
        stack_groups = []
        for stack in self.stacks:
            create_new_group = True
            for group in stack_groups:
                if stack.equivalent_to(group[0]):
                    group.append(stack)
                    create_new_group = False
                    break
            if create_new_group:
                stack_groups.append([stack])
        return stack_groups

    def copy(self):
        """Create a copy of the warehouse in its current state."""
        clone = type(self)(0)
        clone.item_map = self.item_map
        clone.item_location.update(self.item_location)
        for stack in self.stacks:
            stack = stack.copy()
            clone.stacks.append(stack)
            clone.location_map[stack.id] = stack
        clone.inversions = self.inversions
        clone.relocations = self.relocations
        return clone


class ItemLocator(dict):
    """Associates item ids to the ids of the items' current locations."""
    __slots__ = ("warehouse",)

    def __init__(self, warehouse):
        dict.__init__(self)
        self.warehouse = warehouse

    def __getitem__(self, item):
        loc_id = dict.__getitem__(self, item)
        return self.warehouse.location_map[loc_id]

    def __setitem__(self, item, loc):
        # print item, "-->", loc.id
        # if loc is RELEASE:
        #     assert item not in self
        # else:
        #     assert self[item] is not DELIVERY
        #     if self[item] is RELEASE:
        #         assert loc not in (RELEASE, DELIVERY)
        dict.__setitem__(self, item, loc.id)

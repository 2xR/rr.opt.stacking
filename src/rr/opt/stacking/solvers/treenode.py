from __future__ import unicode_literals
from opt.treesearch import TreeNode
from utils.misc import INF

from stacking.instance.warehouse.stack import RELEASE, DELIVERY
from stacking.solvers.heuristics import FO


class SP_TreeNode(TreeNode):
    __slots__ = ("solver", "cursor", "warehouse", "actions")

    @classmethod
    def root(cls, solver):
        solver.lower_bound = 0
        root = cls()
        root.solver = solver
        root.cursor = solver.instance.calendar.cursor()
        root.warehouse = solver.instance.warehouse.copy()
        root.actions = []
        root.flush_stacks(root.warehouse.stacks)
        return root

    def copy(self):
        clone = type(self)()
        clone.solver = self.solver
        clone.cursor = self.cursor.copy()
        clone.warehouse = self.warehouse.copy()
        clone.actions = list(self.actions)
        return clone

    def branches(self):
        # Stop branching as soon as we know it is not worth it
        warehouse = self.warehouse
        if warehouse.relocations + warehouse.inversions >= self.solver.upper_bound:
            return ()
        stack_groups = warehouse.stack_groups()
        cursor = self.cursor
        actions = []
        # Deliveries
        for item in cursor.deliveries:
            src = warehouse.item_location[item]
            if src.top is item:
                actions.append((item, DELIVERY.id))
        # Relocations
        if self.solver.do_remarshal:
            self._remarshaling(stack_groups, actions)
        elif len(cursor.deliveries) > 0:
            self._reshuffling(stack_groups, actions)
        # Releases
        for item in cursor.releases:
            actions.extend((item, group[0].id) for group in stack_groups)
        return actions

    def _remarshaling(self, stack_groups, actions):
        for src_group in stack_groups:
            src_items = src_group[0].items
            if len(src_items) > 0:
                item = src_items[-1]
                for tgt_group in stack_groups:
                    if src_group is not tgt_group:
                        actions.append((item, tgt_group[0].id))
                    elif len(tgt_group) > 1:
                        actions.append((item, tgt_group[1].id))

    def _reshuffling(self, stack_groups, actions):
        deliveries_unaccounted_for = len(self.cursor.deliveries)
        delivery_stacks = []
        current_time = self.cursor.timestamp
        for stack in self.warehouse.stacks:
            if stack.due == current_time:
                if not any(stack.equivalent_to(s) for s in delivery_stacks):
                    delivery_stacks.append(stack)
                deliveries_unaccounted_for -= sum(1 for i in stack.items if i.due == current_time)
                if deliveries_unaccounted_for == 0:
                    break
        assert deliveries_unaccounted_for == 0
        for src in delivery_stacks:
            item = src.items[-1]
            assert item.due > current_time
            for tgt_group in stack_groups:
                tgt = tgt_group[0]
                if src is not tgt:
                    actions.append((item, tgt.id))
                elif len(tgt_group) > 1:
                    actions.append((item, tgt_group[1].id))

    def apply(self, xxx_todo_changeme):
        (item, tgt_id) = xxx_todo_changeme
        cursor = self.cursor
        index = cursor.index
        src = self.move_item(item, tgt_id)
        if src is not RELEASE:
            self.flush_stacks([src])
        while cursor.index > index and not cursor.is_finished():
            index = cursor.index
            self.flush_stacks(self.warehouse.stacks)

    def is_leaf(self):
        return self.cursor.is_finished()

    def objective(self):
        w = self.warehouse
        return w.relocations + w.inversions

    def lower_bound(self):
        w = self.warehouse
        return w.relocations + w.inversions

    # --------------------------------------------------------------------------
    def flush_stacks(self, stacks):
        """"Deliver items at the top of any stack in 'stacks' whose delivery is in the current
        instant (in the cursor object)."""
        deliveries = self.cursor.deliveries
        if len(deliveries) > 0:
            for stack in stacks:
                while len(stack.items) > 0:
                    item = stack.items[-1]
                    if item not in deliveries:
                        break
                    self.move_item(item, DELIVERY.id)

    def move_item(self, item, tgt_id):
        warehouse = self.warehouse
        tgt = warehouse.location_map[tgt_id]
        src = warehouse.move(item, tgt)
        cursor = self.cursor
        timestamp = cursor.timestamp  # retrieve timestamp before cursor is automatically advanced
        if src is RELEASE:
            cursor.released_item(item)
        elif tgt is DELIVERY:
            cursor.delivered_item(item)
        self.actions.append((timestamp, item.id, src.id, tgt_id))
        return src

    def deliver_item(self, item):
        warehouse = self.warehouse
        src = warehouse.item_location[item]
        top = src.items[-1]
        if top is item:
            self.move_item(item, DELIVERY.id)
            return
        rng = self.solver.rng
        while top is not item:
            assert top.due > item.due
            options = self.placement_choices(avoid=src)
            tgt = FO(top, options, rng) if len(options) > 1 else options[0]
            self.move_item(top, tgt.id)
            top = src.items[-1]
        self.move_item(item, DELIVERY.id)

    def semi_greedy_complete(self, cut=INF):
        warehouse = self.warehouse
        rng = self.solver.rng
        cursor = self.cursor
        release_sort_key = lambda i: (-i.due, i.id)
        delivery_sort_key = lambda i: (warehouse.depth(i), i.id)
        while not cursor.is_finished():
            # lists of releases and deliveries must be computed before doing anything else
            # because the cursor automatically advances to the next instant when all events
            # have been processed.
            releases = sorted(cursor.releases, key=release_sort_key)
            deliveries = sorted(cursor.deliveries, key=delivery_sort_key)
            # Process deliveries
            for item in deliveries:
                self.deliver_item(item)
                # Stop the simulation if we've hit the cut value
                if warehouse.relocations + warehouse.inversions >= cut:
                    warehouse.relocations = INF
                    return
            # Process releases
            for item in releases:
                options = self.placement_choices()
                stack = FO(item, options, rng) if len(options) > 1 else options[0]
                self.move_item(item, stack.id)

    def simulation(self):
        leaf = self.copy()
        leaf.semi_greedy_complete()
        return leaf

    def placement_choices(self, avoid=None):
        choices = []
        for group in self.warehouse.stack_groups():
            if group[0] is not avoid:
                choices.append(group[0])
            elif len(group) > 1:
                choices.append(group[1])
        return choices

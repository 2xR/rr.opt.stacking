from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from rr.opt.mcts import basic as mcts

from stacking.instance import RELEASE, DELIVERY

from . import heuristics


class TreeNode(mcts.TreeNode):
    @classmethod
    def root(cls, instance):
        root = cls()
        root.unreleased_items = len(instance.items)
        root.cursor = instance.calendar.cursor()
        root.store = instance.store.copy()
        root.actions = []
        root.flush_stacks(root.store.inner_stacks())
        return root

    def copy(self):
        clone = mcts.TreeNode.copy(self)
        clone.cursor = self.cursor.copy()
        clone.store = self.store.copy()
        clone.actions = list(self.actions)
        return clone

    def branches(self):
        store = self.store
        cursor = self.cursor
        # Detect whether this node is a leaf. A node is a leaf when all releases have been
        # processed and there are no inversions in the store, so we are guaranteed to not have
        # further item relocations.
        if self.unreleased_items == 0 and store.inversions == 0:
            return ()

        stack_groups = store.stack_groups()
        actions = []
        # Deliveries
        for item in cursor.pending_deliveries:
            src = store.item_location[item]
            if src.top is item:
                actions.append((item, DELIVERY.id))
        # Relocations
        if self.solver.do_remarshal:
            self._remarshalling(stack_groups, actions)
        elif len(cursor.pending_deliveries) > 0:
            self._reshuffling(stack_groups, actions)
        # Releases
        for item in cursor.pending_releases:
            actions.extend((item, group[0].id) for group in stack_groups)
        return actions

    def _remarshalling(self, stack_groups, actions):
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
        deliveries_unaccounted_for = len(self.cursor.pending_deliveries)
        delivery_stacks = []
        current_time = self.cursor.timestamp
        for stack in self.store.stacks:
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

    def apply(self, branch):
        item, tgt_id = branch
        cursor = self.cursor
        index = cursor.index
        src = self.move_item(item, tgt_id)
        if src is not RELEASE:
            self.flush_stacks([src])
        while cursor.index > index and not cursor.is_finished():
            index = cursor.index
            self.flush_stacks(self.store.stacks)

    def simulate(self):
        leaf = self.copy()
        leaf.semi_greedy_complete()
        return leaf

    def bound(self):
        return self.relocations + self.store.inversions

    # --------------------------------------------------------------------------
    def flush_stacks(self, stacks):
        """"Deliver items at the top of any stack in 'stacks' whose delivery is in the current
        instant (in the cursor object)."""
        deliveries = self.cursor.pending_deliveries
        if len(deliveries) > 0:
            for stack in stacks:
                while len(stack.items) > 0:
                    item = stack.items[-1]
                    if item not in deliveries:
                        break
                    self.move_item(item, DELIVERY.id)

    def move_item(self, item, tgt_id):
        store = self.store
        tgt = store.location_map[tgt_id]
        src = store.move(item, tgt)
        cursor = self.cursor
        timestamp = cursor.timestamp  # retrieve timestamp before cursor is automatically advanced
        if src is RELEASE:
            cursor.released_item(item)
        elif tgt is DELIVERY:
            cursor.delivered_item(item)
        self.actions.append((timestamp, item.id, src.id, tgt_id))
        return src

    def deliver_item(self, item):
        store = self.store
        src = store.item_location[item]
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
        store = self.store
        rng = self.solver.rng
        cursor = self.cursor
        release_sort_key = lambda i: (-i.due, i.id)
        delivery_sort_key = lambda i: (store.depth(i), i.id)
        while not cursor.is_finished():
            # lists of releases and deliveries must be computed before doing anything else
            # because the cursor automatically advances to the next instant when all events
            # have been processed.
            releases = sorted(cursor.pending_releases, key=release_sort_key)
            deliveries = sorted(cursor.pending_deliveries, key=delivery_sort_key)
            # Process deliveries
            for item in deliveries:
                self.deliver_item(item)
                # Stop the simulation if we've hit the cut value
                if store.relocations + store.inversions >= cut:
                    store.relocations = INF
                    return
            # Process releases
            for item in releases:
                options = self.placement_choices()
                stack = FO(item, options, rng) if len(options) > 1 else options[0]
                self.move_item(item, stack.id)

    def placement_choices(self, avoid=None):
        choices = []
        for group in self.store.stack_groups():
            if group[0] is not avoid:
                choices.append(group[0])
            elif len(group) > 1:
                choices.append(group[1])
        return choices

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from rr.opt.mcts import basic as mcts

from stacking import utils
from stacking.instance import RELEASE, DELIVERY
from stacking.solution import Solution

from . import simulation
from . import heuristics


INF = float("inf")


class TreeNode(mcts.TreeNode):
    @classmethod
    def root(cls, instance):
        root = cls()
        root.store = instance.store.copy(clear_move_callbacks=True)
        root.store.register_move_callback(root.on_move)
        root.cursor = instance.calendar.cursor()
        root.solution = Solution()
        root.unreleased_items = sum(len(instant.releases) for instant in instance.calendar)
        # Process immediate deliveries.
        for stack in root.store.inner_stacks():
            utils.flush_stack(root.store, stack, root.cursor.time)
        return root

    def copy(self):
        clone = mcts.TreeNode.copy(self)
        clone.store = self.store.copy(clear_move_callbacks=True)
        clone.store.register_move_callback(clone.on_move)
        clone.cursor = self.cursor.copy()
        clone.solution = self.solution.copy()
        clone.unreleased_items = self.unreleased_items
        return clone

    def branches(self):
        store = self.store
        cursor = self.cursor
        # Detect whether this node is a leaf. A node is a leaf when all releases have been
        # processed and there are no inversions in the store, so we are guaranteed to not have
        # further item relocations.
        if self.unreleased_items == 0 and store.inversions == 0:
            return ()

        # We only need to concern ourselves with relocations and releases (note that
        # remarshalling is not considered), because item deliveries are automatically handled by
        # our 'on_move()' handler. When we reach this method, we are guaranteed to not have *any*
        # deliverable item at the top of *any* stack.
        branches = []
        stack_groups = store.stack_groups()

        # To generate all valid reshuffling branches **without duplicates**, we first create a set
        # of non-equivalent source stacks (i.e. stacks containing deliverable items). Then, for
        # each such stack, we compute the list of valid target stacks and add those movements to
        # the branch list.
        all_sources = {store.location(item) for item in cursor.pending_deliveries}
        nonequiv_sources = utils.nonequivalent_stacks(all_sources)
        for source in nonequiv_sources:
            item = source.top
            target_ids = [target.id for target in utils.target_stacks(source, stack_groups)]
            branches.extend((item, target_id) for target_id in target_ids)

        # Item releases are much easier to generate: one branch per (item, stack_group) pair.
        target_ids = [target.id for target in utils.target_stacks(RELEASE, stack_groups)]
        for item in cursor.pending_releases:
            branches.extend((item, target_id) for target_id in target_ids)

        return branches

    def apply(self, branch):
        item, target_id = branch
        self.store.move(item, target_id)

    def simulate(self):
        solution = simulation.run(
            store=self.store,
            cursor=self.cursor,
            solution=self.solution,
            heuristic=heuristics.max_flexibility,
        )
        return mcts.Solution(value=solution.relocations, data=solution)

    def bound(self):
        return self.solution.relocations + self.store.inversions

    def on_move(self, store, item, source, target):
        """This method is called automatically by the store object whenever a move() is made."""
        assert store is self.store
        self.solution.record_move(store, item, source, target)
        cursor = self.cursor
        index = cursor.index  # store initial cursor index (see comment below)
        if source is RELEASE:
            cursor.mark_released(item)
            self.unreleased_items -= 1
        if target is DELIVERY:
            cursor.mark_delivered(item)

        # Flush the source stack if this was a relocation.
        # IMPORTANT: this *must* come after updates to the cursor object!
        if source is not RELEASE and target is not DELIVERY:
            utils.flush_stack(store, source, cursor.time)

        # If the cursor index advanced and there are deliveries in the current instant, flush all
        # stacks containing deliverable items. Repeat this until either the cursor stops advancing
        # or it advances into an instant without deliveries.
        while cursor.index > index and len(cursor.pending_deliveries) > 0:
            index = cursor.index  # record new cursor index to detect if it advances again
            time = cursor.time
            stacks = {store.location(i) for i in cursor.pending_deliveries}
            for stack in stacks:
                utils.flush_stack(store, stack, time)

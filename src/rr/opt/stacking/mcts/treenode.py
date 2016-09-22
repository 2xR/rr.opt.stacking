from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import rr.opt.mcts.basic as mcts

from rr.opt.stacking import utils
from rr.opt.stacking.instance import RELEASE
from rr.opt.stacking.solution import Solution

from . import simulation
from . import heuristics


INF = float("inf")


class TreeNode(mcts.TreeNode):
    @classmethod
    def root(cls, instance):
        root = cls()
        root.store = instance.store.copy(clear_move_callbacks=True)
        root.store.register_move_callback(cls.on_move)
        root.store.node = root
        root.cursor = instance.calendar.cursor()
        root.solution = Solution()
        root.unreleased_items = sum(len(instant.releases) for instant in instance.calendar)
        utils.flush_store(root.store, root.cursor)
        return root

    def copy(self):
        clone = mcts.TreeNode.copy(self)
        clone.store = self.store.copy(clear_move_callbacks=False)
        clone.store.node = clone
        clone.cursor = self.cursor.copy()
        clone.solution = self.solution.copy()
        clone.unreleased_items = self.unreleased_items
        return clone

    @staticmethod
    def on_move(store, item, source, target):
        """This method is called automatically by the store object whenever a move() is made.

        Note:
            See the root() and copy() methods above. A reference to the node is kept in the Store
            object so that we can record the movement in the Solution object and update the Cursor.
        """
        node = store.node
        node.solution.record_move(store, item, source, target)
        node.cursor.update_from_move(store, item, source, target)
        if source is RELEASE:
            node.unreleased_items -= 1

    def branches(self):
        # Detect whether this node is a leaf. A node is a leaf when all releases have been
        # processed and there are no inversions in the store, so we are guaranteed to not have
        # further item relocations.
        if self.unreleased_items == 0 and self.store.inversions == 0:
            return ()

        # We only need to concern ourselves with relocations and releases (note that
        # remarshalling is not considered), because item deliveries are handled by the calls to
        # 'utils.flush_stacks()' within 'root()' and 'apply()'. When we reach this method,
        # we are guaranteed to not have **any** deliverable item at the top of **any** stack.
        # 1) Generate reshuffling branches (without duplicates).
        time = self.cursor.time
        stack_groups = self.store.stack_groups()
        nonequiv_stacks = [group[0] for group in stack_groups]
        relocations = []
        branches = []
        for source in nonequiv_stacks:
            if source.due == time:
                targets = utils.target_stacks(source, stack_groups)
                # Search, from top to bottom, for the first item with due date equal to the
                # cursor's current time. We will use this "depth" to sort relocation movements
                # from shallowest to deepest.
                depth = 0
                for i in reversed(source.items):
                    if i.due == time:
                        break
                    depth += 1
                relocations.append((depth, source, targets))
        # Sort relocation branches by the depth of the item we're trying to deliver.
        for _, source, targets in sorted(relocations):
            item = source.top
            branches.extend((item, target.id) for target in targets)

        # 2) Item releases are much easier to generate: one branch per (item, stack_group) pair.
        target_ids = [target.id for target in nonequiv_stacks]
        due_dates = set()  # used to remove symmetries (items w/ same due date)
        for item in sorted(self.cursor.pending_releases, key=(lambda i: i.due), reverse=True):
            if item.due not in due_dates:
                due_dates.add(item.due)
                branches.extend((item, target_id) for target_id in target_ids)
        return branches

    def apply(self, branch):
        item, target_id = branch
        source = self.store.move(item, target_id)
        # If this movement was not a release, deliver all items that can be delivered
        # immediately. This is done to enforce the condition that, whenever we reach branches(),
        # there are no deliverable items at the top of any stack.
        if source is not RELEASE:
            utils.flush_store(self.store, self.cursor)

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

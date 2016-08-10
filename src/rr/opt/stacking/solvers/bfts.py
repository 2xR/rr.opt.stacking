from __future__ import unicode_literals
from builtins import range
from bisect import insort
from opt.treesearch import TreeSearch


class SP_BFTS(TreeSearch):
    default_root = SP_TreeNode.root

    def new_queue(self):
        return deque()

    def enqueue_nonroot(self, xxx_todo_changeme):
        (parent_node, branch_data) = xxx_todo_changeme
        node = parent_node.copy()
        node.apply(branch_data)
        self.enqueue_node(node)

    def enqueue_node(self, node):
        leaf = node.copy()
        leaf.semi_greedy_complete()
        self.check_leaf(leaf)
        insort(self.queue, (leaf.objective(), node))

    def enqueue(self, root):
        self.enqueue_node(root)
        self.enqueue = self.enqueue_nonroot

    def prune_queue(self):
        upper_bound = self.upper_bound
        queue = self.queue
        for _ in range(len(queue)):
            queue.rotate(+1)

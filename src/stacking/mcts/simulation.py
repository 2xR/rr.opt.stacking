from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random

from stacking import utils
from stacking.instance import RELEASE, DELIVERY
from stacking.solution import Solution

from . import heuristics


def run(store, cursor, solution=None, heuristic=heuristics.rand, rng=random):
    store = store.copy(clear_move_callbacks=True)
    cursor = cursor.copy()
    solution = solution.copy() if solution is not None else Solution()
    inner_stacks = list(store.inner_stacks())

    @store.register_move_callback
    def on_move(store, item, source, target):
        solution.record_move(store, item, source, target)
        if source is RELEASE:
            cursor.mark_released(item)
        if target is DELIVERY:
            cursor.mark_delivered(item)

    def place_item(item, source):
        stack_groups = utils.stack_groups(inner_stacks)
        candidates = utils.target_stacks(source, stack_groups)
        target = heuristic(item, candidates, rng) if len(candidates) > 1 else candidates[0]
        store.move(item, target)

    def deliver_item(item):
        source = store.location(item)
        top = source.top
        while top is not item:
            assert top.due > item.due
            place_item(top, source)
            top = source.top
        store.move(item, DELIVERY)

    # Key functions used to prioritize releases and deliveries.
    release_sort_key = lambda i: (-i.due, i.id)
    delivery_sort_key = lambda i: (store.depth(i), i.id)

    while not cursor.is_finished:
        # Compute sorted lists of releases and deliveries using the sort key functions above.
        # Note: we wouldn't be able to use pending_releases and pending_deliveries directly in a
        # for loop anyway, because the sets would be mutated during iteration.
        releases = sorted(cursor.pending_releases, key=release_sort_key)
        deliveries = sorted(cursor.pending_deliveries, key=delivery_sort_key)
        for item in deliveries:
            deliver_item(item)
        for item in releases:
            place_item(item, RELEASE)
    return solution

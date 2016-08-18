from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import range

from rr.opt.stacking.instance.stack import DELIVERY


def flush_stack(store, stack, time):
    """Deliver all items at the top of `stack` whose due date is equal to `time`."""
    for _ in range(len(stack.items)):
        item = stack.top
        if item.due != time:
            break
        source = store.move(item, DELIVERY)
        assert source is stack


def nonequivalent_stacks(stacks):
    """Given `stacks`, create a list of non-equivalent stacks (see :meth:`Stack.equivalent_to`)."""
    nonequivalent = []
    for stack in stacks:
        if not any(stack.equivalent_to(s) for s in nonequivalent):
            nonequivalent.append(stack)
    return nonequivalent


def stack_groups(stacks):
    """Create a list of groups of equivalent stacks.

    Note:
        This is similar to :meth:`nonequivalent_stacks`, however it returns a list of lists
        because it may be necessary to access an element of a group other than the first (when
        reshuffling for example).

    Returns:
        A list of lists of stacks. Each internal list represents a group of equivalent stacks.
    """
    groups = []
    for stack in stacks:
        for group in groups:
            if stack.equivalent_to(group[0]):
                group.append(stack)
                break
        else:
            groups.append([stack])
    return groups


def target_stacks(source, stack_groups):
    """Create a list of valid candidate stacks for item movements originating at `source`.

    Parameters:
        source (Stack): the stack we're starting the movement from.
        stack_groups ([[Stack]]): list of lists of equivalent stacks, as returned by
            `stack_groups()`.
    Returns:
        [Stack]: list of stacks onto which a valid move can be made.
    """
    targets = []
    for group in stack_groups:
        target = group[0]
        if target is source:
            # If 'source' is the same stack as 'target', then we pick the next stack in the same
            # group if possible. Otherwise we skip this singleton group.
            if len(group) > 1:
                target = group[1]
            else:
                continue
        targets.append(target)
    return targets

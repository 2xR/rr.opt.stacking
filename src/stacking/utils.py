from stacking.instance.stack import DELIVERY


def flush_stack(store, stack, time):
    """Deliver all items at the top of `stack` whose due date is equal to `time`.

    Returns:
        A list of the items that were delivered.
    """
    delivered = []
    while len(stack.items) > 0:
        item = stack.top
        if item.due != time:
            break
        source = store.move(item, DELIVERY)
        assert source is stack
        delivered.append(item)
    return delivered


def nonequivalent_stacks(stacks):
    """Given `stacks`, create a list of non-equivalent stacks (see :meth:`Stack.equivalent_to`)."""
    nonequivalent = []
    for stack in stacks:
        if not any(stack.equivalent_to(s) for s in nonequivalent):
            nonequivalent.append(stack)
    return nonequivalent


def stack_groups(stacks):
    """Create a list of groups of equivalent stacks.

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
    """Create a list of valid candidate stacks for item movements originating at `source`."""
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

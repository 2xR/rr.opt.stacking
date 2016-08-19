from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math


def rand(item, stacks, rng):
    """Selects randomly from all stacks."""
    return rng.choice(stacks)


def min_inversions(item, stacks, rng):
    """Selects randomly from stacks where `item` does not create a new inversion."""
    candidates = [stack for stack in stacks if stack.due >= item.due]
    if len(candidates) == 0:
        candidates = stacks
    return rng.choice(candidates)


def max_flexibility(item, stacks, rng):
    """Selects randomly from all stacks where `item` causes minimum loss of flexibility."""
    candidates = max_elems(stacks, key=lambda s: flexibility_score(item, s))
    return rng.choice(candidates) if len(candidates) > 1 else candidates[0]


def max_flexibility_bias(item, stacks, rng):
    """Similar to max_flexibility(), but uses weighted random selection instead of simply picking
    uniformly from the argmax of the flexibility score function."""
    biases = map(lambda s: flexibility_score(item, s), stacks)
    index = biased_choice(biases, rng)
    return stacks[index]


def flexibility_score(item, stack):
    """Assigns a score in [0, 1] to the movement `item -> stack`, related to the loss of "stack
    flexibility". A stack is considered more flexible if it can receive a larger set of items
    with creating new inversions.
    """
    # TODO: consider balancing stack height in the score, or maybe in a different score function.
    dflex = item.due - stack.due  # stack flexibility delta
    if math.isnan(dflex):  # item.due == stack.due == INF
        return 0.5
    elif dflex > 0.0:  # inversion -> score in [0.0, 0.5]
        return 0.5 / (1.0 + dflex)
    else:  # non-inversion -> score in ]0.5, 1.0]
        return 0.5 / (1.0 - dflex) + 0.5


def max_elems(iterable, key=None):
    """Find the elements in 'iterable' corresponding to the maximum values w.r.t. 'key'."""
    iterator = iter(iterable)
    try:
        elem = next(iterator)
    except StopIteration:
        raise ValueError("argument iterable must be non-empty")
    max_elems = [elem]
    max_key = elem if key is None else key(elem)
    for elem in iterator:
        curr_key = elem if key is None else key(elem)
        if curr_key > max_key:
            max_elems = [elem]
            max_key = curr_key
        elif curr_key == max_key:
            max_elems.append(elem)
    return max_elems


def biased_choice(biases, rng):
    """Randomly pick an integer index using different probabilities for selecting each index. The
    list 'biases' should contain the bias (or weight) of each index in the random draw. Biases
    should be non-negative real numbers of any magnitude. The probability of each index is the
    quotient between its bias and the sum of all biases."""
    biases = list(biases)
    assert all(bias >= 0.0 for bias in biases)
    X = rng.uniform(0.0, sum(biases))
    Y = 0.0
    for index, bias in enumerate(biases):
        Y += bias
        if Y >= X:
            return index
    raise Exception("this really shouldn't have happened... how embarrassing (o_O)")

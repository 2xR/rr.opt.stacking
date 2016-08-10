from __future__ import division
from __future__ import unicode_literals
from past.utils import old_div
from functools import partial
from math import isnan
from utils.misc import max_elems


def RAND(item, stacks, rng):
    return rng.choice(stacks)


def MC(item, stacks, rng):
    RCL = [stack for stack in stacks if stack.due >= item.due]
    if len(RCL) == 0:
        RCL = stacks
    return rng.choice(RCL)


def FO(item, stacks, rng):
    return rng.choice(max_elems(stacks, key=partial(FO_score, item)))


def FO_score(item, stack):
    dflex = item.due - stack.due
    if isnan(dflex):
        return 1.0
    elif dflex > 0.0:
        return old_div(1.0, (1.0 + dflex)) - 1.0
    else:
        return old_div(1.0, (1.0 - dflex))

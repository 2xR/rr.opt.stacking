from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import next

import bisect
import collections
import random

import rr.opt.stacking as sp
from rr.opt.stacking.mcts import simulation, heuristics


INF = float("inf")


class Instance(object):
    """Non-determistic Stacking Problem instance."""
    def __init__(self, store, interarrival_distr, stay_distr, **meta):
        self.store = store.copy()
        self.interarrival_distr = interarrival_distr
        self.stay_distr = stay_distr
        self.meta = meta

    def copy(self):
        return type(self)(
            store=self.store,
            interarrival_distr=self.interarrival_distr,
            stay_distr=self.stay_distr,
            **self.meta,
        )

    def observation(self, start_at, end_at, immediate_arrivals=()):
        time = start_at
        items = [sp.Item(id=i.id, due=time+self.stay_distr(i.release)) for i in self.store.items]
        for item in immediate_arrivals:
            items.append(sp.Item(id=item.id, release=time, due=time+self.stay_distr(time)))

        store = sp.Store()




        items = [item.copy() for item in self.store.items]
        item_id = 0 if len(items) == 0 else max(item.id for item in items) + 1
        if immediate_arrivals > 0:
            for _ in range(immediate_arrivals):
                items.append(sp.Item(item_id, release=time, due=self.stay_distr(time)))
        while time < end_at:
            time += self.interarrival_distr(time)
            items.append(sp.Item(
                id=item_id,
                release=time,
                due=min(end_at, time+self.stay_distr(time)),
            ))
            item_id += 1
        return sp.Instance(items, self.store, generated_from=self)


def select_first_move(sols):
    """Given a list of solutions, select the most common first move. No move is selected if there
    are not enough observations or if there is a tie for the most common first move.
    """
    if len(sols) < 10:
        return None
    first_move = collections.Counter(sol.moves[0] for sol in sols)
    if len(first_move) == 1:
        return next(iter(first_move))
    (m1, c1), (m2, c2) = first_move.most_common(2)
    return m1 if c1 > c2 else None


def sample_from_schedule(schedule):
    def sample_func(t):
        t %= schedule[-1][0]  # map 't' to [0, 24*HOUR)
        i = bisect.bisect_left(schedule, (t,))
        func = schedule[i][1]
        obs = func(t)
        assert obs >= 0
        return obs
    return sample_func


def solve(actual_items, instance, end_at=None):
    actual_calendar = sp.Calendar(actual_items)  # calendar of actual events
    if end_at is None:
        end_at = actual_calendar[-1].time
    instance = instance.copy()  # copy the instance because we're going to modify its store
    solution = sp.Solution()
    solution.record_from(instance.store)
    cursor = actual_calendar.cursor()
    cursor.update_from(instance.store)
    while not cursor.is_finished:
        sols = []
        move = None
        while move is None:
            obs = instance.observation(
                start_at=cursor.time,
                end_at=end_at,
                predefined_items=cursor.pending_releases,
            )
            sol = simulation.run(
                store=obs.store,
                cursor=obs.calendar.cursor(),
                heuristic=heuristics.max_flexibility,
            )
            sols.append(sol)
            move = select_first_move(sols)
        item, _, target_id = move
        instance.store.move(item, target_id)
    return solution


MINUTE = 1  # will be our unit of time
HOUR = 60 * MINUTE
DAY = 24 * HOUR

INTERARRIVAL_SCHEDULE = [
    (6*HOUR, lambda t: random.expovariate(1 / HOUR)),
    (7.5*HOUR, lambda t: random.expovariate(2 / HOUR)),
    (9.5*HOUR, lambda t: random.expovariate(40 / HOUR)),
    (11*HOUR, lambda t: random.expovariate(10 / HOUR)),
    (13*HOUR, lambda t: random.expovariate(3 / HOUR)),
    (14.5*HOUR, lambda t: random.expovariate(10 / HOUR)),
    (19*HOUR, lambda t: random.expovariate(5 / HOUR)),
    (21*HOUR, lambda t: random.expovariate(10 / HOUR)),
    (24*HOUR, lambda t: random.expovariate(1 / HOUR)),
]
STAY_SCHEDULE = [
    (10*HOUR, lambda t: random.gauss(10*HOUR, 1*HOUR)),
    (13*HOUR, lambda t: random.gauss(6*HOUR, 1*HOUR)),
    (22*HOUR, lambda t: random.gauss(2*HOUR, 0.5*HOUR)),
    (24*HOUR, lambda t: random.gauss(0.5*HOUR, 0.1*HOUR)),
]


instance = Instance(
    store=sp.Store(stack_count=20, stack_max_size=20),
    interarrival_distr=sample_from_schedule(INTERARRIVAL_SCHEDULE),
    stay_distr=sample_from_schedule(STAY_SCHEDULE),
)
random.seed(0)
actual_items = instance.observation(start_at=0, end_at=1*DAY).items

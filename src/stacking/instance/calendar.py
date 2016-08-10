from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object

import bisect
import collections
import math


INF = float("inf")
Instant = collections.namedtuple("Instant", ["time", "releases", "deliveries"])


class Calendar(list):
    """A simple event calendar class for the Stacking Problem.

    A calendar is just an ordered list of Instant objects. Each instant consists of a timestamp T
    and two sets of items:

        1) releases - items which enter the store on this date
        2) deliveries - items which must be delivered on this date

    A cursor to the calendar can be obtained by calling the cursor() method. Each cursor object
    maintains its own position in the calendar, meaning that multiple cursors on the same
    calendar can be used without affecting one another.
    """
    __slots__ = ()  # prevent creation of per-instance __dict__

    def __init__(self, items):
        list.__init__(self)
        for item in items:
            low_index = 0  # position where binary search starts from
            for time, item_set_name in ((item.release, "releases"), (item.due, "deliveries")):
                if math.isinf(time):  # skip infinite due/release dates
                    continue
                index = bisect.bisect_left(self, (time,), low_index)
                if index < len(self):
                    instant = self[index]
                    if instant.time != time:
                        instant = Instant(time, set(), set())
                        self.insert(index, instant)
                else:
                    instant = Instant(time, set(), set())
                    self.append(instant)
                item_set = getattr(instant, item_set_name)
                item_set.add(item)
                low_index = index + 1  # restrict indices considered by bisect for next iteration

    def cursor(self):
        return Cursor(self)


class Cursor(object):
    """A cursor marks a position on a calendar. Items must be marked as delivered or released
    before advancing the cursor to the next instant in the calendar.
    """
    def __init__(self, calendar):
        self.calendar = calendar  # Calendar to which this cursor is associated
        self.index = -1  # index of the current instant
        self.pending_releases = set()  # items which MUST be released in the current instant
        self.pending_deliveries = set()  # items which MUST be delivered in the current instant
        self.advance()  # move to first instant

    def copy(self):
        cls = type(self)
        clone = cls.__new__(cls)
        clone.calendar = self.calendar
        clone.index = self.index
        clone.pending_releases = set(self.pending_releases)
        clone.pending_deliveries = set(self.pending_deliveries)
        return clone

    @property
    def instant(self):
        return self.calendar[self.index]

    @property
    def time(self):
        return self.calendar[self.index].time

    def is_finished(self):
        return (
            self.index >= len(self.calendar) - 1 and
            len(self.pending_releases) == 0 and
            len(self.pending_deliveries) == 0
        )

    def can_advance(self):
        return (
            self.index < len(self.calendar) - 1 and
            len(self.pending_releases) == 0 and
            len(self.pending_deliveries) == 0
        )

    def advance(self):
        if len(self.pending_releases) > 0:
            raise Exception("pending releases: {}".format(self.pending_releases))
        if len(self.pending_deliveries) > 0:
            raise Exception("pending deliveries: {}".format(self.pending_deliveries))
        self.index += 1
        instant = self.calendar[self.index]
        self.pending_releases = set(instant.releases)
        self.pending_deliveries = set(instant.deliveries)

    def mark_delivered(self, item):
        self.pending_deliveries.remove(item)
        if self.can_advance():
            self.advance()

    def mark_released(self, item):
        self.pending_releases.remove(item)
        if self.can_advance():
            self.advance()

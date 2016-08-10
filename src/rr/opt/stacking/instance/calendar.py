from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object

from bisect import insort_right
from collections import namedtuple


INF = float("inf")
Instant = namedtuple("Instant", "releases, deliveries")


class Calendar(object):
    """An event schedule for the stacking problem. Each instant consists of a timestamp T and two
    sets of items:
        1) releases - items which enter the warehouse at this date
        2) deliveries - items which must be delivered on this date
    A cursor to the calendar can be obtained by calling the cursor() method. Each cursor object
    maintains its own position in the calendar, meaning that multiple cursors on the same calendar
    can be used without affecting one another.
    """
    def __init__(self, items=()):
        self.timestamps = []  # [timestamp] (sorted)
        self.instants = {}  # {timestamp: Instant({releases}, {deliveries})}
        self.item_map = {}  # {id: Item}
        self.last_release = INF
        for item in items:
            self.add(item)

    def cursor(self):
        cursor = Cursor(self)
        cursor.advance()
        return cursor

    def add(self, item):
        if item.id in self.item_map:
            raise NameError("duplicate item id in calendar")
        self.item_map[item.id] = item
        if item.release is not None:
            self.get_entry(item.release).releases.add(item)
            self.last_release = max(self.last_release, item.release)
        if item.due is not None:
            self.get_entry(item.due).deliveries.add(item)

    def get_entry(self, timestamp):
        try:
            return self.instants[timestamp]
        except KeyError:
            entry = Instant(set(), set())
            self.instants[timestamp] = entry
            insort_right(self.timestamps, timestamp)
            return entry


class Cursor(object):
    """A cursor marks a position on a calendar. Items must be marked as delivered or released
    before advancing the cursor to the next instant in the calendar."""
    __slots__ = ("calendar", "index", "releases", "deliveries")

    def __init__(self, calendar):
        self.calendar = calendar  # Calendar object on which the cursor marks a position
        self.index = -1           # index of the current timestamp
        self.releases = None      # items which MUST be released in the current instant
        self.deliveries = None    # items which MUST be delivered in the current instant

    def copy(self):
        clone = type(self)(self.calendar)
        clone.index = self.index
        clone.releases = set(self.releases)
        clone.deliveries = set(self.deliveries)
        return clone

    @property
    def timestamp(self):
        return self.calendar.timestamps[self.index]

    def is_finished(self):
        return (
            self.index >= len(self.calendar.timestamps) - 1 and
            len(self.releases) == 0 and
            len(self.deliveries) == 0
        )

    def can_advance(self):
        return (self.index < len(self.calendar.timestamps) - 1 and
                len(self.releases) == 0 and
                len(self.deliveries) == 0)

    def advance(self):
        if self.index >= 0:
            if len(self.releases) > 0:
                raise Exception("some unreleased items must be released in the current instant")
            if len(self.deliveries) > 0:
                raise Exception("some undelivered items must be delivered in the current instant")
        self.index += 1
        timestamp = self.calendar.timestamps[self.index]
        releases, deliveries = self.calendar.instants[timestamp]
        self.releases = set(releases)
        self.deliveries = set(deliveries)

    def delivered_item(self, item):
        self.deliveries.remove(item)
        if self.can_advance():
            self.advance()

    def released_item(self, item):
        self.releases.remove(item)
        if self.can_advance():
            self.advance()

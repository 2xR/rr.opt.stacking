from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object


INF = float("inf")


class Item(object):
    """Simple object for holding the data relative to a single item.
    """

    def __init__(self, id, release=-INF, due=+INF, meta=None):
        assert release < due
        self.id = id
        self.release = release
        self.due = due
        self.meta = meta

    def __repr__(self):
        return "{}#{}".format(type(self).__name__, self.id)

    def __str__(self):
        return "<{}#{} r={} d={} @{:x}>".format(
            type(self).__name__, self.id, self.release, self.due, id(self))

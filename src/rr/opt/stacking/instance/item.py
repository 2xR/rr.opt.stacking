from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from rr import pretty


INF = float("inf")


@pretty.klass
class Item(object):
    """Simple object for holding the data relative to a single item.
    """
    def __init__(self, id, release=-INF, due=+INF, meta=None):
        assert release < due
        self.id = id
        self.release = release
        self.due = due
        self.meta = meta

    def __info__(self):
        return "{}, r={}, d={}".format(self.id, self.release, self.due)

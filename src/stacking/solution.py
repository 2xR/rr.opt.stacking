from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object

from stacking.instance.stack import RELEASE, DELIVERY


class Solution(object):
    """Simple class to keep a list of moves and number of relocations.

    This class defines a method to record moves in a store, which can either be used directly or
    as a "move callback" for :meth:`Store.on_move`.
    """
    def __init__(self):
        self.moves = []
        self.relocations = 0

    def __repr__(self):
        moves = "\n".join("\ti{}: s{} -> s{}".format(
            item.id,
            "R" if src_id == 0 else src_id,
            "D" if tgt_id == -1 else tgt_id,
        ) for item, src_id, tgt_id in self.moves)
        return "<{}\n{}\n@{:x}>".format(type(self).__name__, moves, id(self))

    def copy(self):
        cls = type(self)
        clone = cls.__new__(cls)
        clone.moves = list(self.moves)
        clone.relocations = self.relocations
        return clone

    def record_from(self, store):
        store.register_move_callback(self.record_move)

    def record_move(self, _, item, source, target):
        self.moves.append((item, source.id, target.id))
        if source is not RELEASE and target is not DELIVERY:
            self.relocations += 1

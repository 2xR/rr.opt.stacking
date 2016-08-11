from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object, open, range

from .item import Item
from .store import Store
from .calendar import Calendar


INF = float("inf")


class Instance(object):
    """An instance of the Stacking Problem consists of a store state and a set of items.
    Additionally, an event calendar is created from the release and due dates of all items.
    """
    def __init__(self, items, store, **meta):
        self.items = list(items)
        self.store = store.copy()
        self.calendar = Calendar(self.items)
        self.meta = meta

    @classmethod
    def load(cls, filepath):
        with open(filepath, "rt") as istream:
            params = {"height": INF, "name": "<no name>"}
            line = next_content_line(istream)
            while line != "--- end of header ---":
                name, value = parse_param(line)
                params[name] = value
                line = next_content_line(istream)
            items = []
            for x in range(params["items"]):
                line = next_content_line(istream)
                item_id, release, due = [int(part) for part in line.split()]
                items.append(Item(item_id, release, due))
        store = Store(nstacks=params["width"], max_height=params["height"])
        return cls(items, store, name=params["name"])


def next_content_line(stream):
    """Auxiliary function. Read lines from a stream (open readable file object-like) until a
    non-comment line (comments begin with #) is found."""
    while True:
        line = stream.readline()
        if len(line) == 0:  # EOF
            return None
        line = line.strip()
        if line[0] != "#":
            return line


def parse_str(value):
    return value


def parse_int(value):
    if value == "inf":
        return INF
    return int(value)


def parse_param(line):
    param_decl, param_value = line.split(":=")
    param_type, param_name = param_decl.split()
    return param_name, PARSE_FUNC[param_type](param_value.strip())


PARSE_FUNC = dict(str=parse_str, int=parse_int)

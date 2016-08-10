from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import object, range

from utils.misc import INF
from utils.namespace import Namespace

from stacking.instance.item import Item
from stacking.instance.warehouse import Warehouse
from stacking.instance.calendar import Calendar


class Instance(object):
    """An instance of the Stacking Problem consists of a warehouse state and a set of items."""
    def __init__(self, items, warehouse, **meta):
        self.items = list(items)
        self.calendar = Calendar(items)
        self.warehouse = warehouse.copy()
        self.warehouse.set_items(items)
        self.meta = Namespace(meta)

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r") as istream:
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
        warehouse = Warehouse(nstacks=params["width"])
        return cls(items, warehouse, name=params["name"])


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

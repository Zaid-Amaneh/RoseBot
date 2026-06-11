import collections
import collections.abc

for _name in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Set", "Hashable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

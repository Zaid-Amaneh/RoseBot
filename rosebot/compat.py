"""Compatibility shim (plumbing) so ``experta`` runs on Python 3.10.

Reason: ``experta`` depends on ``frozendict==1.2``, which uses names removed from
``collections`` in Python 3.10+ (e.g. ``collections.Mapping``). We rebind them from
``collections.abc``. This module must be imported **before** any ``import experta``.
"""

import collections
import collections.abc

for _name in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Set", "Hashable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

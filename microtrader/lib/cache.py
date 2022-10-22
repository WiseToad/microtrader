from typing import final
from collections import deque
from uuid import uuid4
from lib.decors import throwingmember

@final
class Cache:

    @throwingmember
    def __init__(self, limit):
        if limit <= 0:
            raise ParameterError(f"Invalid cache limit value ({maxCount})")
        self._limit = limit

        self._items = {}
        self._ids = deque()
        self._count = 0

    def add(self, item):
        id = uuid4()
        self._items[id] = item
        self._ids.append(id)

        if self._count < self._limit:
            self._count += 1
        else:
            self._items.pop(self._ids.popleft(), None)

        return id

    def __getitem__(self, id):
        return self._items[id]

    def __setitem__(self, id, item):
        if id not in self._items:
            raise KeyError("Specified id does not exists")
        self._items[id] = item

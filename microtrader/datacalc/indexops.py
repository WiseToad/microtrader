from typing import final
from bisect import bisect
from functools import partial
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from datacalc.stream import Stream
from datacalc.validators import noDecreaseValidator

# Value picker.
#
# Picks values from source into target by given index list in "sparse" manner.
# Target is suitable for rendering individual points along with other value graphs.
#
# Streams:
#     indexes - IN
#     source  - IN
#     target  - OUT

@final
class PickOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._indexes = noDecreaseValidator(streams["indexes"], retroactor = self._onRetroaction)
        self._source = Stream(streams["source"])
        self._target = Stream(streams["target"])

    def calc(self):
        self._target.setLen(len(self._source))

        for i in self._indexes:
            self._source.setPos(i)
            self._target[i] = self._source.getNext()

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._source.setPos(
                self._indexes.peekSource(index - 1) + 1
                if index > 0 else 0
            )
            self._target.setLen(self._source.getPos())

# Value lookup.
#
# Collects values from source into target by given index list in "condensed" manner.
# Output is intended to be intermediate data for further processing.
#
# Streams:
#     indexes - IN
#     source  - IN
#     target  - OUT

@final
class LookupOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._indexes = noDecreaseValidator(streams["indexes"], retroactor = self._onRetroaction)
        self._source = Stream(streams["source"])
        self._target = Stream(streams["target"])

    def calc(self):
        for i in self._indexes:
            self._source.setPos(i)
            self._target.append(self._source.getNext())

    def _onRetroaction(self, change, index, indexes):
        if change.isAfter():
            self._source.setPos(
                self._indexes.peekSource(index - 1) + 1
                if index > 0 else 0
            )
            self._target.setLen(index)

# Co-index operator.
#
# Calculates relaxed intersection of index sets, represented by ordered lists of indexes.
#
# Params:
#     (epsilon = 2) - maximum difference between index values to accept their match
#
# Streams:
#     indexes1      - IN  ordered index list 1
#     indexes2      - IN  ordered index list 2
#     coindexes1    - OUT indexes from list 1 matched with indexes from list2
#     coindexes2    - OUT indexes from list 2 matched with indexes from list1

@final
class CoindexOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            epsilon = params.get("epsilon", 2)
            if epsilon < 0:
                raise ParamError(f"Invalid epsilon value ({epsilon})")
            self._epsilon = epsilon
        except Exception as e:
            raise ParamError(e) from e

        self._indexes1 = increaseValidator(streams["indexes1"])
        self._coindexes1 = Stream(streams["coindexes1"])
        self._indexes2 = increaseValidator(streams["indexes2"])
        self._coindexes2 = Stream(streams["coindexes2"])

        self._indexes1.setRetroactor(
            partial(self._onRetroaction,
                indexes = indexes1,
                coindexes = self._coindexes
            )
        )
        self._indexes2.setRetroactor(
            partial(self._onRetroaction,
                indexes = indexes2,
                coindexes = self._coindexes2
            )
        )

    def calc(self):
        indexes1 = iter(self._indexes1)
        indexes2 = iter(self._indexes2)
        try:
            while True:
                i1 = next(indexes1)
                while True:
                    i2 = next(indexes2)
                    if i2 >= i1 - self._epsilon:
                        break

                if i1 >= i2 - self._epsilon:
                    self._coindexes1.append(i1)
                    self._coindexes2.append(i2)

                i2 = next(indexes2)
                while True:
                    i1 = next(indexes1)
                    if i1 >= i2 - self._epsilon:
                        break

                if i2 >= i1 - self._epsilon:
                    self._coindexes1.append(i1)
                    self._coindexes2.append(i2)
        except StopIteration:
            pass

    def _onRetroaction(self, change, index, indexes, coindexes):
        if change.isAfter():
            coindexesLen = (
                bisect(coindexes, indexes.peekSource(index - 1))
                if index > 0 else 0
            )
            self._coindexes1.setLen(coindexesLen)
            self._coindexes2.setLen(coindexesLen)

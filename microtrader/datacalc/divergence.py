from typing import final
from enum import Enum
from functools import partial
from bisect import bisect
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from datacalc.stream import Stream
from datacalc.compound import *
from datacalc.indexops import *
from datacalc.lineops import *

@final
class DivergenceType(Enum):
    CONVERGENCE = -1 # Considered as "bullish divergence" if detected on negative peaks (the minimums)
    DIVERGENCE = 1   # Considered as "bearish divergence" if detected on positive peaks (the maximums)

@final
class DivergenceClass(Enum):
    A = 1
    B = 2
    C = 3

@final
class Divergence:

    def __init__(self, divergenceType, divergenceClass, index1, index2):
        self.divergenceType = divergenceType
        self.divergenceClass = divergenceClass
        self.index1 = index1 # peak index of source 1
        self.index2 = index2 # peak index of source 2

# Divergence detector.
#
# Params:
#     (epsilon)                 - CoindexOperator parameter
#     (threshold1)              - SlopeOperator parameter for source 1
#     (threshold2)              - SlopeOperator parameter for source 2
#                               
# Streams:                      
#     indexes1                  - IN  peak indexes of source 1
#     source1                   - IN
#     indexes2                  - IN  peak indexes of source 2
#     source2                   - IN
#     time                      - IN
#
#     divergences: [Divergence] - OUT
#     (lines1): [Line]          - OUT
#     (lines2): [Line]          - OUT
#
# See also: https://smart-lab.ru/finansoviy-slovar/divergence

@final
class DivergenceOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._divergences = FilterStream(streams["divergences"])
        self._lines1 = Stream(streams.get("lines1"))
        self._lines2 = Stream(streams.get("lines2"))

        self._coindexes1 = Stream()
        self._slopeTypes1 = Stream()
        self._coindexes2 = Stream()
        self._slopeTypes2 = Stream()
        
        self._slopeTypes1.setRetroactor(
            partial(self._onRetroaction,
                coindexes = self._coindexes1,
                slopeTypes = self._slopeTypes1,
                indexSelector = lambda divergence: divergence.index1
            )
        )
        self._slopeTypes2.setRetroactor(
            partial(self._onRetroaction,
                coindexes = self._coindexes2,
                slopeTypes = self._slopeTypes2,
                indexSelector = lambda divergence: divergence.index2
            )
        )

        self._slopeOperators = CompoundOperator(
            configs = [
                OperatorConfig(
                    CoindexOperator,
                    paramMap = {
                        "epsilon": "epsilon"
                    },
                    streamMap = {
                        "indexes1": "indexes1",
                        "indexes2": "indexes2",
                        "coindexes1": "coindexes1",
                        "coindexes2": "coindexes2"
                    }
                ),
                OperatorConfig(
                    SlopeOperator,
                    paramMap = {
                        "threshold": "threshold1"
                    },
                    streamMap = {
                        "indexes": "coindexes1",
                        "source": "source1",
                        "time": "time",
                        "slopeTypes": "slopeTypes1"
                    }
                ),
                OperatorConfig(
                    SlopeOperator,
                    paramMap = {
                        "threshold": "threshold2"
                    },
                    streamMap = {
                        "indexes": "coindexes2",
                        "source": "source2",
                        "time": "time",
                        "slopeTypes": "slopeTypes2"
                    }
                )
            ],
            params = params,
            streams = {
                "indexes1": streams["indexes1"],
                "source1": streams["source1"],
                "indexes2": streams["indexes2"],
                "source2": streams["source2"],
                "time": streams["time"],

                "coindexes1": self._coindexes1,
                "coindexes2": self._coindexes2,
                "slopeTypes1": self._slopeTypes1,
                "slopeTypes2": self._slopeTypes2,
            }
        )

    def calc(self):
        self._slopeOperators.calc()

        for (i1, slopeType1), (i2, slopeType2) in zip(
            self._slopeTypes1.indexed(), self._slopeTypes2.indexed(),
            strict = True
        ):
            divergenceType, divergenceClass = None, None
            if slopeType1 == SlopeType.DOWN and slopeType2 == SlopeType.UP:
                divergenceType, divergenceClass = DivergenceType.CONVERGENCE, DivergenceClass.A
            elif slopeType1 == SlopeType.NONE and slopeType2 == SlopeType.UP:
                divergenceType, divergenceClass = DivergenceType.CONVERGENCE, DivergenceClass.B
            elif slopeType1 == SlopeType.DOWN and slopeType2 == SlopeType.NONE:
                divergenceType, divergenceClass = DivergenceType.CONVERGENCE, DivergenceClass.C
            elif maxSlopeType1 == SlopeType.UP and maxSlopeType2 == SlopeType.DOWN:
                divergenceType, divergenceClass = DivergenceType.DIVERGENCE, DivergenceClass.A
            elif maxSlopeType1 == SlopeType.NONE and maxSlopeType2 == SlopeType.DOWN:
                divergenceType, divergenceClass = DivergenceType.DIVERGENCE, DivergenceClass.B
            elif maxSlopeType1 == SlopeType.UP and maxSlopeType2 == SlopeType.NONE:
                divergenceType, divergenceClass = DivergenceType.DIVERGENCE, DivergenceClass.C

            if divergenceType is not None and divergenceClass is not None:
                self._coindexes1.setPos(i1 - 1)
                line1 = Line(
                    self._coindexes1.getNext(),
                    self._coindexes1.getNext()
                )

                self._coindexes2.setPos(i2 - 1)
                line2 = Line(
                    self._coindexes2.getNext(),
                    self._coindexes2.getNext()
                )

                self._divergences.append(
                    Divergence(
                        divergenceType, 
                        divergenceClass, 
                        line1.endIndex, 
                        line2.endIndex
                    )
                )
                self._lines1.append(line1)
                self._lines2.append(line2)

    def _onRetroaction(self, change, index, coindexes, slopeTypes, indexSelector):
        if change.isAfter():
            coindexes.setPos(index)
            slopeTypes.setPos(index)

            self._divergences.setLen(
                bisect(self._divergences, coindexes[index - 1], key = indexSelector)
                if index > 0 else 0
            )

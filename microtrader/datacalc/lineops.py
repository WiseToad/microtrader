from typing import final
from enum import Enum
from datetime import timedelta
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from datacalc.stream import Stream
from datacalc.compound import *

@final
class Line:

    def __init__(self, startIndex, endIndex):
        self.startIndex = startIndex
        self.endIndex = endIndex

@final
class SlopeType(Enum):
    UP = 1
    DOWN = -1
    NONE = 0

# Line plotter.
#
# Streams:
#     lines: [Lines] - IN
#     source         - IN
#     target         - OUT

@final
class LineOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._lines = sequenceValidator(
            streams["lines"],
            lambda line, prevLine: (
                line is None or prevLine is None 
                or min(line.startIndex, line.endIndex) >= max(prevLine.startIndex, prevLine.endIndex)
            ),
            retroactor = self._onRetroaction
        )
        self._source = Stream(streams["source"])
        self._target = Stream(streams["target"])

    def calc(self):
        self._target.setLen(len(self._source))

        for line in self._lines:
            startIndex, endIndex = line.startIndex, line.endIndex
            if startIndex > endIndex: startIndex, endIndex = endIndex, startIndex

            self._source.setPos(startIndex)
            xStart = self._source.getNext()
            self._source.setPos(endIndex)
            xEnd = self._source.getNext()
            
            if startIndex < endIndex:
                delta = (xEnd - xStart) / (endIndex - startIndex)
                x = xStart
                for i in range(startIndex, endIndex):
                    self._target[i] = x
                    x += delta
            self._target[endIndex] = xEnd

    def _onRetroaction(self, change, index):
        if change.isAfter():
            if index > 0:
                prevLine = self._lines.peekSource(index - 1)
                self._source.setPos(max(prevLine.startIndex, prevLine.endIndex) + 1)
            else:
                self._source.setPos(0)

            self._target.setLen(self._source.getPos())

# Slope detector.
#
# Params:
#     (threshold = 0.0)       - endpoint value difference, normalized to one-minute time interval, to recognize a slope
#
# Streams:
#     indexes                 - IN
#     source                  - IN
#     time                    - IN
#     slopeTypes: [SlopeType] - OUT

@final
class SlopeOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            threshold = params.get("threshold", 0.0)
            if threshold < 0.0:
                raise ParamError(f"Invalid threshold value ({threshold})")
            self._threshold = threshold
        except Exception as e:
            raise ParamError(e) from e

        self._sourceDelta = Stream(None, self._onRetroaction)
        self._timeDelta = Stream()
        self._slopeTypes = Stream(streams["slopeTypes"])

        self._deltaOperator = CompoundOperator(
            configs = [
                OperatorConfig(
                    LookupOperator,
                    streamMap = {
                        "indexes": "indexes",
                        "source": "source",
                        "target": "sourceLookup"
                    }
                ),
                OperatorConfig(
                    mapperOperator(deltaMapper),
                    streamMap = {
                        "source": "sourceLookup",
                        "target": "sourceDelta"
                    }
                ),
                OperatorConfig(
                    LookupOperator,
                    streamMap = {
                        "indexes": "indexes",
                        "source": "time",
                        "target": "timeLookup"
                    }
                ),
                OperatorConfig(
                    mapperOperator(deltaMapper),
                    streamMap = {
                        "source": "timeLookup",
                        "target": "timeDelta"
                    }
                )
            ],
            streams = {
                "indexes": streams["indexes"],
                "source": streams["source"],
                "time": streams["time"],
                "sourceDelta": self._sourceDelta,
                "timeDelta": self._timeDelta
            }
        )

    def calc(self):
        self._deltaOperator.calc()

        for dx, dt in zip(
            self._sourceDelta, self._timeDelta,
            strict = True
        ):
            if dx is None or dt is None:
                slopeType = None
            else:
                slope = dx / (dt / timedelta(minutes = 1))
                if slope > self._threshold:
                    slopeType = SlopeType.UP
                elif slope < -self._threshold:
                    slopeType = SlopeType.DOWN
                else:
                    slopeType = SlopeType.NONE

            self._slopeTypes.append(slopeType)

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._slopeTypes.setLen(index)

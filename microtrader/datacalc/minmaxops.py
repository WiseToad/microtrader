from typing import final
from enum import Enum
from collections import deque
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from lib.utils import mapDict
from datacalc.stream import Stream
from datacalc.indicators import ChannelOperator

@final
class PeakType(Enum):
    MIN = -1
    MAX = 1

# Moving min/max.
#
# Params:
#     (lag = 10) - moving window lower bound lag (in samples) to get min/max within it
#
# Streams:
#     source     - IN
#     min        - OUT
#     max        - OUT

@final
class MinMaxOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            lag = params.get("lag", 10)
            if lag < 0:
                raise ParamError(f"Invalid lag value ({lag})")
            self._lag = lag
        except Exception as e:
            raise ParamError(e) from e

        self._source = Stream(streams["source"])
        self._min = Stream(streams["min"])
        self._max = Stream(streams["max"])

        self._minDeque = deque()
        self._maxDeque = deque()

    def calc(self):
        for i, x in self._source.indexed():
            if x is not None:
                while self._minDeque and self._source[self._minDeque[-1]] >= x:
                    self._minDeque.pop()
                self._minDeque.append(i)

                while self._maxDeque and self._source[self._maxDeque[-1]] <= x:
                    self._maxDeque.pop()
                self._maxDeque.append(i)

            j = max(0, i - self._lag)
            while self._minDeque and self._minDeque[0] < j:
                self._minDeque.popleft()
            while self._maxDeque and self._maxDeque[0] < j:
                self._maxDeque.popleft()

            self._min.append(
                None if not self._minDeque
                else self._source[self._minDeque[0]]
            )
            self._max.append(
                None if not self._maxDeque
                else self._source[self._maxDeque[0]]
            )

# Fractal-based peak detector with additional burst threshold and min/max criterias.
#
# Params:
#     (width = 5)           - peak width in samples
#     (threshold = 0.0)     - burst absolute value to recognize a peak
#     (minMaxLag = 10)      - MinMaxOperator parameter
#
# Streams:
#     source                - IN
#     minIndexes            - OUT minimum value indexes
#     maxIndexes            - OUT maximum value indexes
#     (discardedMinIndexes) - OUT minimum value indexes retroactively discarded over time
#     (discardedMaxIndexes) - OUT maximum value indexes retroactively discarded over time

@final
class FractalExOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            width = params.get("width", 5)
            halfWidth = int((int(width) - 1) / 2)
            if halfWidth < 1:
                raise ParamError(f"Invalid width value ({width})")
            self._halfWidth = halfWidth
    
            threshold = params.get("threshold", 0.0)
            if threshold < 0.0:
                raise ParamError(f"Invalid threshold value ({threshold})")
            self._threshold = threshold

            minMaxLag = params.get("minMaxLag", 10)
            if minMaxLag < 0:
                raise ParamError(f"Invalid lag value ({lag})")
            self._minMaxLag = minMaxLag
        except Exception as e:
            raise ParamError(e) from e

        self._source = Stream(streams["source"])
        self._minIndexes = Stream(streams["minIndexes"])
        self._maxIndexes = Stream(streams["maxIndexes"])

        self._discardedMinIndexes = Stream(streams.get("discardedMinIndexes"))
        self._discardedMaxIndexes = Stream(streams.get("discardedMaxIndexes"))

        self._min = Stream()
        self._max = Stream()

        self._minMaxOperator = MinMaxOperator(
            params = {
                "lag": self._minMaxLag,
            },
            streams = {
                "source": self._source,
                "min": self._min,
                "max": self._max
            }
        )

        self._prev = None
        self._sign = None
        self._signCount = None
        self._trend = None
        self._prevTrend = None

    def calc(self):
        self._minMaxOperator.calc()

        for i, x in self._source.indexed():
            if x is None or self._prev is None:
                self._sign = None
                self._signCount = None
                self._trend = None
                self._prevTrend = None
            else:
                dx = x - self._prev
                if dx > 0:
                    sign = 1
                elif dx < 0:
                    sign = -1
                else:
                    sign = 0

                if sign == self._sign:
                    self._signCount += 1
                else:
                    self._sign = sign
                    self._signCount = 1
                    self._prevTrend = self._trend
                    self._trend = None

                if self._sign != self._trend and self._signCount >= self._halfWidth:
                    iStart = i - self._signCount
                    xStart = self._source[iStart]

                    if abs(x - xStart) >= self._threshold:
                        if self._prevTrend in [-1, 1]:
                            j = max(0, i - self._minMaxLag)
                            if self._sign == 1:
                                if xStart <= self._min[iStart]:
                                    if self._minIndexes and self._minIndexes[-1] >= j:
                                        self._discardedMinIndexes.append(self._minIndexes[-1])
                                        self._minIndexes[-1] = iStart
                                    else:
                                        self._minIndexes.append(iStart)
                            elif self._sign == -1:
                                if xStart >= self._max[iStart]:
                                    if self._maxIndexes and self._maxIndexes[-1] >= j:
                                        self._discardedMaxIndexes.append(self._maxIndexes[-1])
                                        self._maxIndexes[-1] = iStart
                                    else:
                                        self._maxIndexes.append(iStart)

                        self._trend = self._sign

            self._prev = x

# Channel-based peak detector.
#
# Params:
#     (midLag)   - ChannelOperator parameter
#     (boundLag) - ChannelOperator parameter
#     (isSymm)   - ChannelOperator parameter
#     (boost)    - ChannelOperator parameter
#
# Streams:
#     source     - IN
#     minIndexes - OUT minimum value indexes
#     maxIndexes - OUT maximum value indexes
#
# Debug streams:
#     (upper)    - OUT ChannelOperator output
#     (lower)    - OUT ChannelOperator output
#     (mid)      - OUT ChannelOperator output

@final
class ChannelBurstOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._source = FilterStream(streams["source"])
        self._maxIndexes = FilterStream(streams["maxIndexes"])
        self._minIndexes = FilterStream(streams["minIndexes"])

        self._upper = FilterStream(streams.get("upper"))
        self._lower = FilterStream(streams.get("lower"))
        self._mid = FilterStream(streams.get("mid"))

        self._channelOperator = ChannelOperator(
            params = mapDict(params, {
                "midLag": "midLag",
                "boundLag": "boundLag",
                "isSymm": "isSymm",
                "boost": "boost"
            }),
            streams = {
                "source": self._source,
                "upper": self._upper,
                "lower": self._lower,
                "mid": self._mid
            }
        )

        self._flip = None
        self._iPeak = None
        self._xPeak = None

    def calc(self):
        self._channelOperator.calc()

        for x, upper, lower in zip(
            self._source, self._upper, self._lower,
            strict = True
        ):
            flip = None
            if x is not None:
                if upper is not None and x > upper:
                    flip = True
                elif lower is not None and x < lower:
                    flip = False
    
            if flip != self._flip:
                if self._iPeak is not None:
                    if self._flip == False:
                        self._minIndexes.append(self._iPeak)
                    elif self._flip == True:
                        self._maxIndexes.append(self._iPeak)
                self._iPeak = None
                self._xPeak = None
                self._flip = flip
    
            if x is not None and (
                self._xPeak is None
                or (self._flip == True and x > self._xPeak)
                or (self._flip == False and x < self._xPeak)
            ):
                self._iPeak = i
                self._xPeak = x

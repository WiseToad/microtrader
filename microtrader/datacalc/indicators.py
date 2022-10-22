from typing import final
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from lib.utils import mapDict
from datacalc.stream import Stream
from datacalc.compound import *
from datacalc.basicmaps import *
from datacalc.basicops import *
from datacalc.filtermaps import *

# Simple Moving Average.
#
# Params:
#     (lag = 9) - sample count for smoothing
#
# Streams:
#     source    - IN
#     target    - OUT

@final
class SmaOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            lag = params.get("lag", 9)
            if lag < 1:
                raise ParamError(f"Invalid lag value ({lag})")
            self._lag = lag
        except Exception as e:
            raise ParamError(e) from e

        self._source = Stream(streams["source"])
        self._target = Stream(streams["target"])

        self._movingSum = 0.0
        self._movingCount = 0

    def calc(self):
        for i, a in self._source.indexed():
            if a is not None:
                self._movingSum += a
                self._movingCount += 1

            j = i - self._lag
            b = self._source[j] if j >= 0 else None
            if b is not None:
                self._movingSum -= b
                self._movingCount -= 1
                assert self._movingCount >= 0

            self._target.append(
                None if self._movingCount <= 0
                else self._movingSum / self._movingCount
            )

# Exponential Moving Average.
#
# Params:
#     (lag = 9) - sample count for smoothing
#
# Streams:
#     source    - IN
#     target    - OUT

@final
class EmaOperator: 

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            lag = params.get("lag", 9)
            if lag < 1:
                raise ParamError(f"Invalid lag value ({lag})")
            alpha = 2.0 / (lag + 1.0)
        except Exception as e:
            raise ParamError(e) from e

        self._loPassMapper = loPassMapper(streams["source"], alpha)
        self._target = Stream(streams["target"])

    def calc(self):
        self._target.extend(self._loPassMapper)

# Kaufman's Effective Ratio.
#
# Params:
#     (lag = 10) - sample count for ER calculation
#
# Streams:
#     source     - IN
#     ker        - OUT

@final
class KerOperator: 

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            lag = params.get("lag", 10)
            if lag < 1:
                raise ParamError(f"Invalid lag value ({lag})")
            self._lag = lag
        except Exception as e:
            raise ParamError(e) from e

        self._source = Stream(streams["source"])
        self._ker = Stream(streams["ker"])

        self._aPrev = None
        self._bPrev = None
        self._movingVolatility = 0.0

    def calc(self):
        for i, a in self._source.indexed():
            if a is not None and self._aPrev is not None:
                self._movingVolatility += abs(a - self._aPrev)
            self._aPrev = a

            j = i - self._lag
            b = self._source[j] if j >= 0 else None
            if b is not None and self._bPrev is not None:
                self._movingVolatility -= abs(b - self._bPrev)
            self._bPrev = b

            if a is None or b is None:
                y = None
            else:
                try:
                    y = abs(a - b) / self._movingVolatility
                except ZeroDivisionError:
                    y = 1.0
            self._ker.append(y)

# Kaufman's Adaptive Moving Average.
#
# Params:
#     (kerLag = 10)  - sample count for ER calculation
#     (fastLag = 2)  - sample count for non-volatile ("clean") markets with ER -> 1
#     (slowLag = 30) - sample count for volatile ("noisy") markets with ER -> 0
#
# Streams:
#     source         - IN
#     target         - OUT
#     (ker)          - OUT

@final
class KamaOperator: 

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            kerLag = params.get("kerLag", 10)

            fastLag = params.get("fastLag", 2)
            if fastLag < 1:
                raise ParamError(f"Invalid fastLag value ({fastLag})")

            slowLag = params.get("slowLag", 30)
            if slowLag < 1:
                raise ParamError(f"Invalid slowLag value ({slowLag})")

            if fastLag > slowLag:
                raise ParamError(f"fastLag value ({fastLag}) is greater than slowLag value ({slowLag})")

            self._fastAlpha = 2.0 / (fastLag + 1.0)
            self._slowAlpha = 2.0 / (slowLag + 1.0)
        except Exception as e:
            raise ParamError(e) from e

        self._ker = Stream(streams.get("ker"))
        self._alpha = Stream()

        self._kerOperator = KerOperator(
            params = {
                "lag": kerLag
            },
            streams = {
                "source": streams["source"],
                "ker": self._ker
            }
        )
        self._finalOperator = VariadicLoPassOperator(
            params = {},
            streams = {
                "alpha": self._alpha,
                "source": streams["source"],
                "target": streams["target"]
            }
        )

    def calc(self):
        self._kerOperator.calc()

        self._alpha.extend(
            None if ker is None
            else self._slowAlpha + ker * (self._fastAlpha - self._slowAlpha)
            for ker in self._ker
        )

        self._finalOperator.calc()

# Relative Strength Index.
#
# Params:
#     (lag = 14)
#
# Streams:
#     source - IN
#     target - OUT

@final
class RsiOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            lag = params.get("lag", 14)
            if lag < 1:
                raise ParamError(f"Invalid lag value ({lag})")
            alpha = 1.0 / lag
        except Exception as e:
            raise ParamError(e) from e

        self._source = Stream(streams["source"])
        self._target = Stream(streams["target"])

        self._uMa = Stream()
        self._dMa = Stream()

        self._udMaOperator = CompoundOperator(
            configs = [
                OperatorConfig(
                    mapperOperator(deltaMapper),
                    streamMap = {
                        "source": "source",
                        "target": "delta"
                    }
                ),
                OperatorConfig(
                    HwSplitOperator,
                    streamMap = {
                        "source": "delta",
                        "positive": "u",
                        "negative": "d"
                    }
                ),
                OperatorConfig(
                    mapperOperator(loPassMapper),
                    paramMap = {
                        "alpha": "alpha"
                    },
                    streamMap = {
                        "source": "u",
                        "target": "uMa"
                    }
                ),
                OperatorConfig(
                    mapperOperator(loPassMapper),
                    paramMap = {
                        "alpha": "alpha"
                    },
                    streamMap = {
                        "source": "d",
                        "target": "dMa"
                    }
                )
            ],
            params = {
                "alpha": alpha
            }, 
            streams = {
                "source": self._source,
                "uMa": self._uMa,
                "dMa": self._dMa
            }
        )

    def calc(self):
        self._udMaOperator.calc()

        for uMa, dMa in zip(
            self._uMa, self._dMa,
            strict = True
        ):
            if uMa is None or dMa is None:
                rsi = None
            else:
                try:
                    rsi = 100.0 * uMa / (uMa - dMa)
                except ZeroDivisionError:
                    rsi = 50.0
            self._target.append(rsi)

# Moving Average Convergence/Divergence.
#
# Params:
#     (shortLag = 12) 
#     (longLag = 26)
#     (diffLag = 9)
#
# Streams:
#     source - IN
#     target - OUT

@final
class MacdOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._operator = CompoundOperator(
            configs = [
                OperatorConfig(
                    EmaOperator,
                    paramMap = {
                        "lag": "shortLag"
                    },
                    streamMap = {
                        "source": "source",
                        "target": "shortEma"
                    }
                ),
                OperatorConfig(
                    EmaOperator,
                    paramMap = {
                        "lag": "longLag"
                    },
                    streamMap = {
                        "source": "source",
                        "target": "longEma"
                    }
                ),
                OperatorConfig(
                    DiffOperator,
                    streamMap = {
                        "source1": "shortEma",
                        "source2": "longEma",
                        "target": "diff"
                    }
                ),
                OperatorConfig(
                    EmaOperator,
                    paramMap = {
                        "lag": "diffLag"
                    },
                    streamMap = {
                        "source": "diff",
                        "target": "target"
                    }
                )
            ],
            params = {
                "shortLag": 12,
                "longLag": 26,
                "diffLag": 9
            } | params,
            streams = mapDict(streams, {
                "source": "source",
                "target": "target"
            })
        )

    def calc(self):
        self._operator.calc()

# Channel outliner.
#
# Params:
#     (midLag = 30)    - sample count for middle line smoothing
#     (boundLag = 10)  - sample count for upper/lower bound smoothing
#     (isSymm = False) - are bounds symmetric about mid line
#     (boost = 1.0)    - boost for distance from middle line to bounds
#
# Streams:
#     source           - IN
#     upper            - OUT upper channel bound
#     lower            - OUT lower channel bound
#     (mid)            - OUT mid line of channel

@final
class ChannelOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        try:
            midLag = params.get("midLag", 30)
            if midLag < 1:
                raise ParamError(f"Invalid midLag value ({midLag})")
            midAlpha = 1.0 / midLag
            hiAlpha = (midLag - 1.0) / midLag

            boundLag = params.get("boundLag", 10)
            if boundLag < 1:
                raise ParamError(f"Invalid boundLag value ({boundLag})")
            boundAlpha = 1.0 / boundLag

            self._isSymm = params.get("isSymm", False)
                        
            boost = params.get("boost", 1.0)
            if boost < 0.0:
                raise ParamError(f"Invalid boost value ({boost})")
            self._boost = boost
        except Exception as e:
            raise ParamError(e) from e

        self._upper = Stream(streams["upper"])
        self._lower = Stream(streams["lower"])
        self._mid = Stream(streams.get("mid"))

        self._pos = Stream()
        self._neg = Stream()

        self._preOperator = CompoundOperator(
            configs = [
                OperatorConfig(
                    mapperOperator(loPassMapper),
                    paramMap = {
                        "alpha": "midAlpha"
                    },
                    streamMap = {
                        "source": "source",
                        "target": "mid"
                    }
                ),
                OperatorConfig(
                    mapperOperator(hiPassMapper),
                    paramMap = {
                        "alpha": "hiAlpha"
                    },
                    streamMap = {
                        "source": "source",
                        "target": "hi"
                    }
                ),
                OperatorConfig(
                    HwSplitOperator,
                    streamMap = {
                        "source": "hi",
                        "positive": "hiPos",
                        "negative": "hiNeg"
                    }
                ),
                OperatorConfig(
                    mapperOperator(loPassMapper),
                    paramMap = {
                        "alpha": "boundAlpha"
                    },
                    streamMap = {
                        "source": "hiPos",
                        "target": "pos"
                    }
                ),
                OperatorConfig(
                    mapperOperator(loPassMapper),
                    paramMap = {
                        "alpha": "boundAlpha"
                    },
                    streamMap = {
                        "source": "hiNeg",
                        "target": "neg"
                    }
                )
            ],
            params = {
                "midAlpha": midAlpha,
                "hiAlpha": hiAlpha,
                "boundAlpha": boundAlpha
            }, 
            streams = {
                "source": streams["source"],
                "mid": self._mid,
                "pos": self._pos,
                "neg": self._neg
            }
        )

    def calc(self):
        self._preOperator.calc()

        for mid, pos, neg in zip(
            self._mid, self._pos, self._neg,
            strict = True
        ):
            if mid is None:
                self._upper.append(None)
                self._lower.append(None)
            else:
                if self._isSymm:
                    if pos is None or neg is None:
                        pos, neg = None, None
                    else:
                        pos, neg = (pos - neg) / 2.0, (neg - pos) / 2.0
    
                self._upper.append(
                    None if pos is None
                    else mid + self._boost * pos
                )
    
                self._lower.append(
                    None if pos is None
                    else mid + self._boost * neg
                )

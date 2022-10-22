from typing import final
from functools import partial
from inspect import getfullargspec
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from datacalc.stream import Stream

# Wrapper for mapper to transform it into operator.
#
# Params:
#     mapper input arguments except "self", "source" and "retroactor"
#
# Sources:
#     source
#
# Targets:
#     target

def mapperOperator(mapperType):
    return partial(MapperOperator, mapperType)

@final
class MapperOperator:

    @initconfig
    @throwingmember
    def __init__(self, mapperType, params, sources, targets):
        argNames = getfullargspec(mapperType).args
        args = {
            "source": sources["source"]
        } | {
            argName: params[argName]
            for argName in argNames
            if argName in params and argName not in ("self", "source", "retroactor")
        }
        if "retroactor" in argNames:
            args["retroactor"] = self._onRetroaction

        self._mapper = mapperType(**args)
        self._target = Stream(targets["target"])

    def calc(self):
        self._target.extend(self._mapper)

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._target.setLen(index)

# Half-wave splitter.
#
# Separates positive and negative half-waves of source.
#
# Sources:
#     source
#
# Targets:
#     positive
#     negative

@final
class HwSplitOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, sources, targets):
        self._source = Stream(sources["source"], self._onRetroaction)
        self._positive = Stream(targets["positive"])
        self._negative = Stream(targets["negative"])

    def calc(self):
        for x in self._source:
            self._positive.append(
                None if x is None
                else max(x, 0.0)
            )
            self._negative.append(
                None if x is None
                else min(x, 0.0)
            )

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._source.setPos(index)
            self._positive.setLen(index)
            self._negative.setLen(index)

# Simple low-pass RC filter driven by variadic alpha.
#
# Sources:
#     alpha
#     source
#
# Targets:
#     target

@final
class VariadicLoPassOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, sources, targets):
        self._alpha = Stream(sources["alpha"])
        self._source = Stream(sources["source"])
        self._target = Stream(targets["target"])

        self._y = None

    def calc(self):
        for x, alpha in zip(self._source, self._alpha, strict = True):
            if x is None or alpha is None or alpha < 0.0 or alpha > 1.0:
                self._y = None
            else:
                self._y = (
                    x if self._y is None
                    else self._y + alpha * (x - self._y)
                )
            self._target.append(self._y)

# Difference calculator.
#
# Sources:
#     source1
#     source2
#
# Targets:
#     target

@final
class DiffOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, sources, targets):
        self._source1 = Stream(sources["source1"], self._onRetroaction)
        self._source2 = Stream(sources["source2"], self._onRetroaction)
        self._target = Stream(targets["target"])

    def calc(self):
        self._target.extend(
            x1 - x2
            for x1. x2 in zip(
                self._source1, self._source2,
                strict = True
            )
        )

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._source1.setPos(index)
            self._source2.setPos(index)
            self._target.setLen(index)

# Multiplexer.
#
# Forwards specified source to target.
#
# Params:
#     sourceName - source stream name to forward to target
#
# Sources:
#     ...
#
# Targets:
#     target

@final
class MultilpexerOperator:

    @initconfig
    @throwingmember
    def __init__(self, params, sources, targets):
        try:
            self._source = Stream(
                sources[params["sourceName"]],
                self._onRetroaction
            )
        except Exception as e:
            raise ParamError(e) from e

        self._target = Stream(targets["target"])

    def calc(self):
        self._target.extend(self._source)

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._source.setPos(index)
            self._target.setLen(index)

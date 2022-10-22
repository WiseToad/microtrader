from typing import final
from types import MappingProxyType
from lib.decors import initconfig, throwingmember
from lib.utils import mapDict, coalesce
from datacalc.stream import Stream

@final
class OperatorConfig:

    def __init__(self, operatorType, paramMap = None, sourceMap = None, targetMap = None):
        self._operatorType = operatorType
        self._paramMap = coalesce(paramMap, {})
        self._sourceMap = coalesce(sourceMap, {})
        self._targetMap = coalesce(targetMap, {})

    @property
    def operatorType(self):
        return self._operatorType

    @property
    def paramMap(self):
        return MappingProxyType(self._paramMap)

    @property
    def sourceMap(self):
        return MappingProxyType(self._sourceMap)

    @property
    def targetMap(self):
        return MappingProxyType(self._targetMap)

# Compound operator.
#
# Elements within compound operator may be interconnected and interacting
# with each other by specifying source/target streams with equal names.
# But this is not mandatory though.

@final
class CompoundOperator:

    @initconfig
    @throwingmember
    def __init__(self, configs, params, sources, targets):
        sources = {
            sourceName: Stream(sources.get(sourceName))
            for config in configs
            for sourceName in config.sourceMap.values()
        }
        targets = {
            targetName: Stream(targets.get(targetName))
            for config in configs
            for targetName in config.targetMap.values()
        }
        
        self._operators = [
            config.operatorType(
                params = mapDict(params, config.paramMap),
                sources = mapDict(sources, config.sourceMap)
                targets = mapDict(targets, config.targetMap)
            )
            for config in configs
        ]

    def calc(self):
        for operator in self._operators:
            operator.calc()

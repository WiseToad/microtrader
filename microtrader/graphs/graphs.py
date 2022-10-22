from typing import final
from types import MappingProxyType
from enum import Enum
from fnmatch import fnmatch
from lib.exceptions import ParamError
from lib.decors import initconfig, throwingmember
from lib.utils import mergeDefaults, coalesce
from datacalc.valuestream import ValueStream
from datacalc.compound import CompoundOperator

@final
class GraphType(Enum):
    LINE = 1       # линии
    HISTOGRAM = 2  # гистограммы
    CANDLES = 3    # свечи
    BARS = 4       # бары
    DOTTED = 5     # точки
    DOT_DASHED = 6 # пунктир-точка
    DASHED = 7     # пунктир
    PEAK_UP = 10   # треугольник вверх
    PEAK_DOWN = 11 # треугольник вниз

@final
class GraphConfig:

    def __init__(self, name, title = None, graphType = None):
        self._name = name
        self._title = coalesce(title, name)
        self._graphType = coalesce(graphType, GraphType.LINE)

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def graphType(self):
        return self._graphType

@final
class ProcessorConfig:

    def __init__(self, name, graphConfigs, operatorConfigs, defaultParams = None, constantParams = None):
        self._name = name
        self._graphConfigs = graphConfigs
        self._operatorConfigs = operatorConfigs
        self._defaultParams = coalesce(defaultParams, {})
        self._constantParams = coalesce(constantParams, {})

    @property
    def name(self):
        return self._name

    @property
    def graphConfigs(self):
        return tuple(self._graphConfigs)

    @property
    def operatorConfigs(self):
        return tuple(self._operatorConfigs)

    @property
    def defaultParams(self):
        return MappingProxyType(self._defaultParams)

    @property
    def constantParams(self):
        return MappingProxyType(self._constantParams)

@final
class ProcessorConfigs:

    _configs = {}

    @staticmethod
    def add(config):
        configName = config.name
        if configName in ProcessorConfigs._configs:
            raise RuntimeError(f"Config with such name already exists ({configName})")
        ProcessorConfigs._configs[configName] = config

    @staticmethod
    def get(configName):
        return ProcessorConfigs._configs[configName]

@final
class Processor:

    @initconfig
    @throwingmember
    def __init__(self, config, params, sources):
        self._configName = config.name

        try:
            self._params = config.constantParams | mergeDefaults(params, config.defaultParams)
        except Exception as e:
            raise ParamError(e) from e

        self._sources = [
            sourceName: ValueStream(source)
            for sourceName, source in sources.items()
        ]

        graphNames = [graphConfig.name for graphConfig in config.graphConfigs]

        # Dict with all unique streams of input and graph data
        self._streams = {
            graphName: ValueStream()
            for graphName in graphNames
        } | self._sources

        for stream in self._streams:
            stream.setRetroactor(
                partial(self.onRetroaction, stream = stream)
            )

        graphGlobs = {
            graphGlob.strip()
            for graphGlob in self._params.get("(Graphs)", "").split(",")
            if graphGlob.strip()
        }
        enabledGraphs = {
            graphGlob
            for graphGlob in graphGlobs
            if graphGlob[0] != "-"
        }
        disabledGraphs = {
            graphGlob.lstrip("- ")
            for graphGlob in graphGlobs
            if graphGlob[0] == "-"
        }

        # List with only graph data streams, with preserved number and order of graphs
        self._graphStreams = [
            self._streams[graphName]
            if (not enabledGraphs or any(fnmatch(graphName, graphGlob) for graphGlob in enabledGraphs))
                and not any(fnmatch(graphName, graphGlob) for graphGlob in disabledGraphs)
            else None
            for graphName in graphNames            
        ]

        self._operators = CompoundOperator(
            config.operatorConfigs,
            self._params,
            self._streams
        )

    def getConfigName(self):
        return self._configName

    def getSources(self):
        return self._sources

    def calc(self):
        if len(price) != len(volume) != len(time):
            raise ParamError("Input data chunks are of different lengths")

        starts = set(len(stream) for stream in self._streams.values())
        assert len(starts) == 1
        start = starts.pop()
        
        self._price.extend(price)
        self._volume.extend(volume)
        self._time.extend(time)

        for stream in self._streams.values():
            stream.setPos(start)
            
        self._operators.calc()

        if len(set(len(stream) for stream in self._streams.values())) > 1:
            raise RuntimeError("Some of data streams get out of sync")

        return [
            None if graphStream is None
            else [graphStream.getPos() - start] + graphStream[graphStream.getPos():]
            for graphStream in self._graphStreams
        ]

    def _onRetroaction(self, change, index, stream):
        if change.isAfter():
            stream.setPos(index)

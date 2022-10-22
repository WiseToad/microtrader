from graphs.graphs import *
from datacalc.minmaxops import *
from datacalc.indexops import *

grapherConfigs.append(
    GrapherConfig(
        name = "sandbox",
        graphConfigs = [
            GraphConfig("MovingMax"),
            GraphConfig("MovingMin"),
            GraphConfig("Maxs", graphType = GraphType.PEAK_UP),
            GraphConfig("Mins", graphType = GraphType.PEAK_DOWN),
            GraphConfig("DiscardedMaxs", graphType = GraphType.PEAK_UP),
            GraphConfig("DiscardedMins", graphType = GraphType.PEAK_DOWN)
        ],
        operatorConfigs = [
            OperatorConfig(
                MinMaxOperator,
                paramMap = {
                    "lag": "m3Lag"
                },
                streamMap = {
                    "source": "Price",
                    "max": "MovingMax",
                    "min": "MovingMin"
                }
            ),
            OperatorConfig(
                FractalExOperator,
                paramMap = {
                    "width": "peakWidth",
                    "threshold": "peakThreshold",
                    "relThreshold": "peakRelThreshold",
                    "m3Lag": "m3Lag"
                },
                streamMap = {
                    "source": "Price",
                    "maxIndexes": "maxIndexes",
                    "minIndexes": "minIndexes",
                    "discardedMaxIndexes": "discardedMaxIndexes",
                    "discardedMinIndexes": "discardedMinIndexes"
                }
            ),
            OperatorConfig(
                PickOperator,
                streamMap = {
                    "source": "Price",
                    "indexes": "maxIndexes",
                    "target": "Maxs"
                }
            ),
            OperatorConfig(
                PickOperator,
                streamMap = {
                    "source": "Price",
                    "indexes": "minIndexes",
                    "target": "Mins"
                }
            ),
            OperatorConfig(
                PickOperator,
                streamMap = {
                    "source": "Price",
                    "indexes": "discardedMaxIndexes",
                    "target": "DiscardedMaxs"
                }
            ),
            OperatorConfig(
                PickOperator,
                streamMap = {
                    "source": "Price",
                    "indexes": "discardedMinIndexes",
                    "target": "DiscardedMins"
                }
            )
        ],
        defaultParams = {
            "(Graphs)": "Maxs, Mins",

            # MinMaxOperator
            # FractalExOperator
            "m3Lag": 30,

            # FractalExOperator
            "peakWidth": 3,
            "peakThreshold": 0.0,
            "peakRelThreshold": 0.0
        }
    )
)

from graphs.graphs import GraphConfig
from filters.basicfilters import *
from filters.indicators import *
from filters.peaks import *
from filters.divergence import *
from filters.plotters import *
from trading.trader import Trader

class TradingGraphConfig(GraphConfig):

    _name = "trading"

    _graphDescrs = [
        {"name": "Price"},
        {"name": "PriceKama"},
        {"name": "Rsi"},
        {"name": "RsiKama"},

        {"name": "V1.discardedMaxs", "lineType": 10},
        {"name": "V1.discardedMins", "lineType": 11},
        {"name": "V2.discardedMaxs", "lineType": 10},
        {"name": "V2.discardedMins", "lineType": 11},

        {"name": "V1.maxLines", "lineType": 4},
        {"name": "V1.minLines", "lineType": 4},
        {"name": "V2.maxLines", "lineType": 4},
        {"name": "V2.minLines", "lineType": 4}
    ]

    _filterDescrs = [
        {
            "type": KamaFilter,
            "paramMap": {
                "erLag": "PriceKama.erLag",
                "fastLag": "PriceKama.fastLag",
                "slowLag": "PriceKama.slowLag"
            },
            "streamMap": {
                "source": "Price",
                "target": "PriceKama"
            }
        },

        {
            "type": RsiFilter,
            "paramMap": {
                "lag": "Rsi.lag"
            },
            "streamMap": {
                "source": "Price",
                "target": "Rsi"
            }
        },
        {
            "type": KamaFilter,
            "paramMap": {
                "erLag": "RsiKama.erLag",
                "fastLag": "RsiKama.fastLag",
                "slowLag": "RsiKama.slowLag"
            },
            "streamMap": {
                "source": "Rsi",
                "target": "RsiKama"
            }
        },

        {
            "type": FractalExFilter,
            "paramMap": {
                "width": "V1.peakWidth",
                "threshold": "V1.peakThreshold",
                "relThreshold": "V1.peakRelThreshold",
                "m3Lag": "V1.peakM3Lag"
            },
            "streamMap": {
                "source": "PriceKama",
                "maxIndexes": "V1.maxIndexes",
                "minIndexes": "V1.minIndexes",
                "discardedMaxIndexes": "V1.discardedMaxIndexes",
                "discardedMinIndexes": "V1.discardedMinIndexes"
            }
        },
        {
            "type": FractalExFilter,
            "paramMap": {
                "width": "V2.peakWidth",
                "threshold": "V2.peakThreshold",
                "relThreshold": "V2.peakRelThreshold",
                "m3Lag": "V2.peakM3Lag"
            },
            "streamMap": {
                "source": "RsiKama",
                "maxIndexes": "V2.maxIndexes",
                "minIndexes": "V2.minIndexes",
                "discardedMaxIndexes": "V2.discardedMaxIndexes",
                "discardedMinIndexes": "V2.discardedMinIndexes"
            }
        },

        {
            "type": DivergenceFilter,
            "paramMap": {
                "epsilon": "epsilon",
                "threshold1": "V1.slopeThreshold",
                "relThreshold1": "V1.slopeRelThreshold",
                "threshold2": "V2.slopeThreshold",
                "relThreshold2": "V2.slopeRelThreshold"
            },
            "streamMap": {
                "source1": "PriceKama",
                "maxIndexes1": "V1.maxIndexes",
                "minIndexes1": "V1.minIndexes",

                "source2": "RsiKama",
                "maxIndexes2": "V2.maxIndexes",
                "minIndexes2": "V2.minIndexes",

                "divergences": "divergences",

                "maxLineIndexes1": "V1.maxLineIndexes",
                "minLineIndexes1": "V1.minLineIndexes",
                "maxLineIndexes2": "V2.maxLineIndexes",
                "minLineIndexes2": "V2.minLineIndexes"
            }
        },

        {
            "type": PickFilter,
            "streamMap": {
                "source": "PriceKama",
                "indexes": "V1.discardedMaxIndexes",
                "target": "V1.discardedMaxs"
            }
        },
        {
            "type": PickFilter,
            "streamMap": {
                "source": "PriceKama",
                "indexes": "V1.discardedMinIndexes",
                "target": "V1.discardedMins"
            }
        },
        {
            "type": PickFilter,
            "streamMap": {
                "source": "RsiKama",
                "indexes": "V2.discardedMaxIndexes",
                "target": "V2.discardedMaxs"
            }
        },
        {
            "type": PickFilter,
            "streamMap": {
                "source": "RsiKama",
                "indexes": "V2.discardedMinIndexes",
                "target": "V2.discardedMins"
            }
        },

        {
            "type": LineFilter,
            "streamMap": {
                "lineIndexes": "V1.maxLineIndexes",
                "source": "PriceKama",
                "target": "V1.maxLines"
            }
        },
        {
            "type": LineFilter,
            "streamMap": {
                "lineIndexes": "V1.minLineIndexes",
                "source": "PriceKama",
                "target": "V1.minLines"
            }
        },
        {
            "type": LineFilter,
            "streamMap": {
                "lineIndexes": "V2.maxLineIndexes",
                "source": "RsiKama",
                "target": "V2.maxLines"
            }
        },
        {
            "type": LineFilter,
            "streamMap": {
                "lineIndexes": "V2.minLineIndexes",
                "source": "RsiKama",
                "target": "V2.minLines"
            }
        },

        {
            "type": Trader,
            "paramMap": {
                "classCode": "classCode",
                "secCode": "secCode"
            },
            "streamMap": {
                "price": "Price",
                "time": "Time",
                "divergences": "divergences"
            }
        }
    ]

    _defaultParams = {
        "(Graphs)": "PriceKama, V1.discardedMaxs, V1.discardedMins, V1.maxLines, V1.minLines",

        # KamaFilter
        "PriceKama.erLag": 10,
        "PriceKama.fastLag": 2,
        "PriceKama.slowLag": 30,

        # RsiFilter
        "Rsi.lag": 14,

        # KamaFilter
        "RsiKama.erLag": 10,
        "RsiKama.fastLag": 2,
        "RsiKama.slowLag": 30
    }

    _constantParams = {
        # FractalExFilter
        "V1.peakWidth": 3,
        "V1.peakThreshold": 0.0,
        "V1.peakRelThreshold": 0.0,
        "V1.peakM3Lag": 10,

        # FractalExFilter
        "V2.peakWidth": 3,
        "V2.peakThreshold": 0.0,
        "V2.peakRelThreshold": 0.0,
        "V2.peakM3Lag": 10,

        # DivergenceFilter
        "epsilon": 2,
        "V1.slopeThreshold": 0.0,
        "V1.slopeRelThreshold": 0.0,
        "V2.slopeThreshold": 0.0,
        "V2.slopeRelThreshold": 0.0
    }

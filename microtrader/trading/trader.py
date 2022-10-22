from typing import final
from lib.decors import initconfig, throwingmember
from datacalc.valuestream import ValueStream
from datacalc.divergence import *
from trading.orderrepo import OrderRepo

@final
class Trader:

    @initconfig
    @throwingmember
    def __init__(self, params, streams):
        self._classCode = params["classCode"]
        self._secCode = params["secCode"]
        
        self._price = ValueStream(streams["price"])
        self._time = ValueStream(streams["time"])
        self._divergences = ValueStream(streams["divergences"])

    def calc(self):
        for d in self._divergences:
            print(f"INFO:  Divergence detected: type={d.divergenceType} class={d.divergenceClass} time={self._time[d.index1]}")
            if (d.divergenceType == DivergenceType.DIVERGENCE
                and d.divergenceClass == DivergenceClass.A
            ):
                OrderRepo.add({
                    "TIME": self._time[d.index1],
                    "CLASSCODE": self._classCode,
                    "SECCODE": self._secCode,
                    "ACTION": "NEW_ORDER",
                    "OPERATION": 'B',
                    "PRICE": self._price[d.index1],
                    "QUANTITY": 1,
                    "TYPE": "L"
                })

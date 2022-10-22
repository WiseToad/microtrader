from typing import final

# Stock order repository.

@final
class OrderRepo:

    _orders = []
    _pos = 0

    @classmethod
    def add(cls, order):
        print(f"INFO:  Adding order: {order}")
        cls._orders.append(order)

    @classmethod
    def getNew(cls):
        pos = cls._pos
        cls._pos = len(cls._orders)
        return cls._orders[pos:]

from typing import final
from enum import Enum

@final
class StreamChange(Enum):
    TRUNCATING = 0
    TRUNCATE = 1
    RANDOM_WRITING = 2
    RANDOM_WRITE = 3

    def isBefore(self):
        return self in [
            StreamChange.TRUNCATING, 
            StreamChange.RANDOM_WRITING
        ]

    def isAfter(self):
        return self in [
            StreamChange.TRUNCATE,
            StreamChange.RANDOM_WRITE
        ]

# The wrapper around underlying values to read/write them.
#
# Each instance maintains current read position, needed for data exchange, performed
# chunk-by-chunk by successive read/write operations.
#
# Also, Stream class supports past data change handlers, to allow retroactive data
# processing within sophisticated systems of interconnected units.
#
# Underlying values must be subscriptable for both random and sequental read access
# via Stream instance. So, lists and Streams instances are suitable to be used as 
# underlying values, whereas generators are not.
#
# Stream instance can be wrapped by other instances of Stream, no matter how many
# times - each of these instances will have direct access to underlying values, with
# no excessive levels of wrapping.

@final
class Stream:

    @final
    class IndexedIter:
    
        def __init__(self, stream):
            self._stream = stream
    
        def __iter__(self):
            return self
    
        def __next__(self):
            try:
                return self._stream.getPos(), self._stream.getNext()
            except IndexError:
                raise StopIteration

    def __init__(self, values = None, retroactor = None):
        if type(values) == Stream:
            self._values = values._values
            self._streams = values._streams
            self._offset = values._offset
        else:
            self._values = values if values is not None else []
            self._streams = []
            self._offset = 0

        self._pos = 0
        self._streams.append(self)
        self._retroactor = retroactor

    def setRetroactor(self, retroactor):
        self._retroactor = retroactor

    def __del__(self):
        self._streams.remove(self)

    def __str__(self):
        return self._values.__str__()

    def __len__(self):
        return max(0, self._values.__len__() - self._offset)

    def __getitem__(self, index):
        return self._values.__getitem__(
            self._getValueIndex(index)
        )

    def __setitem__(self, index, value):
        index = self._getValueIndex(index)
        if value != self._values[index]:
            self._onValuesChange(StreamChange.RANDOM_WRITING, index)
            self._values.__setitem__(index, value)
            self._onValuesChange(StreamChange.RANDOM_WRITE, index)

    def _getValueIndex(self, index):
        if type(index) != int:
            raise IndexError(f"Unsupported index type ({type(index)})")
        index += (
            self._offset if index >= 0
            else len(self._values) 
        )
        if index < self._offset or index >= len(self._values):
            raise IndexError(f"Index is out of bounds of underlying values")
        return index

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.getNext()
        except IndexError:
            raise StopIteration

    def getNext(self):
        value = self._values[self._offset + self._pos]
        self._pos += 1
        return value

    def indexed(self):
        return Stream.IndexedIter(self)

    def append(self, value):
        self._values.append(value)

    def extend(self, values):
        self._values.extend(values)

    def setLen(self, newLen):
        if newLen < 0:
            raise IndexError(f"Invalid stream length ({len})")
        newLen += self._offset
        if newLen > len(self._values):
            self._values.extend([None] * (newLen - len(self._values)))
        elif newLen < len(self._values):
            self._onValuesChange(StreamChange.TRUNCATING, newLen)
            del self._values[newLen:]
            self._onValuesChange(StreamChange.TRUNCATE, newLen)

    def getOffset(self):
        return self._offset

    def setOffset(self, offset):
        if offset < 0:
            raise IndexError(f"Invalid stream offset ({offset})")
        self._offset = offset

    def getPos(self):
        return self._pos

    def setPos(self, pos):
        if pos < 0:
            raise IndexError(f"Invalid stream position ({pos})")
        self._pos = pos

    def _onValuesChange(self, change, index):
        index -= self._offset
        for stream in self._streams:
            if index < stream._pos:
                if stream._retroactor is None:
                    raise RuntimeError("Changing of already processed data")
                stream._retroactor(change, index)

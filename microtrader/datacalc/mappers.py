from datacalc.stream import Stream

class SimpleMapper:

    def __init__(self, source, transformer, retroactor = None):
        self._source = Stream(source)
        self._transformer = transformer
        self._retroactor = retroactor if type(retroactor) != bool else None
        if type(retroactor) != bool or retroactor:
            self._source.setRetroactor(self._onRetroaction)

    def __iter__(self):
        return (
            self._transformer(value) 
            for value in self._source
        )

    def peekSource(self, index):
        return self._source[index]

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._source.setPos(index)
        if self._retroactor is not None:
            self._retroactor(change, index)

class PrevAwareMapper(SimpleMapper):

    def __init__(self, source, transformer, retroactor = None):
        SimpleMapper.__init__(self, source, transformer, retroactor)
        self._prev = None

    def __iter__(self):
        for value in self._source:
            transformed = self._transformer(value, self._prev)
            self._prev = value
            yield transformed

    def _onRetroaction(self, change, index):
        if change.isAfter():
            self._prev = self._source[index - 1] if index > 0 else None
        SimpleMapper._onRetroaction(self, change, index)

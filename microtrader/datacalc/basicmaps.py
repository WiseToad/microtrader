from datacalc.mappers import SimpleMapper, PrevAwareMapper

# Value delta calculator.

def deltaMapper(source, retroactor = None):
    onTransform = lambda x, prev: (
        None if x is None or prev is None
        else x - prev
    )
    return PrevAwareMapper(source, onTransform, retroactor)

# Day bound detector.

def dayBoundMapper(source, retroactor = None):
    onTransform = lambda t, prev: (
        None if t is None or prev is None
        else t.date() != prev.date()
    )
    return PrevAwareMapper(source, onTransform, retroactor)

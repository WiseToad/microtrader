from datacalc.mappers import PrevAwareMapper

# Sequence validator

def sequenceValidator(source, verifier, errorMsg = None, retroactor = None):
    def onTransform(value, prev):
        if not verifier(value, prev):
            raise ValueError(
                errorMsg if errorMsg is not None
                else "Value is out of sequence"
            )
        return x

    return PrevAwareMapper(source, onTransform, retroactor)

# Increasing sequence validator

def increaseValidator(source, errorMsg = None, retroactor = None):
    onVerify = lambda value, prev: (
        value is None or prev is None
        or value > prev
    )
    return sequenceValidator(source, onVerify, errorMsg, retroactor)

# Non-decreasing sequence validator

def noDecreaseValidator(source, errorMsg = None, retroactor = None):
    onVerify = lambda value, prev: (
        value is None or prev is None
        or value >= prev
    )
    return sequenceValidator(source, onVerify, errorMsg, retroactor)

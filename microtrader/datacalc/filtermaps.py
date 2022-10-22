from lib.exceptions import ParamError
from datacalc.mappers import SimpleMapper, PrevAwareMapper

# Simple low-pass RC filter.
#
# Params:
#     (alpha) - smoothing factor
#     (rc)    - time constant
#
#     Either alpha or rc value should be specified.

def loPassMapper(source, alpha = None, rc = 10.0):
    try:
        if alpha is not None:
            if alpha < 0.0 or alpha > 1.0:
                raise ParamError(f"Invalid alpha value ({alpha})")
        else:
            if rc < 0.0:
                raise ParamError(f"Invalid rc value ({rc})")
            alpha = 1.0 / (rc + 1.0)
    except Exception as e:
        raise ParamError(e) from e

    y = None

    def onTransform(x):
        nonlocal y
        if x is None:
            y = None
        else:
            y = (
                x if y is None
                else y + alpha * (x - y)
            )
        return y

    return SimpleMapper(source, onTransform, False)

# Simple low-pass RC filter applied to value delta.
#
# Params:
#     (alpha) - smoothing factor
#     (rc)    - time constant
#
#     Either alpha or rc value should be specified.

def deltaLoPassMapper(source, alpha = None, rc = 10.0):
    try:
        if alpha is not None:
            if alpha < 0.0 or alpha > 1.0:
                raise ParamError(f"Invalid alpha value ({alpha})")
        else:
            if rc < 0.0:
                raise ParamError(f"Invalid rc value ({rc})")
            alpha = 1.0 / (rc + 1.0)
    except Exception as e:
        raise ParamError(e) from e

    y = None
    dy = None

    def onTransform(x):
        nonlocal y, dy
        if x is None or y is None:
            y = x
            dy = None
        else:
            d = x - y
            dy = (
                d if dy is None
                else dy + alpha * (d - dy)
            )
            y += dy
        return y

    return SimpleMapper(source, onTransform, False)

# Simple high-pass RC filter.
#
# Params:
#     (alpha) - smoothing factor
#     (rc)    - time constant
#
#     Either alpha or rc value should be specified.

def hiPassMapper(source, alpha = None, rc = 10.0):
    try:
        if alpha is not None:
            if alpha < 0.0 or alpha > 1.0:
                raise ParamError(f"Invalid alpha value ({alpha})")
        else:
            if rc < 0.0:
                raise ParamError(f"Invalid rc value ({rc})")
            alpha = rc / (rc + 1.0)
    except Exception as e:
        raise ParamError(e) from e

    y = None

    def onTransform(x, prev):
        nonlocal y
        if x is None or prev is None:
            y = None
        else:
            y = (
                0 if y is None
                else alpha * (y + (x - prev))
            )
        return y

    return PrevAwareMapper(source, onTransform, False)

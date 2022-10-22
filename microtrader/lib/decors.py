from functools import wraps
from lib.exceptions import ParamError, ConfigError

def throwingmember(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            raise type(e)(f"{type(self).__name__}: {e}") from e
    return wrapper

def throwingclass(func):
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        try:
            return func(cls, *args, **kwargs)
        except Exception as e:
            raise type(e)(f"{cls.__name__}: {e}") from e
    return wrapper

def initparams(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise ParamError(e) from e
    return wrapper

def initconfig(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ParamError as e:
            raise ParamError(e) from e
        except Exception as e:
            raise ConfigError(e) from e
    return wrapper

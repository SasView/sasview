from collections.abc import Callable

import numpy as np

# TODO: Proper typing when newer numpy (>1.20) is supported
ArrayLike = np.ndarray | float | int

def assure_vectorised_argument(f: Callable):
    """ Allow arguments to a function mapping numpy vectors
    that would otherwise strictly require numpy vectors,
    to accept and return floats
    """

    def wrapper(first_arg, *args, **kwargs):
        if isinstance(first_arg, (float, int)):
            return f(np.array([first_arg]), *args, **kwargs)[0]

        else:
            return f(first_arg, *args, **kwargs)

    return wrapper

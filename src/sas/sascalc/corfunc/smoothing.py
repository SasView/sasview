from collections import namedtuple
from collections.abc import Callable

import numpy as np

from sas.sascalc.corfunc.vectorisation import ArrayLike, assure_vectorised_argument

Cache = namedtuple("Cache", 'x, y')

class SmoothJoin:
    """
    Function that merges two functions, one on the left (small x),
    one on the right (high x) with a transition region inbetween,
    specified by [start, stop]


    :param left_hand_function: The first curve to interpolate
    :param right_hand_function: The second curve to interpolate
    :param start: The value at which to start the interpolation
    :param stop: The value at which to stop the interpolation
    """

    def __init__(self,
                 left_hand_function: Callable[[ArrayLike], ArrayLike],
                 right_hand_function: Callable[[ArrayLike], ArrayLike],
                 start: float,
                 stop: float):

        self.left_function = left_hand_function
        self.right_function = right_hand_function
        self.start = start
        self.stop = stop

        self._cache: Cache | None = None

    @assure_vectorised_argument
    def __call__(self, x: ArrayLike) -> ArrayLike:
        """
        Evaluate the combined functions at given x values.

        This works by using a convex combination of left and right functions,
        weighted by a sigmoidal function, over the central region.

        """


        # Check cache for previous result, otherwise do calculation
        if self._cache is None or not np.array_equal(x, self._cache.x):

            left_indices = x <= self.start
            right_indices = x >= self.stop

            mid_indices = \
                np.logical_not(
                    np.logical_or(
                        left_indices,
                        right_indices))

            y = np.zeros(x.shape)

            y[left_indices] = self.left_function(x[left_indices])
            y[right_indices] = self.right_function(x[right_indices])

            # Use np.divide
            x_mid = x[mid_indices]

            # This shouldn't have any divide by zero, as x_mid is strictly bigger than start
            # and strictly less than stop
            h = 1.0 / (1.0 + ((x_mid - self.stop) / (self.start - x_mid)) ** 2)

            y[mid_indices] = h * self.right_function(x_mid) + \
                             (1 - h) * self.left_function(x_mid)

            self._cache = Cache(x, y)

        return self._cache.y


def show_smoothing_function():
    """ Local sanity-check plots for the joiner"""
    import matplotlib.pyplot as plt

    xs = np.linspace(0, 10, 100)
    plt.plot(xs, SmoothJoin(lambda x: 0.0, lambda x: 1.0, 2, 8)(xs))

    plt.show()


def main():
    show_smoothing_function()


if __name__ == "__main__":
    main()




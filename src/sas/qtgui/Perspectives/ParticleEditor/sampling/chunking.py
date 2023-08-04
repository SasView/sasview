

"""

Functions designed to help avoid using too much memory, chunks up the pairwise distributions

Something like this



                 First Point

       1   2   3 | 4   5   6 | 7   8   9 | 0
   1             |           |           |
S                |           |           |
e  2   CHUNK 1   |  CHUNK 2  |  CHUNK 3  | CHUNK 4
c                |           |           |
o  3             |           |           |
n ---------------+-----------+-----------+------------
d  4             |           |           |
                 |           |           |
P  5   CHUNK 5   |  CHUNK 6  | CHUNK 7   | CHUNK 8
o                |           |           |
i  6             |           |           |
n ---------------+-----------+-----------+------------
t  7             |           |           |
                 |           |           |
   8   CHUNK 9   | CHUNK 10  | CHUNK 11  |  CHUNK 12
                 |           |           |
   9             |           |           |
  ---------------+-----------+-----------+------------
   0             |           |           |
      CHUNK 13   | CHUNK 14  | CHUNK 15  |  CHUNK 16
                 |           |           |
"""


from typing import Tuple, Sequence, Any

import math

from sas.qtgui.Perspectives.ParticleEditor.sampling.points import PointGenerator
from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import VectorComponents3

from abc import ABC, abstractmethod


class Chunker(ABC):
    def __init__(self, point_generator: PointGenerator):
        self.point_generator = point_generator

    def __iter__(self):
        return self._iterator

    @abstractmethod
    def _iterator(self) -> Tuple[VectorComponents3, VectorComponents3]:
        """ Python generator function that yields chunks """


class Chunks(Chunker):
    """ Class that takes a point generator, and produces all pairwise combinations in chunks

    This trades off speed for space.
    """

    # TODO


class SingleChunk(Chunker):
    """ Chunker that doesn't chunk """

    def _iterator(self):
        points = self.point_generator.generate(0, self.point_generator.n_points)
        yield points, points


class InputLengthMismatch(Exception):
    pass

def sublist_lengths(data: Sequence[Sequence[Any]]) -> int:
    """ Return the length of the """
    iterator = iter(data)
    len_0 = len(next(iterator))
    if not all(len(x) == len_0 for x in iterator):
        raise InputLengthMismatch("Input lists do not have the same length")

    return len_0
def pairwise_chunk_iterator(
        left_data: Sequence[Sequence[Any]],
        right_data: Sequence[Sequence[Any]],
        chunk_size: int) -> Tuple[Sequence[Sequence[Any]], Sequence[Sequence[Any]]]:

    """ Generator to do chunking as described in the module docs above"""

    left_len = sublist_lengths(left_data)
    right_len = sublist_lengths(right_data)

    n_left = math.ceil(left_len / chunk_size)
    n_right = math.ceil(right_len / chunk_size)

    for i in range(n_left):

        left_index_1 = i*chunk_size
        left_index_2 = min(((i+1)*chunk_size, n_left))

        left_chunk = (datum[left_index_1:left_index_2] for datum in left_data)

        for j in range(n_right):

            right_index_1 = j*chunk_size
            right_index_2 = min(((i+1)*chunk_size, n_left))

            right_chunk = (datum[right_index_1:right_index_2] for datum in right_data)

            yield left_chunk, right_chunk

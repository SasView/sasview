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


def pairwise_chunk_iterator(left_data: Sequence[Sequence[Any]], right_data: Sequence[Sequence[Any]]) -> Tuple[Sequence[Any], Sequence[Any]]:
    """ Generator to do chunking"""
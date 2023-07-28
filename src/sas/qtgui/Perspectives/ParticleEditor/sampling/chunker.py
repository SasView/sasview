from typing import Tuple

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

    #TODO


class NoChunks(Chunker):

    def _iterator(self):
        points = self.point_generator.generate(0, self.point_generator.n_points)
        yield points, points
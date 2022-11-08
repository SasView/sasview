from typing import Sequence, Tuple, Union
from abc import abstractmethod

import numpy as np

from sas.qtgui.GL.Renderable import Renderable
from sas.qtgui.GL.Color import Color


class SolidModel(Renderable):
    """ Base class for the two solid models"""
    @property
    def solid_render_enabled(self) -> bool:
        return True

    @abstractmethod
    @property
    def vertices(self) -> Sequence[Tuple[float, float, float]]:
        pass

    @abstractmethod
    @property
    def meshes(self) -> Sequence[Sequence[Sequence[int]]]:
        pass


class SolidVertexModel(SolidModel):

    @abstractmethod
    @property
    def vertex_colors(self) -> Union[Sequence[Color], Color]:
        pass

    def render_solid(self):
        pass

class SolidFaceModel(SolidModel):

    @abstractmethod
    @property
    def face_colours(self) -> np.ndarray:
        pass

    def render_solid(self):
        pass


from abc import abstractmethod

import numpy as np

from sas.qtgui.GL.Renderable import Renderable

class WireModel(Renderable):

    @abstractmethod
    @property
    def vertices(self) -> np.ndarray:
        pass

    @abstractmethod
    @property
    def edges(self) -> np.ndarray:
        pass

    @abstractmethod
    @property
    def edge_colors(self) -> np.ndarray:
        pass
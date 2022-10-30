from abc import ABC, abstractmethod

import numpy as np

class WireModel(ABC):

    @abstractmethod
    @property
    def vertices(self) -> np.ndarray:
        pass

    @abstractmethod
    @property
    def edges(self) -> np.ndarray:
        pass
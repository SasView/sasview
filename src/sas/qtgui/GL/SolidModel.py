from abc import ABC, abstractmethod

import numpy as np

class SolidModel(ABC):

    @abstractmethod
    @property
    def vertices(self) -> np.ndarray:
        pass

    @abstractmethod
    @property
    def faces(self) -> np.ndarray:
        pass
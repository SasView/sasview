from typing import Dict
from abc import ABC, abstractmethod

class Particle(ABC):
    def __init__(self, max_radius):
        self.max_radius = max_radius

    @abstractmethod
    def xyz_evaluate(self, x, y, z, parameters: Dict[str, float]):
        pass

class CartesianParticle(Particle):
    def __init__(self, max_radius):
        super().__init__(max_radius)

    def xyz_evaluate(self, x, y, z, parameters: Dict[str, float]):
        pass
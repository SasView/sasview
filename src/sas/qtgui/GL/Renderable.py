from abc import ABC, abstractmethod

class Renderable(ABC):
    """ Interface for everything that can be rendered with the OpenGL widget"""

    @abstractmethod
    def render_wireframe(self):
        pass

    @abstractmethod
    def render_solid(self):
        pass
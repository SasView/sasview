from abc import ABC, abstractmethod

import logging

logger = logging.getLogger("GL Subsystem")

class Renderable(ABC):
    """ Interface for everything that can be rendered with the OpenGL widget"""

    def render_wireframe(self):
        logger.debug(f"{self.__class__} does not support wireframe rendering")


    def render_solid(self):
        logger.debug(f"{self.__class__} does not support solid rendering")

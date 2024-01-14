from typing import Any, Sequence

from PySide6.QtCore import QEvent

from matplotlib.axes import Axes

from sas.qtgui.Plotting.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.Plotter2D import Plotter2D

from sas.qtgui.Utilities.TypedInputVariables import InputVariable

from abc import abstractmethod

class SlicerInteractor(BaseInteractor[Plotter2D]):

    def __init__(self, base: Plotter2D, axes: Axes, color: str='black'):
        super().__init__(base, axes, color=color)
        self.has_move = False
        self.save_x = 0
        self.save_y = 0

    def save(self, ev: QEvent):
        """
        Remember the position for this interactor so that we
        can restore on Esc.
        """
        self.save_x = self.x
        self.save_y = self.y


    def moveend(self, ev: QEvent):
        """
        Called after a dragging this object and set self.has_move to False
        to specify the end of dragging motion
        """
        self.has_move = False
        self.base.moveend(ev)


    def restore(self, ev: QEvent):
        """
        Restore the positions of the slicer
        """
        self.x = self.save_x
        self.y = self.save_y


    def move(self, x: float, y: float, ev: QEvent):
        """
        Process move to a new position, making sure that the move is allowed.
        """
        self.has_move = True
        self.base.update()
        self.base.draw()

    def setParameters(self, parameters: Sequence[InputVariable[Any]]):
        """ Set the parameters for this interactor """
        for parameter in parameters:
            self.setParameter(parameter)

    @abstractmethod
    def setParameter(self, variable: InputVariable[Any]):
        """ Set a single parameter for this interactor.

        Note: the variable might not refer to this interactor directly """

    @abstractmethod
    def getParameters(self) -> list[InputVariable[Any]]:
        """ Get a dictionary of the parameters for this interactor"""

    def clear(self):
        """ Clear graphics from the plot"""
        raise NotImplementedError(".clear not implemented for this slicer")
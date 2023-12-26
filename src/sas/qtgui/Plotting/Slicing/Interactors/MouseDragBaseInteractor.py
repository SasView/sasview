from PySide6.QtCore import QEvent

from matplotlib.axes import Axes

from sas.qtgui.Plotting.BaseInteractor import BaseInteractor
from sas.qtgui.Plotting.Plotter2D import Plotter2D


class MouseDragBaseInteractor(BaseInteractor[Plotter2D]):

    def __init__(self, base: Plotter2D, axes: Axes, color='black'):
        BaseInteractor.__init__(self, base, axes, color=color)

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

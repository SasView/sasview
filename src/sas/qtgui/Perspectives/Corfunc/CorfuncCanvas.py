from typing import Optional, Tuple

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .corefuncutil import WIDGETS


class CorfuncCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, model, width=5, height=4, dpi=100):
        self.model = model
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)

        self.data: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
        self.extrap = None
        # self.dragging = None
        # self.draggable = False
        # self.leftdown = False
        # self.fig.canvas.mpl_connect("button_release_event", self.on_mouse_up)
        # self.fig.canvas.mpl_connect("button_press_event", self.on_mouse_down)
        # self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
    #
    # def on_legend(self, qx, qy):
    #     """
    #     Checks if mouse coursor is on legend box
    #     :return:
    #     """
    #     on_legend_box = False
    #     bbox = self.legend.get_window_extent()
    #     if qx > bbox.xmin and qx < bbox.xmax and qy > bbox.ymin  and qy < bbox.ymax:
    #         on_legend_box = True
    #     return  on_legend_box
    #
    # def on_mouse_down(self, event):
    #     if not self.draggable:
    #         return
    #     if event.button == 1:
    #         self.leftdown = True
    #     if self.on_legend(event.x, event.y):
    #         return
    #
    #     qmin = float(self.model.item(WIDGETS.W_QMIN).text())
    #     qmax1 = float(self.model.item(WIDGETS.W_QMAX).text())
    #     qmax2 = float(self.model.item(WIDGETS.W_QCUTOFF).text())
    #
    #     q = event.xdata
    #
    #     if (np.abs(q-qmin) < np.abs(q-qmax1) and
    #         np.abs(q-qmin) < np.abs(q-qmax2)):
    #         self.dragging = "qmin"
    #     elif (np.abs(q-qmax2) < np.abs(q-qmax1)):
    #         self.dragging = "qmax2"
    #     else:
    #         self.dragging = "qmax1"
    #
    # def on_mouse_up(self, event):
    #     if not self.dragging:
    #         return None
    #     if event.button == 1:
    #         self.leftdown = False
    #     if self.on_legend(event.x, event.y):
    #         return
    #
    #     if self.dragging == "qmin":
    #         item = WIDGETS.W_QMIN
    #     elif self.dragging == "qmax1":
    #         item = WIDGETS.W_QMAX
    #     else:
    #         item = WIDGETS.W_QCUTOFF
    #
    #     self.model.setItem(item, QtGui.QStandardItem(str(GuiUtils.formatNumber(event.xdata))))
    #
    #     self.dragging = None
    #
    # def on_motion(self, event):
    #     if not self.leftdown:
    #         return
    #     if not self.draggable:
    #         return
    #     if self.dragging is None:
    #         return
    #
    #     if self.dragging == "qmin":
    #         item = WIDGETS.W_QMIN
    #     elif self.dragging == "qmax1":
    #         item = WIDGETS.W_QMAX
    #     else:
    #         item = WIDGETS.W_QCUTOFF
    #
    #     self.model.setItem(item, QtGui.QStandardItem(str(GuiUtils.formatNumber(event.xdata))))


    def draw_q_space(self):
        """Draw the Q space data in the plot window

        This draws the q space data in self.data, as well
        as the bounds set by self.qmin, self.qmax1, and self.qmax2.
        It will also plot the extrpolation in self.extrap, if it exists."""

        self.draggable = True

        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("log")
        self.axes.set_yscale("log")
        self.axes.set_xlabel("Q [$\AA^{-1}$]")
        self.axes.set_ylabel("I(Q) [cm$^{-1}$]")
        self.axes.set_title("Scattering data")
        self.fig.tight_layout()

        qmin = float(self.model.item(WIDGETS.W_QMIN).text())
        qmax1 = float(self.model.item(WIDGETS.W_QMAX).text())
        qmax2 = float(self.model.item(WIDGETS.W_QCUTOFF).text())

        if self.data:
            # self.axes.plot(self.data.x, self.data.y, label="Experimental Data")
            self.axes.errorbar(self.data.x, self.data.y, yerr=self.data.dy, label="Experimental Data")
            self.axes.axvline(qmin, color='k')
            self.axes.axvline(qmax1, color='k')
            self.axes.axvline(qmax2, color='k')
            self.axes.set_xlim(min(self.data.x) / 2,
                               max(self.data.x) * 1.5 - 0.5 * min(self.data.x))
            self.axes.set_ylim(min(self.data.y) / 2,
                               max(self.data.y) * 1.5 - 0.5 * min(self.data.y))

        if self.extrap:
            self.axes.plot(self.extrap.x, self.extrap.y, label="Extrapolation")

        if self.data or self.extrap:
            self.legend = self.axes.legend()

        self.draw()

    def draw_real_space(self):
        """
        This function draws the real space data onto the plot

        The 1d correlation function in self.data, the 3d correlation function
        in self.data3, and the interface distribution function in self.data_idf
        are all draw in on the plot in linear cooredinates."""

        self.draggable = False

        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("linear")
        self.axes.set_yscale("linear")
        self.axes.set_xlabel("Z [$\AA$]")
        self.axes.set_ylabel("Correlation")
        self.axes.set_title("Real Space Correlations")
        self.fig.tight_layout()

        if self.data:
            data1, data3, data_idf = self.data
            self.axes.plot(data1.x, data1.y, label="1D Correlation")
            self.axes.plot(data3.x, data3.y, label="3D Correlation")
            self.axes.set_xlim(0, max(data1.x) / 4)
            self.legend = self.axes.legend()

        self.draw()


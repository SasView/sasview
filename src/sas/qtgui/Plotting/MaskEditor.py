from functools import partial
import copy
import numpy as np

from PyQt5 import QtWidgets

from sas.qtgui.Plotting.PlotterData import Data2D

# Local UI
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.MaskEditorUI import Ui_MaskEditorUI
from sas.qtgui.Plotting.Plotter2D import Plotter2DWidget

from sas.qtgui.Plotting.Masks.SectorMask import SectorMask
from sas.qtgui.Plotting.Masks.BoxMask import BoxMask
from sas.qtgui.Plotting.Masks.CircularMask import CircularMask


class MaskEditor(QtWidgets.QDialog, Ui_MaskEditorUI):
    def __init__(self, parent=None, data=None):
        super(MaskEditor, self).__init__()

        assert isinstance(data, Data2D)

        self.setupUi(self)

        self.data = data
        self.parent = parent
        filename = data.name

        self.current_slicer = None
        self.slicer_mask = None

        self.setWindowTitle("Mask Editor for %s" % filename)

        self.plotter = Plotter2DWidget(self, manager=parent, quickplot=True)
        self.plotter.data = self.data
        self.slicer_z = 0
        self.default_mask = copy.deepcopy(data.mask)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(layout)
        layout.addWidget(self.plotter)

        self.plotter.plot()
        self.subplot = self.plotter.ax

        # update mask
        self.updateMask(self.default_mask)

        self.initializeSignals()

    def initializeSignals(self):
        """
        Attach slots to signals from radio boxes
        """
        self.rbWings.toggled.connect(partial(self.onMask, slicer=SectorMask, inside=True))
        self.rbCircularDisk.toggled.connect(partial(self.onMask, slicer=CircularMask, inside=True))
        self.rbRectangularDisk.toggled.connect(partial(self.onMask, slicer=BoxMask, inside=True))
        self.rbDoubleWingWindow.toggled.connect(partial(self.onMask, slicer=SectorMask, inside=False))
        self.rbCircularWindow.toggled.connect(partial(self.onMask, slicer=CircularMask, inside=False))
        self.rbRectangularWindow.toggled.connect(partial(self.onMask, slicer=BoxMask, inside=False))

        # Button groups defined so we can uncheck all buttons programmatically
        self.buttonGroup = QtWidgets.QButtonGroup()
        self.buttonGroup.addButton(self.rbWings)
        self.buttonGroup.addButton(self.rbCircularDisk)
        self.buttonGroup.addButton(self.rbRectangularDisk)
        self.buttonGroup.addButton(self.rbDoubleWingWindow)
        self.buttonGroup.addButton(self.rbCircularWindow)
        self.buttonGroup.addButton(self.rbRectangularWindow)

        # Push buttons
        self.cmdAdd.clicked.connect(self.onAdd)
        self.cmdReset.clicked.connect(self.onReset)
        self.cmdClear.clicked.connect(self.onClear)

    def emptyRadioButtons(self):
        """
        Uncheck all buttons without them firing signals causing unnecessary slicer updates
        """
        self.buttonGroup.setExclusive(False)
        self.rbWings.blockSignals(True)
        self.rbWings.setChecked(False)
        self.rbWings.blockSignals(False)

        self.rbCircularDisk.blockSignals(True)
        self.rbCircularDisk.setChecked(False)
        self.rbCircularDisk.blockSignals(False)

        self.rbRectangularDisk.blockSignals(True)
        self.rbRectangularDisk.setChecked(False)
        self.rbRectangularDisk.blockSignals(False)

        self.rbDoubleWingWindow.blockSignals(True)
        self.rbDoubleWingWindow.setChecked(False)
        self.rbDoubleWingWindow.blockSignals(False)

        self.rbCircularWindow.blockSignals(True)
        self.rbCircularWindow.setChecked(False)
        self.rbCircularWindow.blockSignals(False)

        self.rbRectangularWindow.blockSignals(True)
        self.rbRectangularWindow.setChecked(False)
        self.rbRectangularWindow.blockSignals(False)
        self.buttonGroup.setExclusive(True)

    def setSlicer(self, slicer):
        """
        Clear the previous slicer and create a new one.
        slicer: slicer class to create
        """
        # Clear current slicer
        if self.current_slicer is not None:
            self.current_slicer.clear()
        # Create a new slicer
        self.slicer_z += 1
        self.current_slicer = slicer(self, self.ax, zorder=self.slicer_z)
        self.ax.set_ylim(self.data.ymin, self.data.ymax)
        self.ax.set_xlim(self.data.xmin, self.data.xmax)
        # Draw slicer
        self.figure.canvas.draw()
        self.current_slicer.update()

    def onMask(self, slicer=None, inside=True):
        """
        Clear the previous mask and create a new one.
        """
        self.clearSlicer()
        # modifying data in-place
        self.slicer_z += 1

        self.current_slicer = slicer(self.plotter, self.plotter.ax, zorder=self.slicer_z, side=inside)

        self.plotter.ax.set_ylim(self.data.ymin, self.data.ymax)
        self.plotter.ax.set_xlim(self.data.xmin, self.data.xmax)

        self.plotter.canvas.draw()

        self.slicer_mask = self.current_slicer.update()

    def update(self):
        """
        Redraw the canvas
        """
        self.plotter.draw()

    def onAdd(self):
        """
        Generate required mask and modify underlying DATA
        """
        if self.current_slicer is None:
            return
        data = Data2D()
        data = self.data
        self.slicer_mask = self.current_slicer.update()
        data.mask = self.data.mask & self.slicer_mask
        self.updateMask(data.mask)
        self.emptyRadioButtons()

    def onClear(self):
        """
        Remove the current mask(s)
        """
        self.slicer_z += 1
        self.clearSlicer()
        self.current_slicer = BoxMask(self.plotter, self.plotter.ax,
                                      zorder=self.slicer_z, side=True)
        self.plotter.ax.set_ylim(self.data.ymin, self.data.ymax)
        self.plotter.ax.set_xlim(self.data.xmin, self.data.xmax)

        self.data.mask = copy.deepcopy(self.default_mask)
        # update mask plot
        self.updateMask(self.data.mask)
        self.emptyRadioButtons()

    def onReset(self):
        """
        Removes all the masks from data
        """
        self.slicer_z += 1
        self.clearSlicer()
        self.current_slicer = BoxMask(self.plotter, self.plotter.ax,
                                      zorder=self.slicer_z, side=True)
        self.plotter.ax.set_ylim(self.data.ymin, self.data.ymax)
        self.plotter.ax.set_xlim(self.data.xmin, self.data.xmax)
        mask = np.ones(len(self.data.mask), dtype=bool)
        self.data.mask = mask
        # update mask plot
        self.updateMask(mask)
        self.emptyRadioButtons()

    def clearSlicer(self):
        """
        Clear the slicer on the plot
        """
        if self.current_slicer is None:
            return

        self.current_slicer.clear()
        self.plotter.draw()
        self.current_slicer = None

    def updateMask(self, mask):
        """
        Respond to changes in masking
        """
        # the case of litle numbers of True points
        if len(mask[mask]) < 10 and self.data is not None:
            self.data.mask = copy.deepcopy(self.default_mask)
        else:
            self.default_mask = mask
        # make temperary data to plot
        temp_mask = np.zeros(len(mask))
        temp_data = copy.deepcopy(self.data)
        # temp_data default is None
        # This method is to distinguish between masked point and data point = 0.
        temp_mask = temp_mask / temp_mask
        temp_mask[mask] = temp_data.data[mask]

        temp_data.data[mask == False] = temp_mask[mask == False]

        if self.current_slicer is not None:
            self.current_slicer.clear()
            self.current_slicer = None

        # modify imshow data
        self.plotter.plot(data=temp_data, update=True)
        self.plotter.draw()

        self.subplot = self.plotter.ax

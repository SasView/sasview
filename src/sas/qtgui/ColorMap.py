"""
Allows users to change the range of the current graph
"""
from PyQt4 import QtGui
from PyQt4 import QtCore
import path_prepare

import matplotlib as mpl
from matplotlib import pylab
import numpy

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from sas.sasgui.guiframe.dataFitting import Data2D
from sas.qtgui.GuiUtils import formatNumber

DEFAULT_MAP = 'jet'

# Local UI
from sas.qtgui.UI.ColorMapUI import Ui_ColorMapUI

class ColorMap(QtGui.QDialog, Ui_ColorMapUI):
    def __init__(self, parent=None, cmap=None, vmin=0.0, vmax=100.0, data=None):
        super(ColorMap, self).__init__()

        self.setupUi(self)
        assert(isinstance(data, Data2D))

        self.data = data
        self._cmap_orig = self._cmap = cmap if cmap is not None else DEFAULT_MAP
        self.all_maps = [m for m in pylab.cm.datad]
        self.maps = sorted(m for m in self.all_maps if not m.endswith("_r"))
        self.rmaps = sorted(set(self.all_maps) - set(self.maps))

        self.vmin = vmin
        self.vmax = vmax

        # Initialize detector labels
        self.initDetectorData()

        # Initialize the combo box
        self.initMapCombobox()

        # Add the color map component
        self.initColorMap()

        # Initialize validators on amplitude textboxes
        validator_min = QtGui.QDoubleValidator(self.txtMinAmplitude)
        validator_min.setNotation(0)
        self.txtMinAmplitude.setValidator(validator_min)
        validator_max = QtGui.QDoubleValidator(self.txtMaxAmplitude)
        validator_max.setNotation(0)
        self.txtMaxAmplitude.setValidator(validator_max)

        # Enforce constant size on the widget
        self.setFixedSize(self.minimumSizeHint())

        # Handle combobox changes
        self.cbColorMap.currentIndexChanged.connect(self.onMapIndexChange)

        # Handle checkbox changes
        self.chkReverse.stateChanged.connect(self.onColorMapReversed)

        # Handle the reset button click
        self.buttonBox.button(QtGui.QDialogButtonBox.Reset).clicked.connect(self.onReset)

        # Handle the amplitude setup
        self.txtMinAmplitude.editingFinished.connect(self.onAmplitudeChange)
        self.txtMaxAmplitude.editingFinished.connect(self.onAmplitudeChange)

    def cmap(self):
        """
        Getter for the color map
        """
        return self._cmap

    def norm(self):
        """
        Getter for the color map norm
        """
        return (self._norm.vmin, self._norm.vmax)

    def onReset(self):
        """
        Respond to the Reset button click
        """
        # Go back to original settings
        self._cmap = self._cmap_orig
        self._norm = mpl.colors.Normalize(vmin=self.vmin, vmax=self.vmax)
        self.txtMaxAmplitude.clear()
        self.txtMinAmplitude.clear()
        self.initMapCombobox()
        # Redraw the widget
        self.redrawColorBar()
        self.canvas.draw()

    def initDetectorData(self):
        """
        Fill out the Detector labels
        """
        xnpts = len(self.data.x_bins)
        ynpts = len(self.data.y_bins)
        self.lblWidth.setText(formatNumber(xnpts))
        self.lblHeight.setText(formatNumber(ynpts))
        xmax = max(self.data.xmin, self.data.xmax)
        ymax = max(self.data.ymin, self.data.ymax)
        qmax = numpy.sqrt(numpy.power(xmax, 2) + numpy.power(ymax, 2))
        self.lblQmax.setText(formatNumber(qmax))
        self.lblStopRadius.setText(formatNumber(self.data.xmin))

    def initMapCombobox(self):
        """
        Fill out the combo box with all available color maps
        """
        if self._cmap in self.rmaps:
            maps = self.rmaps
            # Assure correct state of the checkbox
            self.chkReverse.setChecked(True)
        else:
            maps = self.maps
            # Assure correct state of the checkbox
            self.chkReverse.setChecked(False)

        self.cbColorMap.addItems(maps)
        # Set the default/passed map
        self.cbColorMap.setCurrentIndex(self.cbColorMap.findText(self._cmap))

    def initColorMap(self):
        """
        Prepare and display the color map
        """
        self.fig = mpl.figure.Figure(figsize=(4, 1))
        self.ax1 = self.fig.add_axes([0.05, 0.65, 0.9, 0.15])
        self._norm = mpl.colors.Normalize(vmin=self.vmin, vmax=self.vmax)
        self.redrawColorBar()
        self.canvas = FigureCanvas(self.fig)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.widget.setLayout(layout)

    def onMapIndexChange(self, index):
        """
        Respond to the color map change event
        """
        new_map = str(self.cbColorMap.itemText(index))
        self._cmap = new_map
        self.redrawColorBar()
        self.canvas.draw()

    def redrawColorBar(self):
        """
        Call ColorbarBase with current values, effectively redrawing the widget
        """
        self.cb = mpl.colorbar.ColorbarBase(self.ax1, cmap=self._cmap,
                                            norm=self._norm,
                                            orientation='horizontal')
        self.cb.set_label('Detector Colors')

    def onColorMapReversed(self, isChecked):
        """
        Respond to ticking/unticking the color map reverse checkbox
        """
        current_map = str(self.cbColorMap.currentText())
        if isChecked:
            # Add "_r" to map name for the reversed version
            new_map = current_map + "_r"
            maps = self.rmaps
            # Assure the reversed map exists.
            if new_map not in maps:
                new_map = maps[0]
        else:
            new_map = current_map[:-2] # "_r" = last two chars
            maps = self.maps
            # Base map for the reversed map should ALWAYS exist,
            # but let's be paranoid here
            if new_map not in maps:
                new_map = maps[0]

        self._cmap = new_map
        # Clearning the content of the combobox.
        # Needs signal blocking, or else onMapIndexChange() spoils it all
        self.cbColorMap.blockSignals(True)
        self.cbColorMap.clear()
        # Add the new set of maps
        self.cbColorMap.addItems(maps)
        # Remove the signal block before the proper index set
        self.cbColorMap.blockSignals(False)
        self.cbColorMap.setCurrentIndex(self.cbColorMap.findText(new_map))

    def onAmplitudeChange(self):
        """
        Respond to editing the amplitude fields
        """
        min_amp = self.vmin
        max_amp = self.vmax

        try:
            min_amp = float(self.txtMinAmplitude.text())
        except ValueError:
            pass
        try:
            max_amp = float(self.txtMaxAmplitude.text())
        except ValueError:
            pass

        self._norm = mpl.colors.Normalize(vmin=min_amp, vmax=max_amp)
        self.redrawColorBar()
        self.canvas.draw()

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Plotting.PlotUtilities import COLORS, SHAPES

from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Plotting.UI.PlotPropertiesUI import Ui_PlotPropertiesUI

class PlotProperties(QtWidgets.QDialog, Ui_PlotPropertiesUI):
    """ Dialog for modification of single plot properties """
    def __init__(self,
                 parent=None,
                 color=0,
                 marker=0,
                 marker_size=5,
                 legend=""):
        super(PlotProperties, self).__init__(parent)
        self.setupUi(self)
        self.setFixedSize(self.minimumSizeHint())

        self._parent = parent
        self._marker = marker if marker else 0
        self._color = color if color else 0
        self._legend = legend
        self._markersize = marker_size if marker_size else 5
        self.custom_color = False if isinstance(self._color, int) else True

        # Fill out the color combobox
        self.cbColor.addItems(list(COLORS.keys())[:-1])
        # data1d.custom_color can now be a simple integer,
        # specifying COLORS dict index or a string containing
        # the hex RGB value, e.g. #00FF00
        if isinstance(self._color, int):
            self.cbColor.setCurrentIndex(self._color)
        else:
            # Need the Custom entry here. "Custom" is always last.
            self.cbColor.addItems([list(COLORS.keys())[-1]])
            self.cbColor.setCurrentIndex(list(COLORS.keys()).index("Custom"))

        # Fill out the marker combobox
        self.cbShape.addItems(list(SHAPES.keys()))
        try:
            self.cbShape.setCurrentIndex(self._marker)
        except TypeError:
            marker_index = self.cbShape.findText(self._marker)
            self.cbShape.setCurrentIndex(marker_index)
        if self._legend:
            self.txtLegend.setText(self._legend)
        self.sbSize.setValue(self._markersize)

        # Connect slots
        self.cmdCustom.clicked.connect(self.onColorChange)
        self.cbColor.currentIndexChanged.connect(self.onColorIndexChange)

    def legend(self):
        ''' return current legend '''
        return str(self.txtLegend.text())

    def marker(self):
        ''' return the current shape index in SHAPE '''
        return self.cbShape.currentIndex()

    def markersize(self):
        ''' return marker size (int) '''
        return self.sbSize.value()

    def color(self):
        ''' return current color: index in COLORS or a hex string '''
        if self.custom_color:
            return self._color
        else:
            return self.cbColor.currentIndex()

    def onColorChange(self):
        """
        Pop up the standard Qt color change dialog
        """
        # Pick up the chosen color
        proposed_color = QtWidgets.QColorDialog.getColor(parent=self)
        # Update the text control
        if proposed_color.isValid():
            # Block currentIndexChanged
            self.cbColor.blockSignals(True)
            # Add Custom to the color combo box
            self.cbColor.addItems(["Custom"])
            self.cbColor.setCurrentIndex(list(COLORS.keys()).index("Custom"))
            # unblock currentIndexChanged
            self.cbColor.blockSignals(False)
            # Save the color as #RRGGBB
            self.custom_color = True
            self._color = str(proposed_color.name())
   
    def onColorIndexChange(self):
        """
        Dynamically add/remove "Custom" color index
        """
        # Changed index - assure Custom is deleted
        custom_index = self.cbColor.findText("Custom")
        self.custom_color = False
        if custom_index > -1:
            self.cbColor.removeItem(custom_index)
        
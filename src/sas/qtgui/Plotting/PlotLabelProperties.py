from PySide6 import QtWidgets

from sas.qtgui.Plotting.PlotUtilities import COLORS, COLORS_LETTER, FONTS, WEIGHTS
from sas.qtgui.Plotting.UI.PlotLabelPropertiesUI import Ui_PlotLabelPropertiesUI


class PlotLabelPropertyHolder:
    def __init__(self, font=None, color=None, weight=None, size=None, text="",):
        self.__properties = {}
        self.__properties['font'] = font
        self.__properties['color'] = color
        self.__properties['weight'] = weight
        self.__properties['size'] = size
        self.__properties['text'] = text

    @property
    def font(self):
        return self.__properties['font']

    @font.setter
    def font(self, value):
        self.__properties['font'] = value

    @property
    def color(self):
        return self.__properties['color']

    @color.setter
    def color(self, value):
        self.__properties['color'] = value

    @property
    def weight(self):
        return self.__properties['weight']

    @weight.setter
    def weight(self, value):
        self.__properties['weight'] = value

    @property
    def size(self):
        return self.__properties['size']

    @size.setter
    def size(self, value):
        self.__properties['size'] = value

    @property
    def text(self):
        return self.__properties['text']

    @text.setter
    def text(self, value):
        self.__properties['text'] = value


class PlotLabelProperties(QtWidgets.QDialog, Ui_PlotLabelPropertiesUI):
    """ Dialog for modification of plot label properties """
    def __init__(self,
                 parent=None,
                 x_props={},
                 y_props={}):

        super(PlotLabelProperties, self).__init__(parent)
        self.setupUi(self)

        self.setFixedSize(self.minimumSizeHint())

        self.custom_color = False
        self.custom_colory = False

        self._weight = x_props.weight
        self._color = x_props.color
        self._text = x_props.text
        self._size = x_props.size
        self._family = x_props.font

        self._weighty = y_props.weight
        self._colory = y_props.color
        self._texty = y_props.text
        self._sizey = y_props.size
        self._familyy = y_props.font

        # Fill out the color comboboxes
        self.cbColor.addItems(list(COLORS.keys())[:-1])
        self.cbColor_y.addItems(list(COLORS.keys())[:-1])
        # data1d.custom_color can now be a simple integer,
        # specifying COLORS dict index or a string containing
        # the hex RGB value, e.g. #00FF00
        if isinstance(self._color, int):
            self.cbColor.setCurrentIndex(self._color)
        elif self._color in COLORS.keys():
            self.cbColor.setCurrentIndex(list(COLORS.keys()).index(self._color))
        elif self._color in COLORS.values():
            self.cbColor.setCurrentIndex(list(COLORS.values()).index(self._color))
        elif self._color in COLORS_LETTER.keys():
            self.cbColor.setCurrentIndex(list(COLORS_LETTER.keys()).index(self._color))
        else:
            # Need the Custom entry here. "Custom" is always last.
            self.cbColor.addItems([list(COLORS.keys())[-1]])
            self.cbColor.setCurrentIndex(list(COLORS.keys()).index("Custom"))
            self.custom_color = True

        if isinstance(self._colory, int):
            self.cbColor_y.setCurrentIndex(self._colory)
        elif self._colory in COLORS.keys():
            self.cbColor_y.setCurrentIndex(list(COLORS.keys()).index(self._colory))
        elif self._colory in COLORS.values():
            self.cbColor_y.setCurrentIndex(list(COLORS.values()).index(self._colory))
        elif self._colory in COLORS_LETTER.keys():
            self.cbColor_y.setCurrentIndex(list(COLORS_LETTER.keys()).index(self._colory))
        else:
            # Need the Custom entry here. "Custom" is always last.
            self.cbColor_y.addItems([list(COLORS.keys())[-1]])
            self.cbColor_y.setCurrentIndex(list(COLORS.keys()).index("Custom"))
            self.custom_colory = True

        # Fill out the weight combobox
        self.cbWeight.addItems(WEIGHTS)
        try:
            self.cbWeight.setCurrentIndex(self._weight)
        except TypeError:
            marker_index = self.cbWeight.findText(self._weight)
            self.cbWeight.setCurrentIndex(marker_index)

        self.cbWeight_y.addItems(WEIGHTS)
        try:
            self.cbWeight_y.setCurrentIndex(self._weighty)
        except TypeError:
            marker_index = self.cbWeight_y.findText(self._weighty)
            self.cbWeight_y.setCurrentIndex(marker_index)

        # Fill out the font combobox
        self.cbFont.addItems(FONTS)
        try:
            self.cbFont.setCurrentIndex(self._family)
        except TypeError:
            marker_index = self.cbFont.findText(self._family)
            self.cbFont.setCurrentIndex(marker_index)

        self.cbFont_y.addItems(FONTS)
        try:
            self.cbFont_y.setCurrentIndex(self._familyy)
        except TypeError:
            marker_index = self.cbFont_y.findText(self._familyy)
            self.cbFont_y.setCurrentIndex(marker_index)


        self.txtLegend.setText(self._text)
        self.txtLegend_y.setText(self._texty)

        # Size
        self.cbSize.setValue(self._size)
        self.cbSize_y.setValue(self._sizey)

        # Connect slots
        self.cmdCustom.clicked.connect(self.onColorChange)
        self.cmdCustom_y.clicked.connect(self.onColorChange_y)
        self.cbColor.currentIndexChanged.connect(self.onColorIndexChange)
        self.cbColor_y.currentIndexChanged.connect(self.onColorIndexChange_y)

    def text_x(self):
        ''' return current legend text for x-axis '''
        return str(self.txtLegend.text())

    def text_y(self):
        ''' return current legend text for y-axis '''
        return str(self.txtLegend_y.text())

    def apply_to_ticks_x(self):
        ''' return status of the "Apply to ticks" checkbox for x-axis '''
        return self.chkTicks.isChecked()

    def apply_to_ticks_y(self):
        ''' return status of the "Apply to ticks" checkbox for y-axis '''
        return self.chkTicks_y.isChecked()

    def fx(self):
        ''' return font parameters for x-axis '''
        if self.custom_color:
            color = self._color
        else:
            color = self.cbColor.currentText()
        font = {'family': self.cbFont.currentText(),
                'color': color,
                'weight': self.cbWeight.currentText(),
                'size': self.cbSize.value(),
                }
        return font

    def fy(self):
        ''' return font parameters for y-axis '''
        if self.custom_colory:
            color = self._colory
        else:
            color = self.cbColor_y.currentText()
        font = {'family': self.cbFont_y.currentText(),
                'color': color,
                'weight': self.cbWeight_y.currentText(),
                'size': self.cbSize_y.value(),
                }
        return font

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

    def onColorChange_y(self):
        """
        Pop up the standard Qt color change dialog
        """
        # Pick up the chosen color
        proposed_color = QtWidgets.QColorDialog.getColor(parent=self)
        # Update the text control
        if proposed_color.isValid():
            # Block currentIndexChanged
            self.cbColor_y.blockSignals(True)
            # Add Custom to the color combo box
            self.cbColor_y.addItems(["Custom"])
            self.cbColor_y.setCurrentIndex(list(COLORS.keys()).index("Custom"))
            # unblock currentIndexChanged
            self.cbColor_y.blockSignals(False)
            # Save the color as #RRGGBB
            self.custom_colory = True
            self._colory = str(proposed_color.name())

    def onColorIndexChange(self):
        """
        Dynamically add/remove "Custom" color index
        """
        # Changed index - assure Custom is deleted
        custom_index = self.cbColor.findText("Custom")
        self.custom_color = False
        if custom_index > -1:
            self.cbColor.removeItem(custom_index)

    def onColorIndexChange_y(self):
        """
        Dynamically add/remove "Custom" color index
        """
        # Changed index - assure Custom is deleted
        custom_index = self.cbColor_y.findText("Custom")
        self.custom_colory = False
        if custom_index > -1:
            self.cbColor_y.removeItem(custom_index)

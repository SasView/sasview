from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

class ModelViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the model view
    """
    def __init__(self, parent=None):
        """
        Overwrite generic constructor to allow for some globals
        """
        super(QtWidgets.QStyledItemDelegate, self).__init__()

        # Main parameter table view columns
        self.param_error=-1
        self.param_property=0
        self.param_value=1
        self.param_min=2
        self.param_max=3
        self.param_unit=4

    def fancyColumns(self):
        return [self.param_value, self.param_min, self.param_max, self.param_unit]

    def addErrorColumn(self):
        """
        Modify local column pointers
        Note: the reverse is never required!
        """
        self.param_property=0
        self.param_value=1
        self.param_error=2
        self.param_min=3
        self.param_max=4
        self.param_unit=5

    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() in self.fancyColumns():
            # Units - present in nice HTML
            options = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(options,index)

            style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()

            # Prepare document for inserting into cell
            doc = QtGui.QTextDocument()

            # Convert the unit description into HTML
            text_html = GuiUtils.convertUnitToHTML(str(options.text))
            doc.setHtml(text_html)

            # delete the original content
            options.text = ""
            style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter, options.widget);

            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)

            painter.save()
            painter.translate(textRect.topLeft())
            painter.setClipRect(textRect.translated(-textRect.topLeft()))
            # Draw the QTextDocument in the cell
            doc.documentLayout().draw(painter, context)
            painter.restore()
        else:
            # Just the default paint
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, widget, option, index):
        """
        Overwrite generic editor for certain columns
        """
        if not index.isValid():
            return 0
        if index.column() == self.param_value: #only in the value column
            editor = QtWidgets.QLineEdit(widget)
            validator = GuiUtils.DoubleValidator()
            editor.setValidator(validator)
            return editor
        if index.column() in [self.param_property, self.param_error, self.param_unit]:
            # Set some columns uneditable
            return None

        return super(ModelViewDelegate, self).createEditor(widget, option, index)

    def setModelData(self, editor, model, index):
        """
        Overwrite generic model update method for certain columns
        """
        if index.column() in (self.param_min, self.param_max):
            try:
                value_float = float(editor.text())
            except ValueError:
                # TODO: present the failure to the user
                # balloon popup? tooltip? cell background colour flash?
                return
        QtWidgets.QStyledItemDelegate.setModelData(self, editor, model, index)


class PolyViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the polydispersity view
    """
    POLYDISPERSE_FUNCTIONS = ['rectangle', 'array', 'lognormal', 'gaussian', 'schulz']

    combo_updated = QtCore.pyqtSignal(str, int)
    filename_updated = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        """
        Overwrite generic constructor to allow for some globals
        """
        super(QtWidgets.QStyledItemDelegate, self).__init__()

        self.poly_parameter = 0
        self.poly_pd = 1
        self.poly_min = 2
        self.poly_max = 3
        self.poly_npts = 4
        self.poly_nsigs = 5
        self.poly_function = 6
        self.poly_filename = 7

    def editableParameters(self):
        return [self.poly_pd, self.poly_min, self.poly_max, self.poly_npts, self.poly_nsigs]

    def columnDict(self):
        return {self.poly_pd:    'width',
                self.poly_min:   'min',
                self.poly_max:   'max',
                self.poly_npts:  'npts',
                self.poly_nsigs: 'nsigmas'}

    def addErrorColumn(self):
        """
        Modify local column pointers
        Note: the reverse is never required!
        """
        self.poly_parameter = 0
        self.poly_pd = 1
        self.poly_min = 3
        self.poly_max = 4
        self.poly_npts = 5
        self.poly_nsigs = 6
        self.poly_function = 7
        self.poly_filename = 8

    def createEditor(self, widget, option, index):
        # Remember the current choice
        if not index.isValid():
            return 0
        elif index.column() == self.poly_filename:
            # Notify the widget that we want to change the filename
            self.filename_updated.emit(index.row())
            return None
        elif index.column() in self.editableParameters():
            self.editor = QtWidgets.QLineEdit(widget)
            validator = GuiUtils.DoubleValidator()
            self.editor.setValidator(validator)
            return self.editor
        else:
            QtWidgets.QStyledItemDelegate.createEditor(self, widget, option, index)

    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() in (self.poly_min, self.poly_max):
            # Units - present in nice HTML
            options = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(options,index)

            style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()

            # Prepare document for inserting into cell
            doc = QtGui.QTextDocument()

            # Convert the unit description into HTML
            text_html = GuiUtils.convertUnitToHTML(str(options.text))
            doc.setHtml(text_html)

            # delete the original content
            options.text = ""
            style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter, options.widget);

            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)

            painter.save()
            painter.translate(textRect.topLeft())
            painter.setClipRect(textRect.translated(-textRect.topLeft()))
            # Draw the QTextDocument in the cell
            doc.documentLayout().draw(painter, context)
            painter.restore()
        else:
            # Just the default paint
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

class MagnetismViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the magnetism view
    """
    def __init__(self, parent=None):
        """
        Overwrite generic constructor to allow for some globals
        """
        super(QtWidgets.QStyledItemDelegate, self).__init__()

        self.mag_parameter = 0
        self.mag_value = 1
        self.mag_min = 2
        self.mag_max = 3
        self.mag_unit = 4

    def editableParameters(self):
        return [self.mag_value, self.mag_min, self.mag_max]

    def addErrorColumn(self):
        """
        Modify local column pointers
        Note: the reverse is never required!
        """
        self.mag_parameter = 0
        self.mag_value = 1
        self.mag_min = 3
        self.mag_max = 4
        self.mag_unit = 5

    def createEditor(self, widget, option, index):
        # Remember the current choice
        current_text = index.data()
        if not index.isValid():
            return 0
        if index.column() in self.editableParameters():
            editor = QtWidgets.QLineEdit(widget)
            validator = GuiUtils.DoubleValidator()
            editor.setValidator(validator)
            return editor
        else:
            QtWidgets.QStyledItemDelegate.createEditor(self, widget, option, index)

    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() in (self.mag_min, self.mag_max, self.mag_unit):
            # Units - present in nice HTML
            options = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(options,index)

            style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()

            # Prepare document for inserting into cell
            doc = QtGui.QTextDocument()

            # Convert the unit description into HTML
            text_html = GuiUtils.convertUnitToHTML(str(options.text))
            doc.setHtml(text_html)

            # delete the original content
            options.text = ""
            style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter, options.widget);

            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)

            painter.save()
            painter.translate(textRect.topLeft())
            painter.setClipRect(textRect.translated(-textRect.topLeft()))
            # Draw the QTextDocument in the cell
            doc.documentLayout().draw(painter, context)
            painter.restore()
        else:
            # Just the default paint
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

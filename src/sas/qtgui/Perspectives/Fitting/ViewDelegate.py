from PyQt4 import QtGui
from PyQt4 import QtCore

import sas.qtgui.Utilities.GuiUtils as GuiUtils

class ModelViewDelegate(QtGui.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the model view
    """
    # Main parameter table view columns
    PARAM_PROPERTY=0
    PARAM_VALUE=1
    PARAM_MIN=2
    PARAM_MAX=3
    PARAM_UNIT=4

    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() in (self.PARAM_UNIT, self.PARAM_MIN, self.PARAM_MAX):
            # Units - present in nice HTML
            options = QtGui.QStyleOptionViewItemV4(option)
            self.initStyleOption(options,index)

            style = QtGui.QApplication.style() if options.widget is None else options.widget.style()

            # Prepare document for inserting into cell
            doc = QtGui.QTextDocument()

            # Convert the unit description into HTML
            text_html = GuiUtils.convertUnitToHTML(str(options.text))
            doc.setHtml(text_html)

            # delete the original content
            options.text = ""
            style.drawControl(QtGui.QStyle.CE_ItemViewItem, options, painter, options.widget);

            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            textRect = style.subElementRect(QtGui.QStyle.SE_ItemViewItemText, options)

            painter.save()
            painter.translate(textRect.topLeft())
            painter.setClipRect(textRect.translated(-textRect.topLeft()))
            # Draw the QTextDocument in the cell
            doc.documentLayout().draw(painter, context)
            painter.restore()
        else:
            # Just the default paint
            QtGui.QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, widget, option, index):
        """
        Overwrite generic editor for certain columns
        """
        if not index.isValid():
            return 0
        if index.column() == self.PARAM_VALUE: #only in the value column
            editor = QtGui.QLineEdit(widget)
            validator = QtGui.QDoubleValidator()
            editor.setValidator(validator)
            return editor

        return super(ModelViewDelegate, self).createEditor(widget, option, index)

    def setModelData(self, editor, model, index):
        """
        Overwrite generic model update method for certain columns
        """
        if index.column() in (self.PARAM_MIN, self.PARAM_MAX):
            try:
                value_float = float(editor.text())
            except ValueError:
                # TODO: present the failure to the user
                # balloon popup? tooltip? cell background colour flash?
                return
        QtGui.QStyledItemDelegate.setModelData(self, editor, model, index)


class PolyViewDelegate(QtGui.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the polydispersity view
    """
    # polydispersity functions
    POLYDISPERSE_FUNCTIONS=['rectangle', 'array', 'lognormal', 'gaussian', 'schulz']
    # polydispersity columns
    POLY_PARAMETER=0
    POLY_PD=1
    POLY_MIN=2
    POLY_MAX=3
    POLY_NPTS=4
    POLY_NSIGS=5
    POLY_FUNCTION=6
    POLY_EDITABLE_PARAMS = [POLY_MIN, POLY_MAX, POLY_NPTS, POLY_NSIGS]

    combo_updated = QtCore.pyqtSignal(str, int)

    def createEditor(self, widget, option, index):
        # Remember the current choice
        current_text = index.data().toString()
        if not index.isValid():
            return 0
        if index.column() == self.POLY_FUNCTION:
            editor = QtGui.QComboBox(widget)
            for function in self.POLYDISPERSE_FUNCTIONS:
                editor.addItem(function)
            current_index = editor.findText(current_text)
            editor.setCurrentIndex(current_index if current_index>-1 else 3)
            editor.currentIndexChanged.connect(lambda: self.combo_updated.emit(str(editor.currentText()), index.row()))
            return editor
        elif index.column() in self.POLY_EDITABLE_PARAMS:
            editor = QtGui.QLineEdit(widget)
            validator = QtGui.QDoubleValidator()
            editor.setValidator(validator)
            return editor
        else:
            QtGui.QStyledItemDelegate.createEditor(self, widget, option, index)

    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() in (self.POLY_MIN, self.POLY_MAX):
            # Units - present in nice HTML
            options = QtGui.QStyleOptionViewItemV4(option)
            self.initStyleOption(options,index)

            style = QtGui.QApplication.style() if options.widget is None else options.widget.style()

            # Prepare document for inserting into cell
            doc = QtGui.QTextDocument()

            # Convert the unit description into HTML
            text_html = GuiUtils.convertUnitToHTML(str(options.text))
            doc.setHtml(text_html)

            # delete the original content
            options.text = ""
            style.drawControl(QtGui.QStyle.CE_ItemViewItem, options, painter, options.widget);

            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            textRect = style.subElementRect(QtGui.QStyle.SE_ItemViewItemText, options)

            painter.save()
            painter.translate(textRect.topLeft())
            painter.setClipRect(textRect.translated(-textRect.topLeft()))
            # Draw the QTextDocument in the cell
            doc.documentLayout().draw(painter, context)
            painter.restore()
        else:
            # Just the default paint
            QtGui.QStyledItemDelegate.paint(self, painter, option, index)

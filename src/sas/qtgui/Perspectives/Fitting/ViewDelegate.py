"""
Delegates of the three parameter tables. A delegate asks the table's model for the name of a
column (``ParameterItemModel.column_name``), so it does not follow the error column itself.
"""
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils


def _column(index) -> str | None:
    return index.model().column_name(index.column())


def _number_editor(widget) -> QtWidgets.QLineEdit:
    editor = QtWidgets.QLineEdit(widget)
    editor.setValidator(GuiUtils.DoubleValidator())
    return editor


class _HtmlDelegate(QtWidgets.QStyledItemDelegate):
    """Draws the cells of HTML_COLUMNS as HTML (units, superscripts)."""
    HTML_COLUMNS: tuple = ()
    OFFSET = (0, 0)              # magic values for rendering a nice display in the table
    MARGIN = None                # the text document's margin; None: the default
    PAINTER_FONT = True          # the text document takes the painter's font

    def paint(self, painter, option, index):
        if _column(index) not in self.HTML_COLUMNS:
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
            return
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        style = QtWidgets.QApplication.style() if options.widget is None else options.widget.style()
        doc = QtGui.QTextDocument()
        if self.PAINTER_FONT:
            doc.setDefaultFont(painter.font())
        doc.setHtml(GuiUtils.convertUnitToHTML(str(options.text)))
        if self.MARGIN is not None:
            doc.setDocumentMargin(self.MARGIN)
        # delete the original content
        options.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter, options.widget)
        context = QtGui.QAbstractTextDocumentLayout.PaintContext()
        text_rect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)
        painter.save()
        rect = text_rect.topLeft()
        rect.setX(rect.x() + self.OFFSET[0])
        rect.setY(rect.y() + self.OFFSET[1])
        painter.translate(rect)
        painter.setClipRect(text_rect.translated(-rect))
        doc.documentLayout().draw(painter, context)
        painter.restore()


class ModelViewDelegate(_HtmlDelegate):
    """The main parameter table."""
    HTML_COLUMNS = ("value", "min", "max", "units")
    OFFSET = (3, 2)
    MARGIN = 1
    PAINTER_FONT = False

    def createEditor(self, widget, option, index):
        if not index.isValid():
            return None
        column = _column(index)
        if column == "value":
            return _number_editor(widget)
        if column not in ("min", "max") or not (index.flags() & QtCore.Qt.ItemIsEditable):
            return None
        return super().createEditor(widget, option, index)

    def setModelData(self, editor, model, index):
        if _column(index) in ("min", "max"):
            try:
                float(editor.text())
            except ValueError:
                # TODO: present the failure to the user
                return
        QtWidgets.QStyledItemDelegate.setModelData(self, editor, model, index)


class PolyViewDelegate(_HtmlDelegate):
    """The polydispersity table: a click on the filename asks for an array file."""
    POLYDISPERSE_FUNCTIONS = ['rectangle', 'array', 'lognormal', 'gaussian', 'schulz']
    EDITED = ("value", "min", "max", "npts", "nsigmas")
    HTML_COLUMNS = ("value", "min", "max")
    OFFSET = (0, 5)

    filename_updated = QtCore.Signal(int)

    def createEditor(self, widget, option, index):
        if not index.isValid():
            return None
        column = _column(index)
        if column == "filename":
            # Notify the widget that we want to change the filename
            self.filename_updated.emit(index.row())
            return None
        return _number_editor(widget) if column in self.EDITED else None


class MagnetismViewDelegate(_HtmlDelegate):
    """The magnetism table."""
    EDITED = ("value", "min", "max")
    HTML_COLUMNS = ("value", "min", "max", "units")
    OFFSET = (0, 6)

    def createEditor(self, widget, option, index):
        if not index.isValid():
            return None
        return _number_editor(widget) if _column(index) in self.EDITED else None

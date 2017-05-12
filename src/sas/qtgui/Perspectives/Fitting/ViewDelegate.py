from PyQt4 import QtGui
from PyQt4 import QtCore

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Table view columns
PROPERTY=0
VALUE=1
MIN=2
MAX=3
UNIT=4

class ModelViewDelegate(QtGui.QStyledItemDelegate):
    """
    Custom delegate for appearance and behavior control of the model view
    """
    def paint(self, painter, option, index):
        """
        Overwrite generic painter for certain columns
        """
        if index.column() == UNIT or index.column() == MIN or index.column() == MAX:
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
            style.drawControl(QtGui.QStyle.CE_ItemViewItem, options, painter);

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

    #def sizeHint(self, option, index):
    #    options = QtGui.QStyleOptionViewItemV4(option)
    #    self.initStyleOption(options,index)

    #    doc = QtGui.QTextDocument()
    #    doc.setHtml(options.text)
    #    doc.setTextWidth(options.rect.width())
    #    return QtCore.QSize(doc.idealWidth(), doc.size().height())

from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget
from PySide6.QtCore import Slot, Signal
from sasdata.quantities.units import NamedUnit
from sasdata.ascii_reader_metadata import pairings
from column_unit import ColumnUnit
from typing import cast

class ColEditor(QWidget):
    """An editor widget which allows the user to specify the columns of the data
    from a set of options based on which dataset type has been selected."""
    column_changed = Signal()

    @Slot()
    def onColumnUpdate(self):
        column_changed = cast(ColumnUnit, self.sender())
        pairing = pairings.get(column_changed.currentColumn)
        if not pairing is None:
            for col_unit in self.option_widgets:
                # Second condition is important because otherwise, this event will keep being called, and the GUI will
                # go into an infinite loop.
                if col_unit.currentColumn == pairing and col_unit.currentUnit != column_changed.currentUnit:
                    col_unit.currentUnit = column_changed.currentUnit
        self.column_changed.emit()


    def __init__(self, cols: int, options: list[str]):
        super().__init__()

        self.cols = cols
        self.options = options
        self.layout = QHBoxLayout(self)
        self.option_widgets: list[ColumnUnit] = []
        for _ in range(cols):
            new_widget = ColumnUnit(self.options)
            new_widget.column_changed.connect(self.onColumnUpdate)
            self.layout.addWidget(new_widget)
            self.option_widgets.append(new_widget)

    def setCols(self, new_cols: int):
        """Set the amount of columns for the user to edit."""

        # Decides whether we need to extend the current set of combo boxes, or
        # remove some.
        if self.cols < new_cols:
            for _ in range(new_cols - self.cols):
                new_widget = ColumnUnit(self.options)
                new_widget.column_changed.connect(self.onColumnUpdate)
                self.layout.addWidget(new_widget)
                self.option_widgets.append(new_widget)

            self.cols = new_cols
        if self.cols > new_cols:
            excess_cols = self.cols - new_cols
            length = len(self.option_widgets)
            excess_combo_boxes = self.option_widgets[length - excess_cols:length]
            for box in excess_combo_boxes:
                self.layout.removeWidget(box)
                box.setParent(None)
            self.option_widgets = self.option_widgets[0:length - excess_cols]
            self.cols = new_cols
        self.column_changed.emit()

    def setColOrder(self, cols: list[str]):
        """Sets the series of currently selected columns to be cols, in that
        order. If there are not enough column widgets include as many of the
        columns in cols as possible.

        """
        try:
            for i, col_name in enumerate(cols):
                self.option_widgets[i].setCurrentColumn(col_name)
        except IndexError:
            pass # Can ignore because it means we've run out of widgets.

    def colNames(self) -> list[str]:
        """Get a list of all of the currently selected columns."""
        return [widget.currentColumn for widget in self.option_widgets]

    @property
    def columns(self) -> list[tuple[str, NamedUnit]]:
        return [(widget.currentColumn, widget.currentUnit) for widget in self.option_widgets]

    def replaceOptions(self, new_options: list[str]) -> None:
        """Replace options from which the user can choose for each column."""
        self.options = new_options
        for widget in self.option_widgets:
            widget.replaceOptions(new_options)

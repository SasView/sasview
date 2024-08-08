from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget
from PySide6.QtCore import Slot, Signal
from column_unit import ColumnUnit


class ColEditor(QWidget):
    """An editor widget which allows the user to specify the columns of the data
    from a set of options based on which dataset type has been selected."""
    column_changed = Signal()

    @Slot()
    def on_column_update(self):
        self.column_changed.emit()


    def __init__(self, cols: int, options: list[str]):
        super().__init__()

        self.cols = cols
        self.options = options
        self.layout = QHBoxLayout(self)
        self.option_widgets = []
        for _ in range(cols):
            new_widget = ColumnUnit(self.options)
            new_widget.column_changed.connect(self.on_column_update)
            self.layout.addWidget(new_widget)
            self.option_widgets.append(new_widget)

    def set_cols(self, new_cols: int):
        """Set the amount of columns for the user to edit."""

        # Decides whether we need to extend the current set of combo boxes, or
        # remove some.
        if self.cols < new_cols:
            for _ in range(new_cols - self.cols):
                new_widget = ColumnUnit(self.options)
                new_widget.column_changed.connect(self.on_column_update)
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

    def set_col_order(self, cols: list[str]):
        """Sets the series of currently selected columns to be cols, in that
        order. If there are not enough column widgets include as many of the
        columns in cols as possible.

        """
        try:
            for i, col_name in enumerate(cols):
                self.option_widgets[i].set_current_column(col_name)
        except IndexError:
            pass # Can ignore because it means we've run out of widgets.

    def col_names(self) -> list[str]:
        """Get a list of all of the currently selected columns."""
        return [widget.current_column for widget in self.option_widgets]

    def replace_options(self, new_options: list[str]) -> None:
        """Replace options from which the user can choose for each column."""
        self.options = new_options
        for widget in self.option_widgets:
            widget.replace_options(new_options)

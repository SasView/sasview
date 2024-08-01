from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget
from PySide6.QtCore import Slot
from column_unit import ColumnUnit
from dataset_types import default_units


class ColEditor(QWidget):
    # def create_col_combo_box(self) -> QComboBox:
    #     new_combo_box = QComboBox()
    #     for option in self.options:
    #         new_combo_box.addItem(option)
    #     new_combo_box.setEditable(True)
    #     validator = QRegularExpressionValidator(r"[a-zA-Z0-9]+")
    #     new_combo_box.setValidator(validator)
    #     return new_combo_box

    # def create_unit_combo_box(self, selected_option: str) -> QComboBox:
    #     new_combo_box = QComboBox()
    #     default_unit = default_units[selected_option]
    #     new_combo_box.addItem(default_unit)
    #     return new_combo_box

    # def create_col_unit_box(self) -> tuple[QComboBox, QComboBox]:
    #     new_col_combo_box = self.create_col_combo_box()
    #     new_unit_combo_box = self.create_unit_combo_box(new_col_combo_box.currentText())
    #     # self.option_widgets.append(new_col_combo_box)
    #     return new_col_combo_box, new_unit_combo_box

    @Slot()
    def on_column_update(self):
        pass


    def __init__(self, cols: int, options: list[str]):
        super().__init__()

        self.cols = cols
        self.options = options
        self.layout = QHBoxLayout(self)
        self.option_widgets = []
        for _ in range(cols):
            new_widget = ColumnUnit(self.options)
            self.layout.addWidget(new_widget)
            self.option_widgets.append(new_widget)

    def set_cols(self, new_cols: int):
        # Decides whether we need to extend the current set of combo boxes, or
        # remove some.
        if self.cols < new_cols:
            for _ in range(new_cols - self.cols):
                # new_combo_box = self.create_col_combo_box()
                # self.option_widgets.append(new_combo_box)
                # self.layout.addWidget(new_combo_box)
                new_widget = ColumnUnit(self.options)
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

    def set_col_order(self, cols: list[str]):
        try:
            for i, col_name in enumerate(cols):
                self.option_widgets[i].set_current_column(col_name)
        except IndexError:
            pass # Can ignore because it means we've run out of widgets.

    def col_names(self) -> list[str]:
        return [col[0].currentText() for col in self.option_widgets]

    def replace_options(self, new_options: list[str]) -> None:
        self.options = new_options
        for widget in self.option_widgets:
            # col_box.clear()
            # col_box.addItems(new_options)
            # new_unit = default_units[col_box.currentText()]
            # unit_box.clear()
            # unit_box.addItem(new_unit)
            widget.replace_options(new_options)

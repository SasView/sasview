from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget


class ColEditor(QWidget):
    def create_col_combo_box(self) -> QComboBox:
        new_combo_box = QComboBox()
        for option in self.options:
            new_combo_box.addItem(option)
        new_combo_box.setEditable(True)
        return new_combo_box
    def __init__(self, cols: int, options: list[str]):
        super().__init__()

        self.cols = cols
        self.options = options
        self.layout = QHBoxLayout(self)
        self.option_widgets = []
        for _ in range(cols):
            # TODO: This is placeholder data.
            new_combo_box = self.create_col_combo_box()
            self.option_widgets.append(new_combo_box)
            self.layout.addWidget(new_combo_box)

    def set_cols(self, new_cols: int):
        # Decides whether we need to extend the current set of combo boxes, or
        # remove some.
        if self.cols < new_cols:
            for _ in range(new_cols - self.cols):
                new_combo_box = self.create_col_combo_box()
                self.option_widgets.append(new_combo_box)
                self.layout.addWidget(new_combo_box)
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
                self.option_widgets[i].setCurrentText(col_name)
        except IndexError:
            pass # Can ignore because it means we've run out of widgets.

    def col_names(self) -> list[str]:
        return [col.currentText() for col in self.option_widgets]

    def replace_options(self, new_options: list[str]) -> None:
        self.options = new_options
        for box in self.option_widgets:
            box.clear()
            box.addItems(new_options)

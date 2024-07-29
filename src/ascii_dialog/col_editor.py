from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget

def create_col_combo_box() -> QComboBox:
    placeholder_options = ["First", "Second", "Third"]
    new_combo_box = QComboBox()
    for option in placeholder_options:
        new_combo_box.addItem(option)
    return new_combo_box

class ColEditor(QWidget):
    def __init__(self, cols: int):
        super().__init__()

        self.cols = cols
        self.layout = QHBoxLayout(self)
        self.option_widgets = []
        for _ in range(cols):
            # TODO: This is placeholder data.
            new_combo_box = create_col_combo_box()
            self.option_widgets.append(new_combo_box)
            self.layout.addWidget(new_combo_box)

    def set_cols(self, new_cols: int):
        # Decides whether we need to extend the current set of combo boxes, or
        # remove some.
        if self.cols < new_cols:
            for _ in range(new_cols - self.cols):
                new_combo_box = create_col_combo_box()
                self.option_widgets.append(new_combo_box)
            self.cols = new_cols
        if self.cols > new_cols:
            excess_cols = new_cols - self.cols
            length = len(self.option_widgets)
            excess_combo_boxes = self.option_widgets[length - excess_cols:length]
            for box in excess_combo_boxes:
                self.layout.removeWidget(box)
            self.option_widgets = self.option_widgets[0:length - excess_cols]

from PySide6 import QtWidgets
from PySide6.QtCore import Qt


class LabelledSlider(QtWidgets.QWidget):
    """ Slider with labels and value text"""
    def __init__(self, name: str, min_value: int, max_value: int, value: int, tick_interval: int=10, name_width=10, value_width=30, value_units="°"):
        super().__init__()

        self.units = value_units

        self.name_label = QtWidgets.QLabel(name)
        self.name_label.setFixedWidth(name_width)

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setRange(min_value, max_value)
        self.slider.setTickInterval(tick_interval)
        self.slider.valueChanged.connect(self._on_value_changed)

        self.value_label = QtWidgets.QLabel(str(value) + value_units)
        self.value_label.setFixedWidth(value_width)
        self.value_label.setAlignment(Qt.AlignRight)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        layout.setContentsMargins(0,0,0,0)

        self.setLayout(layout)


    def _on_value_changed(self):
        self.value_label.setText("%i"%self.value() + self.units)

    @property
    def valueChanged(self):
        return self.slider.valueChanged

    def value(self) -> int:
        return int(self.slider.value())


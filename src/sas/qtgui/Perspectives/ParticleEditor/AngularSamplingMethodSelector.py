
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QVBoxLayout, QWidget

from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import AngularDistribution
from sas.qtgui.Perspectives.ParticleEditor.GeodesicSampleSelector import GeodesicSamplingSpinBox
from sas.qtgui.Perspectives.ParticleEditor.sampling.angles import angular_sampling_methods
from sas.qtgui.Perspectives.ParticleEditor.sampling.geodesic import GeodesicDivisions


class ParametersForm(QWidget):
    """ Form that displays the parameters associated with the class (also responsible for generating the sampler)"""
    def __init__(self, sampling_class: type, parent=None):
        super().__init__(parent=parent)

        self.sampling_class = sampling_class

        self.layout = QFormLayout()
        self.parameter_callbacks = []

        for parameter_name, text, cls in sampling_class.parameters():
            if isinstance(cls, GeodesicDivisions):
                widget = GeodesicSamplingSpinBox()

                def callback():
                    return widget.getNDivisions()

            elif isinstance(cls, float):
                widget = QDoubleSpinBox()

                def callback():
                    return widget.value()


            else:
                raise TypeError(f"Cannot create appropriate widget for parameter of type '{cls}'")

            self.layout.addRow(text, widget)
            self.parameter_callbacks.append((parameter_name, callback))

            self.setLayout(self.layout)

    def generate_sampler(self) -> AngularDistribution:
        """ Generate a sampler based on the selected parameters """

        parameter_dict = {name: callback() for name, callback in self.parameter_callbacks}

        return self.sampling_class(**parameter_dict)



class AngularSamplingMethodSelector(QWidget):
    """ Selects the method for doing angular sampling, and provides access to the parameters """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        self.combo = QComboBox()
        self.combo.addItems([cls.name() for cls in angular_sampling_methods])

        subwidget = QWidget()
        self.subwidget_layout = QVBoxLayout()
        subwidget.setLayout(self.subwidget_layout)

        layout.addWidget(self.combo)
        layout.addWidget(subwidget)

        self.setLayout(layout)

        self.entry_widgets = [ParametersForm(cls) for cls in angular_sampling_methods]

        for widget in self.entry_widgets:
            self.subwidget_layout.addWidget(widget)
            widget.hide()

        self.entry_widgets[0].show()

        self.combo.currentIndexChanged.connect(self.on_update)

    def on_update(self):
        for i in range(self.subwidget_layout.count()):
            self.subwidget_layout.itemAt(i).widget().hide()

        self.subwidget_layout.itemAt(self.combo.currentIndex()).widget().show()

    def generate_sampler(self) -> AngularDistribution:
        """ Create the angular distribution sampler spectified by the current settings"""
        return self.subwidget_layout.itemAt(self.combo.currentIndex()).widget().generate_sampler()

def main():
    """ Show a demo """

    from PySide6 import QtWidgets


    app = QtWidgets.QApplication([])


    widget = QWidget()
    layout = QVBoxLayout()

    sampling = AngularSamplingMethodSelector()

    def callback():
        print(sampling.generate_sampler())

    button = QtWidgets.QPushButton("Check")
    button.clicked.connect(callback)

    layout.addWidget(sampling)
    layout.addWidget(button)

    widget.setLayout(layout)

    widget.show()
    app.exec_()


if __name__ == "__main__":
    main()

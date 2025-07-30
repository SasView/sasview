
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from sas.qtgui.Perspectives.ParticleEditor.datamodel.types import MagnetismFunction, SLDFunction
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterEntries import (
    MagneticParameterEntry,
    ParameterEntry,
)
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterTableModel import ParameterTableModel


class ParameterTable(QWidget):
    """ Main table of parameters """
    def __init__(self, model: ParameterTableModel):
        super().__init__()

        self._model = model

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self.build()

    def build(self):
        """ Build the list of parameters"""
        # General parameters
        self._layout.addWidget(self._section_heading("General Parameters"))
        for parameter in self._model.fixed_parameters:
            entry = ParameterEntry(parameter, self._model, base_size=150)
            self._layout.addWidget(entry)

        self._layout.addWidget(self._section_heading("SLD Function Parameters"))
        for parameter in self._model.sld_parameters:
            entry = ParameterEntry(parameter, self._model)
            self._layout.addWidget(entry)

        self._layout.addWidget(self._section_heading("Magnetism Parameters"))
        for parameter in self._model.magnetism_parameters:
            entry = MagneticParameterEntry(parameter, self._model)
            self._layout.addWidget(entry)

    def _section_heading(self, text: str):
        span = QWidget()
        layout = QHBoxLayout()
        label = QLabel("<b>"+text+"</b>")

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))


        span.setLayout(layout)
        return span

    def clear(self):
        """ Clear the list of parameters """
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def rebuild(self):
        """ Rebuild the parameter list"""
        self.clear()
        self.build()

    def clean(self):
        """ Clean up the unused parameters in the parameter list """
        self._model.clean()
        self.rebuild()

    def update_contents(self, sld_function: SLDFunction, magnetism_function: MagnetismFunction | None):
        """ Update the contents of the parameter table with new functions"""
        self._model.update_from_code(sld_function, magnetism_function)
        self.rebuild()


def main():
    """ Show a demo of the table """
    from PySide6 import QtWidgets
    app = QtWidgets.QApplication([])

    model = ParameterTableModel()

    def test_function_1(x, y, z, a, b, c=7): pass
    def test_function_2(x, y, z, a, d=2, c=5): pass

    model.update_from_code(test_function_1, test_function_2)

    table = ParameterTable(model)

    table.show()
    app.exec_()


if __name__ == "__main__":
    main()

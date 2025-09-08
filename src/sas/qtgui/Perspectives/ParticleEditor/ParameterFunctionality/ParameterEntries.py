from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QSpacerItem, QWidget

from sas.qtgui.Perspectives.ParticleEditor.datamodel.parameters import MagnetismParameterContainer, Parameter
from sas.qtgui.Perspectives.ParticleEditor.ParameterFunctionality.ParameterTableModel import ParameterTableModel


class ParameterEntry(QWidget):
    """ GUI Entry"""

    def __init__(self, parameter: Parameter, model: ParameterTableModel, base_size=50):
        super().__init__()

        self._parameter = parameter
        self._base_size = base_size
        self._model = model

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)

        # Stuff with space either side
        self.main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self._add_items()
        self.main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.setLayout(self.main_layout)



    def _add_items(self):
        """ Add the components to this widget """
        if self._parameter.in_use:
            parameter_text = self._parameter.name
        else:
            parameter_text = f"<i>{self._parameter.name} (unused)</i>"

        self.name_label = QLabel(parameter_text)
        self.name_label.setFixedWidth(self._base_size)
        self.name_label.setAlignment(Qt.AlignRight)

        self.value_field = QLineEdit()
        doubleValidator = QDoubleValidator()
        self.value_field.setValidator(doubleValidator)
        self.value_field.setText(str(self._parameter.value))
        self.value_field.setFixedWidth(75)
        self.value_field.textEdited.connect(self._update_value)

        self.fit_check = QCheckBox("Fit")
        self.fit_check.setFixedWidth(40)

        self.main_layout.addWidget(self.name_label)
        self.main_layout.addWidget(self.value_field)
        self.main_layout.addWidget(self.fit_check)


    def _update_value(self):
        """ Called when the value is changed"""

        try:
            value = float(self.value_field.text())
            self._parameter.value = value
            print("Set", self._parameter.name, "=", self._parameter.value)

        except ValueError:
            # Just don't update
            pass




class MagneticParameterEntry(ParameterEntry):

    def __init__(self, parameter: MagnetismParameterContainer, model: ParameterTableModel):
        self._entry = parameter

        super().__init__(parameter.parameter, model)

    def _add_items(self):
        super()._add_items()

        self.link_check = QCheckBox("Link to SLD")
        self.link_check.setChecked(self._entry.linked)
        self.link_check.setFixedWidth(80)

        if self._model.can_link(self._parameter.name):
            self.link_check.setEnabled(True)
        else:
            self.link_check.setEnabled(False)

        self.main_layout.addWidget(self.link_check)

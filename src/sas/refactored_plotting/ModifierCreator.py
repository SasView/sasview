from sas.refactored_plotting.PlotModifiers import ModifierLinestyle, ModifierLinecolor, ModifierColormap
from PySide6.QtWidgets import QDialog, QComboBox, QLabel, QFormLayout, QPushButton

class ModifierCreator(QDialog):
    def __init__(self):
        super().__init__()

        self.candidate_modifiers = {
            "Line Style": ModifierLinestyle,
            "Line Colour": ModifierLinecolor,
            "Colour": ModifierColormap
        }

        self.setWindowTitle("Create a Plot Modifier")

        self.modifierLabel = QLabel("Select a modifier.")
        self.modifierComboBox = QComboBox()

        for key in self.candidate_modifiers.keys():
            self.modifierComboBox.addItem(key)

        self.modifierValueLabel = QLabel("Select the value for that modifier.")
        self.modifierValueComboBox = QComboBox()
        self.modifierValueComboBox.currentTextChanged.connect(self.onChangeModifier)

        self.createButton = QPushButton("Create")
        self.createButton.clicked.connect(self.done)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.modifierLabel, self.modifierComboBox)
        self.layout.addRow(self.modifierValueLabel, self.modifierValueComboBox)
        self.layout.addRow(self.createButton)
        # TODO: Add items

    def onChangeModifier(self):
        self.modifierValueComboBox.clear()
        modifier_options = self.candidate_modifiers[self.modifierValueComboBox.currentText()].options
        for option in modifier_options:
            self.modifierValueComboBox.addItem(option)
        
    


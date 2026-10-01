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

        # This has to be defined first because it depends on the next combo box
        # for its options.
        self.modifierValueLabel = QLabel("Select the value for that modifier.")
        self.modifierValueComboBox = QComboBox()

        self.modifierLabel = QLabel("Select a modifier.")
        self.modifierComboBox = QComboBox()
        self.modifierComboBox.currentTextChanged.connect(self.onChangeModifier)

        for key in self.candidate_modifiers.keys():
            self.modifierComboBox.addItem(key)

        self.createButton = QPushButton("Create")
        self.createButton.clicked.connect(self.done)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.modifierLabel, self.modifierComboBox)
        self.layout.addRow(self.modifierValueLabel, self.modifierValueComboBox)
        self.layout.addRow(self.createButton)

    def onChangeModifier(self):
        self.modifierValueComboBox.clear()
        modifier_options = self.candidate_modifiers[self.modifierComboBox.currentText()].options
        for option in modifier_options:
            self.modifierValueComboBox.addItem(option)
        
    


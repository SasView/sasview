from PySide6 import QtWidgets
from FitPageUI import Ui_fitPageWidget


class FitPage(QtWidgets.QWidget, Ui_fitPageWidget):
    def __init__(self, int_identifier):
        super(FitPage, self).__init__()
        self.setupUi(self)

        #fitPageIdentifier keeps track of which number this fitpage is identifier by (it is incremental)
        self.fitPageIdentifier = int_identifier

        self.comboBoxFormFactor.addItems(["Sphere", "Cylinder"])
        self.doubleSpinBox_height.setDisabled(True)
        self.comboBoxFormFactor.currentIndexChanged.connect(self.index_changed)

    def get_int_identifier(self):
        return self.fitPageIdentifier

    def get_combobox_index(self):
        return self.comboBoxFormFactor.currentIndex()

    def get_checkbox_fit(self):
        return self.checkBoxCreateFit.isChecked()

    def get_checkbox_2d(self):
        return self.checkBox2dData.isChecked()

    def index_changed(self, selected_item):
        if selected_item == 0:
            self.doubleSpinBox_height.setDisabled(True)
        elif selected_item == 1:
            self.doubleSpinBox_height.setDisabled(False)

from PySide6 import QtWidgets
from UI.FitPageUI import Ui_fitPageWidget


class FitPage(QtWidgets.QWidget, Ui_fitPageWidget):
    """
    Widget that is shown in the tabs from the Mainwindow. Is a subclass of a widget to directly store fitpage indexes
    in it.
    """
    def __init__(self, identifier):
        super(FitPage, self).__init__()
        self.setupUi(self)

        #identifier keeps track of which number this fitpage is identifier by (it is incremental)
        self._identifier = identifier

        self.comboBoxFormFactor.addItems(["Sphere", "Cylinder"])
        self.doubleSpinBox_height.setDisabled(True)
        self.comboBoxFormFactor.currentIndexChanged.connect(self.index_changed)

    @property
    def identifier(self):
        return self._identifier

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

from PyQt5 import QtWidgets

from sas.qtgui.Utilities.UI.PreferencesUI import Ui_preferencesUI


class PreferencesPanel(QtWidgets.QDialog, Ui_preferencesUI):
    """A preferences panel to house all SasView related settings.

    Release notes:
    SasView v5.0.5: Added defaults for loaded data units and plotted units

    **Important Note** When adding new preference widgets, the index for the listWidget and stackedWidget must match
    """
    def __init__(self, parent=None):
        super(PreferencesPanel, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle("Preferences")
        # Set defaults
        self.stackedWidget.setCurrentIndex(0)
        self.listWidget.setCurrentRow(0)
        # Add actions
        self.listWidget.currentItemChanged.connect(self.prefMenuChanged)

    def prefMenuChanged(self):
        """When the preferences menu selection changes, changes to the appropriate preferences widget """
        row = self.listWidget.currentRow()
        self.stackedWidget.setCurrentIndex(row)

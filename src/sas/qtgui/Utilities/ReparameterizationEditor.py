from PySide6 import QtWidgets, QtCore, QtGui

from sas.qtgui.Utilities.UI.ReparameterizationEditorUI import Ui_ReparameterizationEditor
from sas.qtgui.Utilities.ModelSelector import ModelSelector

class ReparameterizationEditor(QtWidgets.QDialog, Ui_ReparameterizationEditor):

    def __init__(self, parent=None):
        super(ReparameterizationEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        self.addSignals()
    
    def addSignals(self):
        self.selectModelButton.clicked.connect(self.onSelectModel)
        self.cmdCancel.clicked.connect(self.close)

    def onSelectModel(self):
        """
        Launch model selection dialog
        """
        self.model_selector = ModelSelector(self)
        self.model_selector.returnModelParamsSignal.connect(self.loadOldParams)
        self.model_selector.show()

    def loadOldParams(self, params):
        """
        Load parameters from the selected model into the oldParamTree
        """
        for param in params:
            item = QtWidgets.QTreeWidgetItem(self.oldParamTree)
            item.setText(0, param.name)
            self.oldParamTree.addTopLevelItem(item)

            # Create list of specs: (display name, property name)
            specs = [ ("default", "default"),
                       ("min", "limits[0]"),
                       ("max", "limits[1]"),
                       ("units", "units")
                     ]
            for spec in specs:
                sub_item = QtWidgets.QTreeWidgetItem(item)
                sub_item.setText(0, spec[0]) # First column is display name
                if '[' in spec[1]:
                    # Limit specs have an index, so we need to extract it
                    prop_name, index = spec[1].split('[')
                    index = int(index[:-1])  # Remove the closing ']' and convert to int
                    # Use getattr to get the property, then index into it
                    sub_item.setText(1, str(getattr(param, prop_name)[index]))
                else:
                    sub_item.setText(1, str(getattr(param, spec[1])))
                    

    def closeEvent(self, event):
        self.close()
        self.deleteLater()  # Schedule the window for deletion
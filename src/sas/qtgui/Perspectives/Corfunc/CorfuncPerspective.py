# global
import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from twisted.internet import threads
from twisted.internet import reactor

# sas-global
from sas.sascalc.invariant import invariant
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Utilities.GuiUtils as GuiUtils

# local
from UI.CorfuncPanel import Ui_CorfuncDialog
# from InvariantDetails import DetailsDialog
# from InvariantUtils import WIDGETS


class CorfuncWindow(QtGui.QDialog, Ui_CorfuncDialog):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.
    name = "Corfunc" # For displaying in the combo box
    #def __init__(self, manager=None, parent=None):
    def __init__(self, parent=None):
        #super(InvariantWindow, self).__init__(parent)
        super(CorfuncWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Corfunc Perspective")

        self.communicate = GuiUtils.Communicate()

    def allowBatch(self):
        """
        We cannot perform corfunc analysis in batch at this time.
        """
        return False

    def setData(self, data_item, is_batch=False):
        """
        Obtain a QStandardItem object and dissect it to get Data1D/2D
        Pass it over to the calculator
        """
        if not isinstance(data_item, list):
            msg = "Incorrect type passed to the Corfunc Perpsective"
            raise AttributeError(msg)

        if not isinstance(data_item[0], QtGui.QStandardItem):
            msg = "Incorrect type passed to the Corfunc Perspective"
            raise AttributeError(msg)

        self._model_item = data_item[0]
        data = GuiUtils.dataFromItem(self._model_item)

        # self.model.item(WIDGETS.W_FILENAME).setData(QtCoreQVariant(self._model_item.text()))

    def setClosable(self, value=True):
        """
        Allow outsiders close this widget
        """
        assert isinstance(value, bool)

        self._allow_close = value


if __name__ == "__main__":
    app = QtGui.QApplication([])
    import qt4reactor
    # qt4reactor.install()
    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from twisted.internet import reactor
    dlg = CorfuncWindow(reactor)
    print(dlg)
    dlg.show()
    # print(reactor)
    # reactor.run()
    sys.exit(app.exec_())

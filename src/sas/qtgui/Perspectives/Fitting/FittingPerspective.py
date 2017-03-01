import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

from FittingWidget import FittingWidget

class FittingWindow(QtGui.QTabWidget):
    """
    """
    name = "Fitting" # For displaying in the combo box in DataExplorer
    def __init__(self, manager=None, parent=None, data=None):
        super(FittingWindow, self).__init__()

        self.manager = manager
        self.parent = parent
        self._data = data

        # List of active fits
        self.tabs = []

        # Max index for adding new, non-clashing tab names
        self.maxIndex = 0

        # Index of the current tab
        self.currentTab = 0

        # The current optimizer
        self.optimizer = 'DREAM'

        # The tabs need to be closeable
        self.setTabsClosable(True)

        # Initialize the first tab
        self.addFit(None)

        # Deal with signals
        self.tabCloseRequested.connect(self.tabCloses)

        self.setWindowTitle('Fit panel - Active Fitting Optimizer: %s' % self.optimizer)

    def addFit(self, data):
        """
        Add a new tab for passed data
        """
        tab	= FittingWidget(manager=self.manager, parent=self.parent, data=data)
        self.tabs.append(tab)
        self.maxIndex += 1
        self.addTab(tab, self.tabName())

    def tabName(self):
        """
        Get the new tab name, based on the number of fitting tabs so far
        """
        page_name = "FitPage" + str(self.maxIndex)
        return page_name

    def tabCloses(self, index):
        """
        Update local bookkeeping on tab close
        """
        assert(len(self.tabs) >= index)
        # don't remove the last tab
        if len(self.tabs) <= 1:
            return
        del self.tabs[index]
        self.removeTab(index)

    def allowBatch(self):
        """
        Tell the caller that we accept multiple data instances
        """
        return True

    def setData(self, data_item=None):
        """
        Assign new dataset to the fitting instance
        """
        assert(data_item is not None)

        # Find an unassigned tab.
        # If none, open a new tab.
        available_tabs = list(map(lambda tab:tab.acceptsData(), self.tabs))

        if True in available_tabs:
            self.tabs[available_tabs.index(True)].data = data_item
        else:
            self.addFit(data_item)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    dlg = FittingWindow()
    dlg.show()
    sys.exit(app.exec_())

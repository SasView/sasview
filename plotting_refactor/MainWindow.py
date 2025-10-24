import sys
import traceback

from DataViewer import DataViewer
from FitPage import FitPage
from PySide6 import QtWidgets
from UI.MainWindowUI import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    MainWindow for the application, uses self.fittingTabs to create a tab selection of FitPages in which
    comboboxes and spinboxes are placed for data creation. Also has calculation and plot buttons to invoke methods
    for these logics.
    Owner of the DataViewer, that centralizes the logic between plotting and data handling (with the DataCollector)
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Tabbed Plot Demo")
        self.setFixedSize(700, 560)

        self.fitPageCounter = 1
        self.fittingTabs.addTab(FitPage(self.fitPageCounter), "Fit Page "+str(self.fitPageCounter))

        self.dataviewer = DataViewer(self)

        self.cmdShowDataViewer.clicked.connect(self.dataviewer.onShowDataViewer)
        self.cmdPlot.clicked.connect(self.onPlot)
        self.cmdCalculate.clicked.connect(self.onCalculate)
        self.actionNewFitPage.triggered.connect(self.onActionNewFitPage)

    def onPlot(self):
        """
        Invoked when pressing plot button, collects the fitpage_index for the currently selected fitpage and gives it
        to other parts of the program where this is used as a unique identifier for datasets that are saved in the
        DataCollector.
        Invokes plot creation after data creation.
        """
        fitpage_index = self.fittingTabs.currentWidget().identifier
        self.onCalculate()
        self.dataviewer.create_plot(fitpage_index)

    def onCalculate(self):
        """
        Calculates data for the currently selected fitpage. This data is then shown in the DataViewer dataTreeWidget.
        """
        fitpage_index = self.fittingTabs.currentWidget().identifier
        create_fit = self.fittingTabs.currentWidget().get_checkbox_fit()
        checked_2d = self.fittingTabs.currentWidget().get_checkbox_2d()
        self.dataviewer.update_dataset(fitpage_index, create_fit, checked_2d)

    def onActionNewFitPage(self):
        """
        Creates a new fitpage by the button in the menubar of the mainwindow on top.
        """
        self.fitPageCounter += 1
        self.fittingTabs.addTab(FitPage(self.fitPageCounter), "Fit Page " + str(self.fitPageCounter))
        self.fittingTabs.setCurrentIndex(self.fitPageCounter-1)

    def closeEvent(self, event):
        QtWidgets.QApplication.closeAllWindows()
        sys.exit()

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error caught!:")
    print("error message:\n", tb)
    QtWidgets.QApplication.quit()


def main():
    sys.excepthook = excepthook
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    ret = app.exec()
    sys.exit(ret)

if __name__ == '__main__':
    main()

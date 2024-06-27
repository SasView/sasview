import sys
import os
import traceback
from PySide6 import QtWidgets

from MainWindowUI import Ui_MainWindow
from FitPage import FitPage
from DataViewer import DataViewer

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("Tabbed Plot Demo")
        self.setFixedSize(700, 560)

        self.fitPageCounter = 1
        self.newFitPage = FitPage(int_identifier=self.fitPageCounter)
        self.fittingTabs.addTab(self.newFitPage, "Fit Page "+str(self.fitPageCounter))

        self.dataviewer = DataViewer(self)

        self.cmdShowDataViewer.clicked.connect(self.dataviewer.onShowDataViewer)
        self.cmdPlot.clicked.connect(self.onPlot)
        self.cmdCalculate.clicked.connect(self.onCalculate)
        self.actionNewFitPage.triggered.connect(self.onActionNewFitPage)

    def onPlot(self):
        fitpage_index = self.fittingTabs.currentWidget().get_int_identifier()
        self.onCalculate()
        self.dataviewer.create_plot(fitpage_index)

    def onCalculate(self):
        fitpage_index = self.fittingTabs.currentWidget().get_int_identifier()
        create_fit = self.fittingTabs.currentWidget().get_checkbox_fit()
        checked_2d = self.fittingTabs.currentWidget().get_checkbox_2d()
        self.dataviewer.update_dataset(self, fitpage_index, create_fit, checked_2d)
        self.dataviewer.update_datasets_from_collector()

    def onActionNewFitPage(self):
        self.fitPageCounter += 1
        self.newFitPage = FitPage(self.fitPageCounter)
        self.fittingTabs.addTab(self.newFitPage, "Fit Page " + str(self.fitPageCounter))
        self.fittingTabs.setCurrentIndex(self.fitPageCounter-1)

    def closeEvent(self, event):
        QtWidgets.QApplication.closeAllWindows()
        sys.exit()

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error caught!:")
    print("error message:\n", tb)
    QtWidgets.QApplication.quit()


sys.excepthook = excepthook
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

ret = app.exec()
sys.exit(ret)

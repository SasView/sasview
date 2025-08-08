"""
FitPanel class contains fields allowing to fit  models and  data

"""
from PySide6 import QtCore, QtWidgets


class ResultPanel(QtWidgets.QTabWidget):
    """
    FitPanel class contains fields allowing to fit  models and  data

    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.

    """
    ## Internal name for the AUI manager
    window_name = "Result panel"
    windowClosedSignal = QtCore.Signal()

    def __init__(self, parent, manager=None, *args, **kwargs):
        """
        """
        super(ResultPanel, self).__init__(parent)
        self.manager = manager
        self.communicator = self.manager.communicator()
        self.setMinimumSize(400, 400)
        self.data_id = None

        from .PlotView import ConvergenceView, CorrelationView, TraceView, UncertaintyView
        self.convergenceView = ConvergenceView()
        self.correlationView = CorrelationView()
        self.uncertaintyView = UncertaintyView()
        self.traceView = TraceView()
        self.show()

    def onPlotResults(self, results, optimizer="Unknown"):
        # import moved here due to its cost
        self.clearAnyData()

        result = results[0][0]
        name = result.data.sas_data.name
        current_optimizer = optimizer
        self.data_id = result.data.sas_data.id
        self.setWindowTitle(self.window_name + " - " + name + " - " + current_optimizer)
        if hasattr(result, 'convergence') and len(result.convergence) > 0:
            self.convergenceView.update(result)
            self.addTab(self.convergenceView, "Convergence")
            self.convergenceView.show()
        else:
            self.convergenceView.close()
        if hasattr(result, 'uncertainty_state'):
            self.correlationView.update(result)
            self.correlationView.show()
            self.addTab(self.correlationView, "Correlation")

            self.uncertaintyView.update(result)
            self.uncertaintyView.show()
            self.addTab(self.uncertaintyView, "Uncertainty")

            self.traceView.update(result)
            self.traceView.show()
            self.addTab(self.traceView, "Parameter Trace")
        else:
            for view in (self.correlationView, self.uncertaintyView, self.traceView):
                view.close()
        # no tabs in the widget - possibly LM optimizer. Mark "closed"
        if self.count()==0:
            self.close()

    def onDataDeleted(self, data):
        """ Check if the data set is shown in the window and close tabs as needed. """
        if not data or not self.isVisible():
            return
        if data.id == self.data_id:
            self.setWindowTitle(self.window_name)
            self.clearAnyData()
            self.close()

    def clearAnyData(self):
        """ Clear any previous results and reset window to its base state. """
        self.data_id = None
        # Clear up previous results
        for view in (self.convergenceView, self.correlationView,
                     self.uncertaintyView, self.traceView):
            view.close()
        # close all tabs. REMEMBER TO USE REVERSED RANGE!!!
        for index in reversed(range(self.count())):
            self.removeTab(index)

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # notify the parent so it hides this window
        self.windowClosedSignal.emit()
        event.ignore()

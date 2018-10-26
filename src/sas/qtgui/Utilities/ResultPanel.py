"""
FitPanel class contains fields allowing to fit  models and  data

"""
import sys
import datetime

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from bumps.dream.stats import var_stats, format_vars


class ResultPanel(QtWidgets.QTabWidget):
    """
    FitPanel class contains fields allowing to fit  models and  data

    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.

    """
    ## Internal name for the AUI manager
    window_name = "Result panel"
    windowClosedSignal = QtCore.pyqtSignal()

    def __init__(self, parent, manager=None, *args, **kwargs):
        """
        """
        super(ResultPanel, self).__init__(parent)
        self.manager = manager
        self.communicator = self.manager.communicator()
        self.setMinimumSize(400, 400)

        self.updateBumps() # patch bumps ## TEMPORARY ##

        # the following two imports will move to the top once
        # the monkeypatching is gone
        from bumps.gui.convergence_view import ConvergenceView
        from bumps.gui.uncertainty_view import UncertaintyView, CorrelationView, TraceView


        self.convergenceView = ConvergenceView()
        self.uncertaintyView = UncertaintyView()
        self.correlationView = CorrelationView()
        self.traceView = TraceView()
        self.show()

    def updateBumps(self):
        """
        Monkeypatching bumps plot viewer to allow Qt
        """
        from . import PlotView
        import bumps.gui
        sys.modules['bumps.gui.plot_view'] = PlotView

    def onPlotResults(self, results):
        # Clear up previous results
        for view in (self.convergenceView, self.correlationView,
                     self.uncertaintyView, self.traceView):
            view.close()

        result = results[0][0]
        filename = result.data.sas_data.filename
        current_time = datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y")
        self.setWindowTitle(self.window_name + " - " + filename + " - " + current_time)
        if hasattr(result, 'convergence'):
            best, pop = result.convergence[:, 0], result.convergence[:, 1:]
            self.convergenceView.update(best, pop)
            self.addTab(self.convergenceView, "Convergence")
            self.convergenceView.show()
        else:
            self.convergenceView.close()
        if hasattr(result, 'uncertainty_state'):
            stats = var_stats(result.uncertainty_state.draw())
            msg = format_vars(stats)
            self.correlationView.update(result.uncertainty_state)
            self.correlationView.show()
            self.addTab(self.correlationView, "Correlation")

            self.uncertaintyView.update((result.uncertainty_state, stats))
            self.uncertaintyView.show()
            self.addTab(self.uncertaintyView, "Uncertainty")

            self.traceView.update(result.uncertainty_state)
            self.traceView.show()
            self.addTab(self.traceView, "Parameter Trace")
        else:
            for view in (self.correlationView, self.uncertaintyView, self.traceView):
                view.close()

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # notify the parent so it hides this window
        self.windowClosedSignal.emit()
        event.ignore()


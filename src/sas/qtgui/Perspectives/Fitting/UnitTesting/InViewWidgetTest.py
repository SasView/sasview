import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.InViewWidget import InViewWidget
from sas.qtgui.Plotting.PlotterData import Data1D

logger = logging.getLogger(__name__)

class InViewWidgetTest:

    @pytest.fixture(autouse=True)
    def widget(self, qapp, qtbot):
        w = InViewWidget(parent=None)
        # Prevent auto-deletion on close during tests
        w.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        qtbot.addWidget(w)     # keeps it alive and cleans up reliably
        w.show()
        qapp.processEvents()
        return w

    def _make_fw(self, *, params, values, details, data=None, pdi=False):
        """
        Building dummy widget of Fit Page with elements that are connected with InViewWidget
        """

        class _FW:
            pass

        fw = _FW()
        fw.main_params_to_fit = list(params)

        class _Chk:
            def __init__(self, checked):
                self._c = checked

            def isChecked(self):
                return self._c

        class _Poly:
            def __init__(self):
                self.poly_params_to_fit = [n for n in params if n.endswith('.width')]
                self.poly_model = QtGui.QStandardItemModel()
                for n in self.poly_params_to_fit:
                    it = QtGui.QStandardItem(f"Distribution of {n[:-6]}")
                    it.setData(n, QtCore.Qt.UserRole)
                    self.poly_model.appendRow(it)
                self.poly_params = {}

        fw.polydispersity_widget = _Poly()


        # Adding controls that are getting turned on and off when InViewWidget is active
        fw.lstParams = QtWidgets.QTableView()
        fw.cbCategory = QtWidgets.QComboBox()
        fw.cmdFit = QtWidgets.QPushButton()
        fw.cmdPlot = QtWidgets.QPushButton()

        fw.getModelKeyFromName = lambda name: 'model'
        fw.getRowFromName = lambda name: 0

        # Param Table
        m = QtGui.QStandardItemModel(1, 2)

        first_param = params[0]
        m.setItem(0, 1,  QtGui.QStandardItem(str(values[first_param])))
        fw.model_dict = {'model': m}

        class _Kernel:
            def __init__(self, _details):
                self.details = dict(_details)

            def setParam(self, name, value): #### <-----------------
                pass

        class _Logic:
            def __init__(self):
                self.kernel_module = _Kernel(details)
                self.data = data or Data1D(x=[0.01, 0.02], y=[1.0, 1.0])

            def new1DPlot(self, return_data, tab_id):
                return SimpleNamespace()


        fw.logic = _Logic()
        fw.q_range_min = None
        fw.q_range_max = None

        class _Smearing:
            def smearer(self):
                return None

        fw.smearing_widget = _Smearing()
        fw.is2D = False
        fw.weighting = None
        fw.tab_id = 1
        return fw

    def test_defaults(self, widget):
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget._update_timer.isSingleShot()
        assert widget._update_timer.interval() == 75 #### <-----------------
        assert widget.plotter is not None

    def test_setData_plots(self, widget, mocker):
        widget.plotter.plot = MagicMock()
        d = Data1D(x=[1.0, 2.0], y=[1.0, 2.0])
        widget.setData(d)
        assert widget._has_data is True
        widget.plotter.plot.assert_called_once()

    def test_initFromFitPage_builds_sliders(self, widget):
        fw = self._make_fw(
            params=['scale'],
            values={'scale': 1.0},
            details={'scale': ('', 0.5, 1.5)}
        )
        widget.initFromFitPage(fw)
        # slider metadata exists
        assert 'scale' in widget._slider_meta
        meta = widget._slider_meta['scale']
        spin = meta['spin']
        assert spin.minimum() == 0.5
        assert spin.maximum() == 1.5
        assert spin.value() == 1.0

    def test_recompute_model_triggers_calc_and_plot(self, widget, mocker):
        d = Data1D(x=[0.01, 0.02], y=[1.0, 1.0])
        widget.setData(d)
        fw = self._make_fw(
            params=['scale'],
            values={'scale': 1.0},
            details={'scale': ('', 0.5, 1.5)},
            data=d
        )

        # Keep weight trivial
        mocker.patch.object(FittingUtilities, 'getWeight', return_value=None)

        # Dummy Calc1D which returns something to feed _complete_inview
        class DummyCalc:
            def __init__(self, **kwargs): self.kwargs = kwargs
            def compute(self): return {'theory': [1.0, 1.0]}

        mocker.patch('sas.qtgui.Perspectives.Fitting.InViewWidget.Calc1D',
                     side_effect=lambda **kw: DummyCalc(**kw))

        # Plotter interactions: ensure plot_dict and methods are safe
        widget.plotter.plot = MagicMock()
        widget.plotter.replacePlot = MagicMock()
        widget.plotter.plot_dict = {}

        # Observe new1DPlot call and plotting
        fw.logic.new1DPlot = MagicMock(return_value=SimpleNamespace())
        widget.initFromFitPage(fw)  # calls _recompute_model inside
        assert fw.logic.new1DPlot.called
        assert widget.plotter.plot.called or widget.plotter.replacePlot.called

    def test_apply_to_fitpage_updates_model(self, widget, mocker):
        fw = self._make_fw(
            params=['scale'],
            values={'scale': 1.0},
            details={'scale': ('', 0.5, 1.5)}
        )
        widget.initFromFitPage(fw)
        widget._param_values['scale'] = 1.2345

        # Stable formatting for assertion
        mocker.patch('sas.qtgui.Perspectives.Fitting.InViewWidget.GuiUtils.formatNumber',
                     side_effect=lambda v, high=True: str(v))

        widget._apply_to_fitpage()
        model = fw.model_dict['model']
        assert model.item(0, 1).text() == '1.2345'


    @pytest.mark.xfail(reason="2022-09 already broken")
    def test_onHelp(self, widget):
        pass

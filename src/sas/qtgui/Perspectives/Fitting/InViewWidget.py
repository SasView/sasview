import copy
import logging

from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.UI.InViewWidgetUI import Ui_InViewWidgetUI
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities import GuiUtils
from sas.system import HELP_SYSTEM

logger = logging.getLogger(__name__)

class InViewWidget(QtWidgets.QWidget, Ui_InViewWidgetUI):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(QtCore.Qt.Window, True)
        self.setupUi(self)
        self.communicator = GuiUtils.Communicate()
        self.plotter = PlotterWidget(self, self)
        self._has_data = False
        if self.plotBox.layout() is not None:
            self.plotBox.layout().addWidget(self.plotter)
        self._fw = None
        self._plot_name = "InView Model"
        self._param_values = {}
        self._param_info = {}
        self._slider_meta = {}
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(75)
        self._update_timer.timeout.connect(self._recompute_model)
        if hasattr(self, 'cmdUpdateParam'):
            self.cmdUpdateParam.clicked.connect(self._apply_to_fitpage)
        if hasattr(self, 'cmdHelp'):
            self.cmdHelp.clicked.connect(self.onHelp)
        if hasattr(self, 'cmdClose'):
            self.cmdClose.clicked.connect(self.close)

    def setData(self, data):
        if not isinstance(data, Data1D):
            return
        self._has_data = True
        #self.plotter.plot(data=data)

        try:
            x = data.x
            y = data.y
            if y is not None and hasattr(y, "__len__") and len(x) == len(y):
                # Let Plotter draw data points (with errors if present)
                # Optional: ensure it's not mistaken for a theory line
                # data.symbol = 17  # e.g. triangle marker; leave as-is if you prefer defaults
                self.plotter.plot(data=data)
            # else: skip plotting data, but keep the window and model plotting functional
        except Exception:
            # If anything odd about the dataset, skip plotting data
            pass

    def initFromFitPage(self, fitting_widget):
        self._fw = fitting_widget
        params = list(self._fw.main_params_to_fit)
        try:
            if self._fw.chkPolydispersity.isChecked():
                params += list(self._fw.polydispersity_widget.poly_params_to_fit)
        except Exception:
            pass
        seen = set()
        params = [p for p in params if not (p in seen or seen.add(p))]
        self._param_info = {}
        for name in params:
            try:
                model_key = self._fw.getModelKeyFromName(name)
                row = self._fw.getRowFromName(name)
                if row is None:
                    continue
                val = GuiUtils.toDouble(self._fw.model_dict[model_key].item(row, 1).text())
            except Exception:
                continue
            try:
                _, pmin, pmax = self._fw.logic.kernel_module.details.get(name, ('', None, None))
            except Exception:
                pmin = None
                pmax = None
            if pmin is None or pmax is None or not (pmax > pmin):
                delt = abs(val) if val is not None else 1.0
                if delt <= 0:
                    delt = 1.0
                pmin = (val - delt) if val is not None else -1.0
                pmax = (val + delt) if val is not None else 1.0
            ###
            unit = ""
            try:
                d = self._fw.logic.kernel_module.details.get(name)
                if d and len(d) >= 1 and d[0]:
                    unit = str(d[0])
                elif name.endswith('.width'):
                    base = name[:-6]
                    bd = self._fw.logic.kernel_module.details.get(base)
                    if bd and len(bd) >= 1 and bd[0]:
                        unit = str(bd[0])
            except Exception:
                unit = ""

            self._param_info[name] = {
                'min': float(pmin),
                'max': float(pmax),
                'value': float(val),
                'unit': unit
            }
            #self._param_info[name] = {'min': float(pmin), 'max': float(pmax), 'value': float(val)}
            ###
        self._build_sliders(list(self._param_info.keys()))
        self._recompute_model()

    def _build_sliders(self, params):
        layout = self.sliderBox.layout()
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            else:
                sub = item.layout()
                if sub is not None:
                    while sub.count():
                        child = sub.takeAt(0)
                        cw = child.widget()
                        if cw is not None:
                            cw.deleteLater()
                    sub.deleteLater()
        self._slider_meta = {}
        steps = 1000
        for name in params:
            info = self._param_info[name]
            container = QtWidgets.QWidget(self)
            h = QtWidgets.QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            lbl = QtWidgets.QLabel(self._display_label_for_param(name), container)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, container)
            slider.setMinimum(0)
            slider.setMaximum(steps)
            slider.setTracking(True)
            spin = QtWidgets.QDoubleSpinBox(container)
            spin.setDecimals(8)
            spin.setMinimum(info['min'])
            spin.setMaximum(info['max'])
            ###
            if info['max'] > info['min']:
                spin.setSingleStep((info['max'] - info['min'])/100.0)

            unit = info.get('unit', '')
            unit_lbl = QtWidgets.QLabel("", container)
            unit_lbl.setObjectName(f"lblUnit_{name}")
            unit_lbl.setContentsMargins(6, 0, 0, 0)
            if unit:
                unit_lbl.setTextFormat(QtCore.Qt.RichText)
                unit_lbl.setText(GuiUtils.convertUnitToHTML(unit))
            unit_lbl.setVisible(bool(unit))

            val = info['value']
            spin.setValue(val)
            ###
            pos = self._value_to_slider(val, info['min'], info['max'], steps)
            slider.setValue(pos)
            h.addWidget(lbl)
            h.addWidget(slider, 2)
            h.addWidget(spin)
            h.addWidget(unit_lbl)
            layout.addWidget(container)
            self._slider_meta[name] = {'slider': slider, 'spin': spin, 'min': info['min'], 'max': info['max'], 'steps': steps}
            self._param_values[name] = val
            slider.valueChanged.connect(lambda v, p=name: self._on_slider_changed(p, v))
            spin.valueChanged.connect(lambda v, p=name: self._on_spin_changed(p, v))

    def _display_label_for_param(self, name: str) -> str:
        if name.endswith('.width'):
            try:
                poly_model = self._fw.polydispersity_widget.poly_model
                for row in range(poly_model.rowCount()):
                    item = poly_model.item(row, 0)
                    if item is None:
                        continue
                    if item.data(QtCore.Qt.UserRole) == name:
                        txt = item.text()
                        if txt:
                            return str(txt)
            except Exception:
                pass
            base = name[:-6]
            return f"Distribution of {base}"
        return name

    def _slider_to_value(self, pos, min_v, max_v, steps):
        return float(min_v + (max_v - min_v) * (float(pos) / float(steps)))

    def _value_to_slider(self, val, min_v, max_v, steps):
        if max_v == min_v:
            return 0
        t = (val - min_v) / (max_v - min_v)
        t = min(max(t, 0.0), 1.0)
        return int(round(t * steps))

    def _on_slider_changed(self, name, pos):
        meta = self._slider_meta.get(name)
        if not meta:
            return
        val = self._slider_to_value(pos, meta['min'], meta['max'], meta['steps'])
        self._param_values[name] = val
        spin = meta['spin']
        try:
            spin.blockSignals(True)
            spin.setValue(val)
        finally:
            spin.blockSignals(False)
        self._update_timer.start()

    def _on_spin_changed(self, name, val):
        meta = self._slider_meta.get(name)
        if not meta:
            return
        self._param_values[name] = float(val)
        slider = meta['slider']
        pos = self._value_to_slider(val, meta['min'], meta['max'], meta['steps'])
        try:
            slider.blockSignals(True)
            slider.setValue(pos)
        finally:
            slider.blockSignals(False)
        self._update_timer.start()

    def _recompute_model(self):
        if self._fw is None or not self._has_data:
            return
        model = copy.deepcopy(self._fw.logic.kernel_module)
        #####
        # 1) If polydispersity is enabled, push slider widths into the polydispersity widget
        try:
            if self._fw.chkPolydispersity.isChecked():
                for pname, pinfo in self._param_info.items():
                    if '.width' in pname:
                        val = float(self._param_values.get(pname, pinfo['value']))
                        self._fw.polydispersity_widget.poly_params[pname] = val
        except Exception:
            pass

        # 2) Apply extras (polydispersity + magnetism) using the Fit page widgets
        try:
            # This calls polydispersity_widget.updateModel(model) and magnetism_widget.updateModel(model)
            self._fw.updateKernelModelWithExtraParams(model)
        except Exception:
            pass

        # 3) Apply all slider params to the model (non-PDI and as a final override for PDI widths)
        for pname, pinfo in self._param_info.items():
            try:
                model.setParam(pname, float(self._param_values.get(pname, pinfo['value'])))
            except Exception:
                pass
        #####
        data = self._fw.logic.data
        qmin = self._fw.q_range_min
        qmax = self._fw.q_range_max
        smearer = self._fw.smearing_widget.smearer()
        weight = FittingUtilities.getWeight(data=data, is2d=self._fw.is2D, flag=self._fw.weighting)
        calc = Calc1D(model=model, page_id=0, data=data, qmin=qmin, qmax=qmax, smearer=smearer, weight=weight, update_chisqr=False, completefn=self._complete_inview)
        try:
            ret = calc.compute()
            if ret is not None:
                self._complete_inview(ret)
        except Exception:
            return

    def _complete_inview(self, return_data):
        try:
            fitted = self._fw.logic.new1DPlot(return_data, self._fw.tab_id)
        except Exception:
            return
        fitted.name = self._plot_name
        fitted.symbol = "Line"

        if self._plot_name in self.plotter.plot_dict:
            self.plotter.replacePlot(self._plot_name, fitted)
        else:
            self.plotter.plot(data=fitted)

    def _apply_to_fitpage(self):
        if self._fw is None:
            return
        # Update the Fit page table only; no plotting here
        for name, val in self._param_values.items():
            row = self._fw.getRowFromName(name)
            if row is None:
                continue
            model_key = self._fw.getModelKeyFromName(name)
            model = self._fw.model_dict.get(model_key)
            if model is None:
                continue
            try:
                model.item(row, 1).setText(GuiUtils.formatNumber(val, high=True))
            except Exception:
                model.item(row, 1).setText(str(val))
        # Let the view refresh and dataChanged handlers run
        QtWidgets.QApplication.processEvents()

        # Stoping any pending slider-triggered recompute , after that, closing the window
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()

    def onHelp(self):
        """
        Show the InView help in the embedded documentation window
        """
        if not HELP_SYSTEM.path:
            logger.error("Help documentation was not found.")
            return
        base = HELP_SYSTEM.path
        help_location = base / "user" / "qtgui" / "Perspectives" / "Fitting" / "inview.html"
        if not help_location.exists():
            help_location = base / "user" / "qtgui" / "Perspectives" / "Fitting" / "fitting_help.html"
        # Keep a reference so the window isn't garbage collected immediately
        self._help_window = GuiUtils.showHelp(help_location)

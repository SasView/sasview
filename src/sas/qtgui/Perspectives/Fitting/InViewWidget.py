import copy
import logging

import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.ModelThread import Calc1D
from sas.qtgui.Perspectives.Fitting.UI.InViewWidgetUI import Ui_InViewWidgetUI
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities import GuiUtils
from sas.system import HELP_SYSTEM

logger = logging.getLogger(__name__)

SLIDER_STEPS = 1000        
UPDATE_INTERVAL_MS = 15    
LOG_SLIDER_RATIO = 1e3     
FIXED_XLIM = (1e-4, 1.0)   
FIXED_YLIM = (1e-3, 1e4)   
DATA_MARGIN = 0.05

def format_value(val):
    if val != 0 and (abs(val) < 1e-2 or abs(val) >= 1e4):
        mantissa, exponent = f"{val:.2e}".split('e')
        mantissa = mantissa.rstrip('0').rstrip('.')
        return f"{mantissa}e{int(exponent)}"
    return f"{val:.2f}".rstrip('0').rstrip('.')


class CompactSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDecimals(12)            

    def textFromValue(self, value):
        return format_value(value)

    def valueFromText(self, text):
        try:
            return float(text)
        except ValueError:
            return self.value()

    def validate(self, text, pos):
        try:
            float(text)
            return QtGui.QValidator.Acceptable, text, pos
        except ValueError:
            return QtGui.QValidator.Intermediate, text, pos

    WIDEST_TEXT = "-8.88e-88"

    def _extra_width(self):
        fm = self.fontMetrics()
        current = max(fm.horizontalAdvance(self.textFromValue(self.minimum())), fm.horizontalAdvance(self.textFromValue(self.maximum())))
        return max(0,fm.horizontalAdvance(self.WIDEST_TEXT) - current)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(hint.width() + self._extra_width())
        return hint

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        hint.setWidth(hint.width() + self._extra_width())
        return hint

def finite_range(val, pmin, pmax):
    if pmin is None or not np.isfinite(pmin):
        pmin = 0.0 if val > 0 else (10*val if val < 0 else -1.0)
    if pmax is None or not np.isfinite(pmax):
        pmax = 10.0*val if val > 0 else (0.0 if val < 0 else 1.0)
    pmin, pmax = min(pmin, val), max(pmax, val)
    if not pmax > pmin:
        delt = abs(val) if val != 0 else 1.0
        pmin, pmax = val - delt, val + delt
    return float(pmin), float(pmax)

class SuggestBoundsDialog(QtWidgets.QDialog):
    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("InView - parameter ranges")
        self._rows = rows
        self._bounds = []
        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(
            "Some parameters have infinite min/max, so a slider range cannot be set.\n"
            "Suggested ranges are filled in below - accept them or edit Min/Max.\n"
            "The ranges are written to the Fit Page and are also used as fit bounds.")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.table = QtWidgets.QTableWidget(len(rows), 4, self)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value", "Min", "Max"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        bold = QtGui.QFont()
        bold.setBold(True)
        for i, (name, value, old_min, old_max, s_min, s_max) in enumerate(rows):
            for col, text in ((0, name), (1, f"{value:.6g}")):
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.table.setItem(i, col, item)
            for col, old, new in ((2, old_min, s_min), (3, old_max, s_max)):
                item = QtWidgets.QTableWidgetItem(f"{new:.6g}")
                if not np.isfinite(old):
                    item.setFont(bold)          # suggested value
                    item.setToolTip(f"suggested (was {old})")
                self.table.setItem(i, col, item)
        layout.addWidget(self.table)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self)
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Use these ranges")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(560, 140 + 32 * len(rows))

    def _on_accept(self):
        bounds = []
        for i, row in enumerate(self._rows):
            name = row[0]
            try:
                pmin = float(self.table.item(i, 2).text())
                pmax = float(self.table.item(i, 3).text())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "InView", f"{name}: Min and Max must be numbers.")
                return
            if not (np.isfinite(pmin) and np.isfinite(pmax) and pmin < pmax):
                QtWidgets.QMessageBox.warning(self, "InView", f"{name}: Min must be finite and smaller than Max.")
                return
            bounds.append((name, pmin, pmax))
        self._bounds = bounds
        self.accept()

    def bounds(self):
        return self._bounds

def suggest_finite_bounds(fitting_widget, params, parent = None):
    kernel = fitting_widget.logic.kernel_module
    rows = []
    for name in dict.fromkeys(params):  
        details = kernel.details.get(name)
        if details is None or len(details) < 3:
            continue
        old_min, old_max = float(details[1]), float(details[2])
        if np.isfinite(old_min) and np.isfinite(old_max):
            continue
        try:
            value = float(kernel.getParam(name))
        except Exception:
            value = 0.0
        s_min, s_max = finite_range(value, old_min, old_max)
        if np.isfinite(old_min):
            s_min = old_min
        if np.isfinite(old_max):
            s_max = old_max
        if not s_max > s_min:
            s_max = s_min + (abs(s_min) if s_min != 0 else 1.0)
        rows.append((name, value, old_min, old_max, s_min, s_max))
    if not rows:
        return True
    dialog = SuggestBoundsDialog(rows, parent)
    if dialog.exec() != QtWidgets.QDialog.Accepted:
        return False
    for name, pmin, pmax in dialog.bounds():
        _write_bounds_to_fitpage(fitting_widget, name, pmin, pmax)
    return True

def _write_bounds_to_fitpage(fitting_widget, name, pmin, pmax):
    details = fitting_widget.logic.kernel_module.details.get(name)
    if details is not None and len(details) >= 3:
        details[1] = pmin
        details[2] = pmax
    try:
        if fitting_widget.getModelKeyFromName(name) != "standard":
            return
        row = fitting_widget.getRowFromName(name)
        if row is None:
            return
        delegate = fitting_widget.lstParams.itemDelegate()
        table = fitting_widget._model_model
        table.item(row, delegate.param_min).setText(GuiUtils.formatNumber(pmin, high=True))
        table.item(row, delegate.param_max).setText(GuiUtils.formatNumber(pmax, high=True))
    except Exception:
        logger.debug("Could not show the new bounds of %s in the Fit Page", name, exc_info=True)

class InViewWidget(QtWidgets.QWidget, Ui_InViewWidgetUI):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(QtCore.Qt.Window, True)
        self.setupUi(self)
        self.communicator = GuiUtils.Communicate()
        self.plotter = PlotterWidget(self, self)
        self._has_data = False
        self._data = None
        if self.plotBox.layout() is not None:
            self.plotBox.layout().addWidget(self.plotter)
        self._fw = None
        self._plot_name = "InView Model"
        self._param_values = {}
        self._param_info = {}
        self._slider_meta = {}
        self._model_copy = None
        self._calc_result = None
        self._model_lines = []
        self._setting_limits = False
        self._callback_registry = None
        self._update_timer = QtCore.QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(UPDATE_INTERVAL_MS)
        self._update_timer.timeout.connect(self._recompute_model)
        self._build_axis_controls()
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
        self._data = data

        try:
            x = data.x
            y = data.y
            if y is not None and hasattr(y, "__len__") and len(x) == len(y):
                self.plotter.plot(data=data)
        except Exception:
            pass

    def initFromFitPage(self, fitting_widget):
        self._fw = fitting_widget
        self._model_copy = None
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
            pmin, pmax = finite_range(float(val), pmin, pmax) 
            use_log = pmin >0 and pmax / pmin > LOG_SLIDER_RATIO
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
                'unit': unit, 
                'log': use_log
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
        steps = SLIDER_STEPS
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
            slider.setSingleStep(1)
            slider.setPageStep(10)
            slider.setToolTip(f"{format_value(info['min'])} ... {format_value(info['max'])}"
                                          + (" (logarithmic)" if info['log'] else ""))
            spin = CompactSpinBox(container)
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
            pos = self._value_to_slider(val, info['min'], info['max'], steps, info['log'])
            slider.setValue(pos)
            h.addWidget(lbl)
            h.addWidget(slider, 2)
            h.addWidget(spin)
            h.addWidget(unit_lbl)
            layout.addWidget(container)
            self._slider_meta[name] = {'slider': slider, 'spin': spin, 'min': info['min'], 'max': info['max'], 'steps': steps, 'log': info['log']}
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

    def _slider_to_value(self, pos, min_v, max_v, steps, log=False):
        t = float(pos) / float(steps)
        if log:
            return float(10**(np.log10(min_v) + t*(np.log10(max_v) - np.log10(min_v))))
        return float(min_v + (max_v - min_v) * t)

    def _value_to_slider(self, val, min_v, max_v, steps, log=False):
        if max_v == min_v:
            return 0
        if log:
            t = (np.log10(max(val,min_v)) - np.log10(min_v)) / (np.log10(max_v) - np.log10(min_v))
        else:
            t = (val - min_v) / (max_v - min_v)
        t = min(max(float(t), 0.0), 1.0)
        return int(round(t * steps))
    def _schedule_update(self):
        if not self._update_timer.isActive():
            self._update_timer.start()
        
    def _on_slider_changed(self, name, pos):
        meta = self._slider_meta.get(name)
        if not meta:
            return
        val = self._slider_to_value(pos, meta['min'], meta['max'], meta['steps'], meta['log'])
        self._param_values[name] = val
        spin = meta['spin']
        try:
            spin.blockSignals(True)
            spin.setValue(val)
        finally:
            spin.blockSignals(False)
        self._schedule_update()

    def _on_spin_changed(self, name, val):
        meta = self._slider_meta.get(name)
        if not meta:
            return
        self._param_values[name] = float(val)
        slider = meta['slider']
        pos = self._value_to_slider(val, meta['min'], meta['max'], meta['steps'], meta['log'])
        try:
            slider.blockSignals(True)
            slider.setValue(pos)
        finally:
            slider.blockSignals(False)
        self._schedule_update()

    def _recompute_model(self):
        if self._fw is None or not self._has_data:
            return
        if self._model_copy is None:
            self._model_copy = copy.deepcopy(self._fw.logic.kernel_module)
        model = self._model_copy
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
        self._calc_result = None
        calc = Calc1D(model=model, page_id=0, data=data, qmin=qmin, qmax=qmax, smearer=smearer, weight=weight, update_chisqr=False, completefn=self._store_result)
        try:
            ret = calc.compute()
        except Exception:
            logger.debug("InView model calculation failed", exc_info=True)
            return
        if ret is None:
            ret = self._calc_result
        if ret is not None:
            self._complete_inview(ret)
            return
    def _store_result(self, return_data):
        self._calc_result = return_data

    def _complete_inview(self, return_data):
        try:
            fitted = self._fw.logic.new1DPlot(return_data, self._fw.tab_id)
        except Exception:
            return
        fitted.name = self._plot_name
        fitted.id = self._plot_name
        fitted.symbol = "Line"

        if self._update_model_lines(fitted):
            self.plotter.canvas.draw_idle()
            return
        self._full_replot(fitted)

    def _ax(self):
        return getattr(self.plotter, 'ax', None)

    def _update_model_lines(self, fitted):
        ax = self._ax()
        lines = [ln for ln in self._model_lines if ax is not None and ln.axes is ax and ln in ax.lines]
        if not lines or len(lines) != len(self._model_lines):
            return False
        x = np.array(fitted.x, dtype=float)
        y = np.array(fitted.y, dtype=float)
        for ln in lines:
            ln.set_data(x, y)
        return True

    def _full_replot(self, fitted):
        ax = self._ax()
        if ax is not None and self._limits_initialized:
            limits = (ax.get_xlim(), ax.get_ylim())
        else:
            limits = self._default_limits()
        self._setting_limits = True
        try:
            if self._plot_name in self.plotter.plot_dict:
                self.plotter.replacePlot(self._plot_name, fitted)
            else:
                self.plotter.plot(data=fitted)
            ax = self._ax()
            if ax is not None:
                ax.get_xlim()
                ax.get_ylim()
        finally:
            self._setting_limits = False
        self._set_limits(*limits)
        self._limits_initialized = True
        self._find_model_lines(fitted)
        self._connect_limit_callbacks()
        self.plotter.canvas.draw_idle()

    def _find_model_lines(self, fitted):
        self._model_lines = []
        ax = self._ax()
        if ax is None:
            return
        x = np.array(fitted.x, dtype=float)
        y = np.array(fitted.y, dtype=float)
        for ln in ax.lines:
            lx = np.asarray(ln.get_xdata(), dtype=float)
            ly = np.asarray(ln.get_ydata(), dtype=float)
            if lx.shape == x.shape and ly.shape ==y.shape and np.allclose(lx, x, equal_nan=True) and np.allclose(ly, y, equal_nan=True):
                self._model_lines.append(ln)

    def _build_axis_controls(self):
        box = QtWidgets.QGroupBox("Axes range", self)
        grid = QtWidgets.QGridLayout(box)
        validator = QtGui.QDoubleValidator(box)
        self.txtXmin, self.txtXmax, self.txtYmin, self.txtYmax = \
            (QtWidgets.QLineEdit(box) for _ in range(4))
        for edit in (self.txtXmin, self.txtXmax, self.txtYmin, self.txtYmax):
            edit.setValidator(validator)
            edit.setMinimumWidth(80)
            edit.editingFinished.connect(self._on_limits_typed)
        self.cmdDefaultRange = QtWidgets.QPushButton("Default range", box)
        self.cmdDefaultRange.setToolTip("Range of the loaded data + 5% margin (q and intensity)")
        grid.addWidget(QtWidgets.QLabel("x min/max:", box), 0, 0)
        grid.addWidget(self.txtXmin, 0, 1)
        grid.addWidget(self.txtXmax, 0, 2)
        grid.addWidget(QtWidgets.QLabel("y min/max:", box), 1, 0)
        grid.addWidget(self.txtYmin, 1, 1)
        grid.addWidget(self.txtYmax, 1, 2)
        grid.addWidget(self.cmdDefaultRange, 0, 3, 2, 1)
        grid.setColumnStretch(4, 1)
        if self.plotBox.layout() is not None:
            self.plotBox.layout().addWidget(box)
        self.cmdDefaultRange.clicked.connect(self._apply_fixed_preset)
        self._limits_initialized = False
        self._show_present_in_fields()

    def _show_present_in_fields(self):
        for edit, value in zip((self.txtXmin, self.txtXmax, self.txtYmin, self.txtYmax), (*self._default_limits()[0],*self._default_limits()[1])):
            edit.setText(f"{value:.4g}")

    def _connect_limit_callbacks(self):
        ax = self._ax()
        if ax is None or ax.callbacks is self._callback_registry:
            return
        self._callback_registry = ax.callbacks
        ax.callbacks.connect('xlim_changed', self._on_limits_changed_by_user)
        ax.callbacks.connect('ylim_changed', self._on_limits_changed_by_user)

    def _set_limits(self, xlim, ylim):
        ax =self._ax()
        if ax is None:
            return
        self._setting_limits = True
        try:
            if xlim:
                ax.set_xlim(xlim)
            if ylim:
                ax.set_ylim(ylim)
        finally:
            self._setting_limits = False
        self._show_limits()

    def _show_limits(self):
        ax = self._ax()
        if ax is None:
            return
        for edit, value in zip((self.txtXmin, self.txtXmax, self.txtYmin, self.txtYmax), (*ax.get_xlim(), *ax.get_ylim())):
            edit.setText(f"{value:.4g}")

    def _apply_fixed_preset(self):
        self._set_limits(*self._default_limits())
        if self._ax() is not None:
            self.plotter.canvas.draw_idle()

    def _default_limits(self):
        xlim = ylim = None
        data = getattr(self, '_data', None)
        if data is not None:
            xlim = self._padded_range(data.x, self._is_log('x'))
            ylim = self._padded_range(data.y,self._is_log('y'))
        return xlim or FIXED_XLIM, ylim or FIXED_YLIM
    
    @staticmethod

    def _padded_range(values, log_axis):
        if values is None:
            return None
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        if log_axis:
            values = values[values > 0]
        if values.size == 0:
            return None
        lo, hi = float(values.min()), float(values.max())
        lo, hi = lo - DATA_MARGIN*abs(lo), hi + DATA_MARGIN*abs(hi)
        return (lo, hi) if hi > lo else None

    def _is_log(self, axis):
        ax = self._ax()
        if ax is None:
            return True
        return (ax.get_xscale() if axis == 'x' else ax.get_yscale()) == 'log'

    def _on_limits_changed_by_user(self, ax):
        if self._setting_limits:
            return
        self._show_limits()

    def _on_limits_typed(self):
        ax = self._ax()
        if ax is None:
            return
        try:
            x0, x1, y0, y1 = (float(e.text()) for e in
                              (self.txtXmin, self.txtXmax, self.txtYmin, self.txtYmax))
        except ValueError:
            return
        invalid = x1 <= x0 or y1 <= y0 or \
            (ax.get_xscale() == 'log' and x0 <= 0) or (ax.get_yscale() == 'log' and y0 <= 0)
        if invalid:
            self._show_limits()
            return
        self._set_limits((x0, x1), (y0, y1))
        self.plotter.canvas.draw_idle()
    
    def closeEvent(self, event):
        self._update_timer.stop()
        super().closeEvent(event)        
            
    def _apply_to_fitpage(self):
        if self._fw is None:
            return
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
        QtWidgets.QApplication.processEvents()

        if hasattr(self, '_update_timer'):
            self._update_timer.stop()

    def onHelp(self):
        if not HELP_SYSTEM.path:
            logger.error("Help documentation was not found.")
            return
        base = HELP_SYSTEM.path
        help_location = base / "user" / "qtgui" / "Perspectives" / "Fitting" / "inview.html"
        if not help_location.exists():
            help_location = base / "user" / "qtgui" / "Perspectives" / "Fitting" / "fitting_help.html"
        self._help_window = GuiUtils.showHelp(help_location)

"""
ParameterSliderWidget - a single slider row bound to one fitting parameter.

The widget works purely in the float domain and knows nothing about sasmodels
or FittingWidget. FittingWidget binds it to the parameter selected in the
main parameter table and writes the emitted values back into that table.
"""
import math

from PySide6 import QtCore, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.BackgroundColor import BG_DEFAULT, BG_ERROR

NO_SELECTION_REASON = "Select a single parameter in the table to enable the slider."


class _FocusWheelSlider(QtWidgets.QSlider):
    """Slider that ignores the mouse wheel unless it has keyboard focus,
    so scrolling the panel over it does not change a parameter."""

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class ParameterSliderWidget(QtWidgets.QWidget):
    """
    Name label, min box, slider, max box and value read-out in one row.
    """
    valueChanged = QtCore.Signal(str, float)          # (name, value) on every user tick
    rangeChanged = QtCore.Signal(str, float, float)   # (name, min, max) after a valid range edit
    rangeRejected = QtCore.Signal(str)                # message for the status bar

    STEPS = 1000
    # Smallest step, relative to the range end points, that still changes the
    # 5-significant-digit value shown in the parameter table.
    MIN_RELATIVE_STEP = 1e-4

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._name: str | None = None
        self._units = ""
        self._value = 0.0
        self._range = (0.0, 1.0)
        self._limits = (-math.inf, math.inf)

        # Created in visual order, which is also the default tab order
        self.lblSliderName = QtWidgets.QLabel()
        self.lblSliderName.setMinimumWidth(90)
        self.txtSliderMin = self._createRangeBox()
        self.sldParameter = _FocusWheelSlider(QtCore.Qt.Horizontal)
        self.sldParameter.setRange(0, self.STEPS)
        self.sldParameter.setSingleStep(self.STEPS // 100)
        self.sldParameter.setPageStep(self.STEPS // 10)
        self.sldParameter.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.sldParameter.valueChanged.connect(self._onSliderMoved)
        self.txtSliderMax = self._createRangeBox()
        self.lblSliderValue = QtWidgets.QLabel()
        self.lblSliderValue.setMinimumWidth(90)
        self.lblSliderValue.setTextFormat(QtCore.Qt.RichText)

        self.lblSliderName.setAccessibleName("Slider parameter")
        self.txtSliderMin.setAccessibleName("Slider minimum")
        self.sldParameter.setAccessibleName("Parameter slider")
        self.txtSliderMax.setAccessibleName("Slider maximum")
        self.lblSliderValue.setAccessibleName("Slider value")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for control in self._controls():
            layout.addWidget(control, 1 if control is self.sldParameter else 0)

        self.unbind()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bind(self, name: str, value: float, vmin: float, vmax: float,
             hard_min: float, hard_max: float, units: str = "") -> None:
        """Attach the slider to parameter *name* with range [vmin, vmax]."""
        self._name = name
        self._units = GuiUtils.convertUnitToHTML(units)
        self._limits = (hard_min, hard_max)
        self.lblSliderName.setText(name)
        self.lblSliderName.setToolTip(
            "Parameter controlled by the slider. "
            "Select a single row in the table above to change it.")
        self.txtSliderMin.setToolTip(
            "Lower end of the slider range. Defaults to the current value minus 100 %. "
            "Press Enter to apply.")
        self.txtSliderMax.setToolTip(
            "Upper end of the slider range. Defaults to the current value plus 100 %. "
            "Press Enter to apply.")
        self.sldParameter.setToolTip(
            f"Drag to change {name}. The table and the plot update as you drag. "
            "Arrow keys step by 1 %, Page Up/Down by 10 %. "
            "The mouse wheel works only while the slider has focus.")
        self.lblSliderValue.setToolTip(f"Current value of {name}.")
        self._setControlsEnabled(True)
        self.setRange(vmin, vmax)
        self.setValue(value)

    def unbind(self, reason: str = NO_SELECTION_REASON) -> None:
        """Detach the slider and show *reason* on every control."""
        self._name = None
        self.lblSliderName.setText("Select a parameter")
        self.lblSliderValue.setText("")
        for box in (self.txtSliderMin, self.txtSliderMax):
            box.clear()
            box.setStyleSheet(BG_DEFAULT)
        for control in self._controls():
            control.setToolTip(reason)
        self._setControlsEnabled(False)

    def setValue(self, value: float) -> None:
        """Move the knob to *value* without emitting valueChanged."""
        self._value = value
        vmin, vmax = self._range
        position = round((value - vmin) / (vmax - vmin) * self.STEPS)
        self.sldParameter.blockSignals(True)
        self.sldParameter.setValue(min(max(position, 0), self.STEPS))
        self.sldParameter.blockSignals(False)
        self._showValue()

    def setRange(self, vmin: float, vmax: float) -> None:
        """Set the slider range without emitting rangeChanged."""
        self._range = (vmin, vmax)
        for box, end in ((self.txtSliderMin, vmin), (self.txtSliderMax, vmax)):
            box.setText(GuiUtils.formatNumber(end, high=True))
            box.setStyleSheet(BG_DEFAULT)
        self.setValue(self._value)

    def isBound(self) -> bool:
        return self._name is not None

    def name(self) -> str | None:
        return self._name

    def value(self) -> float:
        return self._value

    def range(self) -> tuple[float, float]:
        return self._range

    @classmethod
    def defaultRange(cls, value: float, hard_min: float, hard_max: float) -> tuple[float, float] | None:
        """
        Return [value - |value|, value + |value|] ([-1, 1] for zero) clipped to
        the hard limits, widened to value +/- 1 if the clip collapses it.
        Returns None if no valid range exists.
        """
        span = abs(value) or 1.0
        vmin, vmax = max(value - span, hard_min), min(value + span, hard_max)
        if vmin >= vmax:
            vmin, vmax = max(value - 1.0, hard_min), min(value + 1.0, hard_max)
        result = cls.validateRange(vmin, vmax, hard_min, hard_max)
        return None if isinstance(result, str) else result

    @classmethod
    def validateRange(cls, vmin: float, vmax: float,
                      hard_min: float, hard_max: float) -> tuple[float, float] | str:
        """Return the (possibly swapped) range, or a message explaining why it is invalid."""
        if not (math.isfinite(vmin) and math.isfinite(vmax)):
            return "Slider limits must be finite numbers."
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if vmin == vmax:
            return "Slider minimum and maximum must differ."
        if vmin < hard_min or vmax > hard_max:
            return (f"Slider limits must lie within [{GuiUtils.formatNumber(hard_min, high=True)}, "
                    f"{GuiUtils.formatNumber(hard_max, high=True)}].")
        if (vmax - vmin) / cls.STEPS < cls.MIN_RELATIVE_STEP * max(abs(vmin), abs(vmax)):
            return "Slider range is too narrow for the table's display precision."
        return vmin, vmax

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _createRangeBox(self) -> QtWidgets.QLineEdit:
        # No QValidator: it would suppress editingFinished for intermediate
        # text such as "-" and leave bad text in the box silently.
        box = QtWidgets.QLineEdit()
        box.setMaximumWidth(80)
        box.setAlignment(QtCore.Qt.AlignRight)
        box.editingFinished.connect(lambda: self._onRangeEdited(box))
        return box

    def _controls(self) -> list[QtWidgets.QWidget]:
        return [self.lblSliderName, self.txtSliderMin, self.sldParameter,
                self.txtSliderMax, self.lblSliderValue]

    def _setControlsEnabled(self, enabled: bool) -> None:
        for control in self._controls():
            control.setEnabled(enabled)

    def _showValue(self) -> None:
        if self._name is not None:
            self.lblSliderValue.setText(
                f"{GuiUtils.formatNumber(self._value, high=True)} {self._units}".strip())

    def _onSliderMoved(self, position: int) -> None:
        if self._name is None:
            return
        vmin, vmax = self._range
        self._value = vmin + position * (vmax - vmin) / self.STEPS
        self._showValue()
        self.valueChanged.emit(self._name, self._value)

    def _onRangeEdited(self, box: QtWidgets.QLineEdit) -> None:
        # editingFinished fires on Enter and on focus loss; act only on real edits
        if self._name is None or not (self.txtSliderMin.isModified() or self.txtSliderMax.isModified()):
            return
        try:
            candidate = (GuiUtils.toDouble(self.txtSliderMin.text()),
                         GuiUtils.toDouble(self.txtSliderMax.text()))
        except TypeError:
            result = "Slider limits must be numbers."
        else:
            result = self.validateRange(*candidate, *self._limits)

        if isinstance(result, str):
            self.setRange(*self._range)  # restore the previous text
            box.setStyleSheet(BG_ERROR)
            self.rangeRejected.emit(result)
            return

        self.setRange(*result)
        self.rangeChanged.emit(self._name, *result)
        vmin, vmax = result
        if not vmin <= self._value <= vmax:
            # Clamp through the normal value path so the change is undoable
            self.setValue(min(max(self._value, vmin), vmax))
            self.valueChanged.emit(self._name, self._value)

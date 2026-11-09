"""
Document to the page settings widgets (FW-MVC-DESIGN.md §4.3, Phases 5 and 6): the model
selection (category, model and structure-factor combo boxes, the 2D view), fit options,
smearing, the polydispersity, magnetism and chain-fit toggles, and the Fit button.

The widgets keep their .ui files. On a document-first change the sync writes the
widget, and the page fields the legacy readers use, and applies a toggle's side
effects (``FittingWidget.apply*``). After a layout change the page refreshes what
depends on it (``FittingWidget.onLayoutChanged``). Runs through ``controller.subscribe_view``.
"""
from __future__ import annotations

from sas.qtgui.Perspectives.Fitting.model.events import (
    DataChanged,
    FlagsChanged,
    ModelChanged,
    OptionsChanged,
    ParametersChanged,
    SmearingChanged,
)
from sas.qtgui.Utilities import GuiUtils


class SettingsSync:

    def __init__(self, page) -> None:
        self._page = page
        self.subscription = page.controller.subscribe_view(self._on_change)

    def _on_change(self, change) -> None:
        if change.get(ModelChanged) is not None:
            self._page.showSelection(self._page.document.selection, self._page.document.flags.view_2d)
            self._page.onLayoutChanged()
        if change.get(OptionsChanged) is not None:
            self._options()
        if change.get(SmearingChanged) is not None:
            self._smearing()
        if change.get(FlagsChanged) is not None:
            self._flags()
        parameters = change.get(ParametersChanged)
        if (any(change.get(e) is not None for e in (ModelChanged, FlagsChanged, DataChanged))
                or (parameters is not None and parameters.fields & {"fit", "fittable"})):
            self._page.cmdFit.setEnabled(self._page.haveParamsToFit())

    def _options(self) -> None:
        page, o = self._page, self._page.document.options
        page.q_range_min, page.q_range_max, page.npts = o.qmin, o.qmax, o.npts
        page.log_points, page.weighting = o.log_points, o.theory_weighting
        page.options_widget.setState(o.qmin, o.qmax, o.npts, o.log_points, o.fit_weighting)
        page.lblMinRangeDef.setText(GuiUtils.formatNumber(o.qmin, high=True))
        page.lblMaxRangeDef.setText(GuiUtils.formatNumber(o.qmax, high=True))

    def _smearing(self) -> None:
        page, s = self._page, self._page.document.smearing
        widget = page.smearing_widget
        if widget.cbSmearing.currentText() != s.mode:
            widget.cbSmearing.setCurrentIndex(widget.cbSmearing.findText(s.mode))
        widget.setState(s.accuracy or None, s.d_down, s.d_up)
        page.lblCurrentSmearing.setText(s.mode)

    def _flags(self) -> None:
        page, f = self._page, self._page.document.flags
        for checkbox, value, applied, apply in (
                (page.chkPolydispersity, f.polydispersity, page.polydispersity_widget.isActive,
                 page.applyPolydispersity),
                (page.chkMagnetism, f.magnetism, page.magnetism_widget.isActive, page.applyMagnetism),
                (page.chkChainFit, f.chain_fit, page.is_chain_fitting, page.applyChainFit)):
            if checkbox.isChecked() != value:
                checkbox.blockSignals(True)
                checkbox.setChecked(value)
                checkbox.blockSignals(False)
            if applied != value:
                apply(value)

"""
Document to legacy kernel (FW-MVC-DESIGN.md §6, Phase 4). Temporary: removed in Phase 6,
once nothing but the services reads ``logic.kernel_module``.

Pushes document-first parameter changes into the stores outside the item models
that the legacy readers still use:

- ``logic.kernel_module``: values, bounds (``details``), dispersions, the name;
- the polydispersity and magnetism widgets' value dicts (``poly_params``,
  ``magnet_params``), which ``updateKernelModelWithExtraParams`` applies;
- the lists of parameters to fit, ``page_parameters`` (model-switch retention)
  and the Fit button.

Subscribed before the table adapters, which read the kernel's dispersion
(``updateFunctionCaption``). Like them, it runs through
``DocumentShadow.subscribe_reverse``.
"""
from __future__ import annotations

import numpy as np

from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.qtgui.Perspectives.Fitting.model.events import IdentityChanged, ParametersChanged
from sas.qtgui.Perspectives.Fitting.model.parameters import Table, ValueKind


class LegacyKernelSync:

    def __init__(self, page) -> None:
        self._page = page
        self.subscription = page.shadow.subscribe_reverse(self._on_change)

    def _on_change(self, change) -> None:
        page = self._page
        kernel = page.logic.kernel_module
        if kernel is None:
            return
        doc = page.document
        if change.get(IdentityChanged) is not None:
            kernel.name = doc.identity.mnemonic
        parameters = change.get(ParametersChanged)
        if parameters is None:
            return
        for key in parameters.keys:
            if key in doc.parameters:
                self._push(kernel, doc.parameters[key], parameters.fields)
        if "fit" in parameters.fields:
            params = doc.parameters
            page.main_params_to_fit = [params.legacy_key(p.key) for p in params.by_table(Table.MAIN) if p.fit]
            page.polydispersity_widget.poly_params_to_fit = [p.key for p in params.by_table(Table.POLY) if p.fit]
            page.magnetism_widget.magnet_params_to_fit = [p.key for p in params.by_table(Table.MAGNET) if p.fit]
            page.cmdFit.setEnabled(page.haveParamsToFit())
        if parameters.fields & {"value", "dispersion"}:
            page.page_parameters = page.getParameterDict()

    def _push(self, kernel, p, fields) -> None:
        if p.kind is ValueKind.INT:
            return    # the shell count is part of the layout, which the legacy code builds
        page = self._page
        values = {}
        if "value" in fields:
            values[p.key] = p.value
        if "dispersion" in fields and p.dispersion is not None:
            name = p.key[:-len(".width")]
            d = p.dispersion
            if d.array is not None or kernel.dispersion[name]["type"] != d.type:
                distribution = POLYDISPERSITY_MODELS[d.type]()
                if d.array is not None:
                    distribution.set_weights(np.array(d.array.x), np.array(d.array.w))
                kernel.set_dispersion(name, distribution)
            values.update({f"{name}.npts": d.npts, f"{name}.nsigmas": d.nsigmas})
        for key, value in values.items():
            # While polydispersity is off the kernel's widths stay 0 (togglePoly); poly_params keeps them
            if not (key == p.key and p.table is Table.POLY and not page.polydispersity_widget.isActive):
                kernel.setParam(key, value)
        if p.table is Table.POLY:
            page.polydispersity_widget.poly_params.update(values)
        elif p.table is Table.MAGNET:
            page.magnetism_widget.magnet_params.update(values)
        if p.min is not None and p.key in kernel.details:
            if "min" in fields:
                kernel.details[p.key][1] = p.min
            if "max" in fields:
                kernel.details[p.key][2] = p.max

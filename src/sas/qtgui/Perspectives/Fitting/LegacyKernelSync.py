"""
Document to legacy kernel (FW-MVC-DESIGN.md §6, Phases 4 and 6). Temporary: removed in
Phase 7, once nothing but the services reads ``logic.kernel_module``.

After every committed change, read-backs included, ``logic.kernel_module`` holds the
document's effective state, so the readers that still use it see the committed state.
It is a new instance (``KernelBuilder.build``) when the selection changes, as it was
when the legacy builders made it; otherwise the state is pushed into the same instance
(``KernelBuilder.apply``), because the smearer evaluates the instance it was built with.
``logic.model_parameters`` and ``logic.current_shell_displayed`` follow the selection.
Subscribed first, before the table adapters and the settings sync, which may read the kernel.
"""
from __future__ import annotations

from sas.qtgui.Perspectives.Fitting.model.events import DataChanged, FlagsChanged, ModelChanged, ParametersChanged


class LegacyKernelSync:

    def __init__(self, page) -> None:
        self._page = page
        self._built = None      # (logic, selection, layout generation) the kernel was built for
        self.subscription = page.document.subscribe(self._on_change)

    def _on_change(self, change) -> None:
        page = self._page
        doc = page.document
        logic = page.logic
        built = (logic, doc.selection, doc.parameters.layout_generation)
        if logic.kernel_module is None or not len(doc.parameters) or built != self._built:
            logic.kernel_module = page.kernel_builder.build(doc)
            self._built = built
        else:
            page.kernel_builder.apply(logic.kernel_module, doc)
        selection = doc.selection
        source = selection.model if selection.model in page.models else selection.structure
        logic.model_parameters = page.models[source]._model_info.parameters if source in page.models else None
        logic.current_shell_displayed = selection.multiplicity or 0
        parameters = change.get(ParametersChanged)
        if (any(change.get(e) is not None for e in (ModelChanged, FlagsChanged, DataChanged))
                or (parameters is not None and parameters.fields & {"fit", "fittable"})):
            page.cmdFit.setEnabled(page.haveParamsToFit())

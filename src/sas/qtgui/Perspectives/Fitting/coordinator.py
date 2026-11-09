"""
FitPerspectiveCoordinator (FW-MVC-DESIGN.md §3.5, Phase 7): the only owner of operations
that span the fit pages of the perspective. Qt-free; the perspective owns it.

- **Rename** a page: the name must be non-empty and unique; the page takes it, and the
  constraint expressions of every page follow (one ``SYSTEM`` transaction per page).
  Not undoable, as before.
- **Invalidation** (§9.2 C-1): when a page's layout changes, or the page closes, the active
  constraints of the *other* pages that referred to a parameter it no longer has are
  deactivated and reported, neither left dangling nor deleted. A page without a model is
  not checked: a category switch empties the layout until the model is chosen.
- **Simultaneous fit**: the pages' fit problems go into one shared ``Fit``; the results are
  routed back to the pages by page id, in the order the problems were set up.

The constraint tab (``ConstraintWidget``) holds the rest of the cross-page UI until Phase 8.
"""
from __future__ import annotations

from collections.abc import Callable

from sas.qtgui.Perspectives.Fitting.model.events import ModelChanged


class FitPerspectiveCoordinator:

    def __init__(self, pages: Callable[[], list], status: Callable[[str], None],
                 changed: Callable[[], None] = lambda: None) -> None:
        self._pages = pages              # the open fit pages
        self._status = status            # a status-bar message
        self._changed = changed          # constraints of some page changed (the constraint tab refreshes)
        self._subscriptions: dict[int, object] = {}
        self._fit_pages: list[int] = []  # page ids of the running simultaneous fit, in problem order

    # -- pages ------------------------------------------------------------

    def add_page(self, page) -> None:
        def on_change(change) -> None:
            if change.get(ModelChanged) is not None and len(page.document.parameters):
                # After the page has published: the other pages may then be changed freely
                page.document.after_publish(lambda: self._invalidate(page))
        self.remove_subscription(page)
        self._subscriptions[id(page)] = page.document.subscribe(on_change)

    def remove_subscription(self, page) -> None:
        subscription = self._subscriptions.pop(id(page), None)
        if subscription is not None:
            subscription.dispose()

    def remove_page(self, page) -> None:
        """The page closed: its requests are cancelled, and constraints on it are deactivated."""
        self.remove_subscription(page)
        page.controller.close()
        self._invalidate(page, closing=True)

    def _invalidate(self, page, closing: bool = False) -> None:
        mnemonic = page.document.identity.mnemonic
        others = [p for p in self._pages() if p is not page]
        symbols = {}
        for p in others if closing else others + [page]:
            symbols.update(p.document.symbol_table())
        deactivated = [name for p in others for name in p.controller.deactivate_dangling(mnemonic, symbols)]
        if deactivated:
            self._status(f"Constraints deactivated: {', '.join(deactivated)} "
                         f"refer to parameters of {mnemonic} that no longer exist.")
            self._changed()

    # -- rename -----------------------------------------------------------

    def rename(self, page, mnemonic: str) -> str | None:
        """Give *page* the name *mnemonic*; returns why not, if it cannot be."""
        if not mnemonic:
            return "Please use a non-empty name."
        old = page.document.identity.mnemonic
        if any(p is not page and p.document.identity.mnemonic == mnemonic for p in self._pages()):
            return "Please use a unique name."
        page.controller.rename(mnemonic, old)
        for p in self._pages():
            if p is not page:
                p.controller.replace_page_name(old, mnemonic)
        return None

    # -- simultaneous fit -------------------------------------------------

    def prepare_simultaneous_fit(self, fitter, pages_and_weights) -> list:
        """Set up the fit problems of the pages, each with its weight increase, in *fitter*.
        Returns the Fit objects; ValueError if a page has nothing to fit."""
        fit_id = 0
        fitters = [fitter]
        self._fit_pages = []
        for page, weight_increase in pages_and_weights:
            fitters, fit_id = page.prepareFitters(fitter=fitter, fit_id=fit_id, weight_increase=weight_increase)
            self._fit_pages.append(page.page_id)
        return fitters

    def fit_pages(self) -> list[list[int]]:
        """The page ids of the simultaneous fit, as FitThread takes them."""
        return [[page_id] for page_id in self._fit_pages]

    def route_fit_results(self, results: list, elapsed: float) -> None:
        """Each page gets its result, by page id; a page closed during the fit gets nothing."""
        pages = {p.page_id: p for p in self._pages()}
        for page_id, result in zip(self._fit_pages, results):
            page = pages.get(page_id)
            if page is not None and result.model.name == page.document.identity.mnemonic:
                page.fitComplete(([[result]], elapsed))

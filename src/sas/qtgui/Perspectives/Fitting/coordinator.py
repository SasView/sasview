"""
FitPerspectiveCoordinator (FW-MVC-DESIGN.md §3.5, Phases 7 and 8): the only owner of operations
that span the fit pages of the perspective. Qt-free; the perspective owns it.

- **Rename** a page: the name must be non-empty and unique; the page takes it, and the
  constraint expressions of every page follow (one ``SYSTEM`` transaction per page).
  Not undoable, as before.
- **Constraints** across pages: the symbols of every page, the active constraints, and a new
  constraint, checked against them (unknown symbols, syntax, cycles) before the page takes it.
  A change of any page's constraints refreshes the constraint tab (``changed``).
- **Invalidation** (§9.2 C-1): when a page's layout changes, or the page closes, the active
  constraints of the *other* pages that referred to a parameter it no longer has are
  deactivated and reported, neither left dangling nor deleted. A page without a model is
  not checked: a category switch empties the layout until the model is chosen.
- **Simultaneous fit**: the pages' fit problems go into one shared ``Fit``; the results are
  routed back to the pages by page id, in the order the problems were set up.
"""
from __future__ import annotations

from collections.abc import Callable

from sas.qtgui.Perspectives.Fitting.model.events import ConstraintsChanged, ModelChanged
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service


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
            # After the page has published: the other pages may then be changed freely
            if change.get(ModelChanged) is not None and len(page.document.parameters):
                page.document.after_publish(lambda: self._invalidate(page))
            if change.get(ConstraintsChanged) is not None:
                page.document.after_publish(self._changed)
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
        symbols = self.symbols(exclude=page)
        if not closing:
            symbols.update(page.document.symbol_table())
        deactivated = [name for p in others for name in p.controller.deactivate_dangling(mnemonic, symbols)]
        if deactivated:
            self._status(f"Constraints deactivated: {', '.join(deactivated)} "
                         f"refer to parameters of {mnemonic} that no longer exist.")
            self._changed()

    # -- constraints --------------------------------------------------------

    def symbols(self, exclude=None) -> dict[str, float]:
        """The constraint symbols of the open pages ({'M1.scale': 1.0, ...}), but *exclude*'s."""
        table: dict[str, float] = {}
        for p in self._pages():
            if p is not exclude:
                table.update(p.document.symbol_table())
        return table

    def active_constraints(self) -> list[tuple[str, str]]:
        """(qualified parameter, expression) of the active constraints of the open pages,
        e.g. ('M1.scale', 'M2.scale + 2')."""
        return [(f"{p.document.identity.mnemonic}.{name}", expression)
                for p in self._pages() for name, expression in constraint_service.active(p.document)]

    def add_constraint(self, page, key: str, constraint):
        """Put *constraint* on *page*'s parameter *key*, if it evaluates with the symbols and the
        other constraints of every page; the constrained parameter is fitted (it is computed from
        the others while fitting). Returns the errors (html), or an empty list."""
        qualified = f"{page.document.identity.mnemonic}.{constraint.param}"
        symbols = {**self.symbols(), **page.document.symbol_table()}
        errors = constraint_service.validate(symbols, self.active_constraints() + [(qualified, constraint.func)])
        if not errors:
            page.controller.set_constraint(key, constraint, fit=True)
            self._status("Constraint added")
        return errors

    # -- rename -----------------------------------------------------------

    def check_name(self, page, mnemonic: str) -> str | None:
        """Why *page* (None: a new page) cannot be called *mnemonic*, or None."""
        if not mnemonic:
            return "Please use a non-empty name."
        if any(p is not page and p.document.identity.mnemonic == mnemonic for p in self._pages()):
            return "Please use a unique name."
        return None

    def rename(self, page, mnemonic: str) -> str | None:
        """Give *page* the name *mnemonic*; returns why not, if it cannot be."""
        error = self.check_name(page, mnemonic)
        if error is not None:
            return error
        old = page.document.identity.mnemonic
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
            fitters, fit_id = page.controller.prepare_fitters(fitter, fit_id, weight_increase)
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

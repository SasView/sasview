"""
Common base for the dialogs listed in the Tools menu.

The registry of tools lives in ``sas.qtgui.MainWindow.tools``. This module only
holds the mixin, so that tool modules can import it without importing the
registry (which imports every tool).
"""
from typing import TYPE_CHECKING, ClassVar

import sas.qtgui.Utilities.GuiUtils as GuiUtils

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from sas.data_manager import NewDataManager


class CalculatorTool:
    """Mixin for Tools-menu dialogs.

    It must come FIRST among the bases, so its ``__init__`` runs and passes the
    parent on to the Qt class::

        class SldPanel(CalculatorTool, QtWidgets.QDialog): ...
        class KiessigPanel(CalculatorTool, QtWidgets.QDialog, Ui_KiessigPanel): ...

    The generated ``Ui_*`` classes have no ``__init__``, so they can sit after
    the Qt class.

    Rules for tools:

    * Construct with ``(parent=None, *, data_manager=None)``. The host passes
      the main window as ``parent``, not the GuiManager.
    * Don't store the host as ``self.parent``, ``self.manager``, ``self._parent``
      or ``self._manager``. Use ``self.parent()`` for the Qt parent.
    * Set ``help_url`` as a class attribute. ``onHelp`` opens it.
    * Data going in or out uses ``sasdata`` types and ``self.data_manager``.
      When ``data_manager`` is None (as in tests), disable controls that need it.
    * Don't subscribe to global signals in ``__init__``.
    """

    help_url: ClassVar[str | None] = None

    def __init__(self, parent: "QWidget | None" = None, *args, data_manager: "NewDataManager | None" = None, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data_manager = data_manager

    def onHelp(self):
        """Open this tool's page in the documentation."""
        if self.help_url:
            GuiUtils.showHelp(self.help_url)

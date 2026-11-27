"""
Registry of the calculator dialogs in the Tools menu.

To add a tool: write a dialog that uses ``CalculatorTool``
(``sas.qtgui.Calculators.calculator_tool``) and add a ``ToolSpec`` to ``TOOLS``.
The menu entries are generated from this list, in this order, directly after
the Data Operation entry. The other Tools-menu entries (Data Operation,
MuMag, GSC, the viewers and the Python shell) are still defined in
``MainWindowUI.ui``.
"""
import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from sas.qtgui.Calculators.DensityPanel import DensityPanel
from sas.qtgui.Calculators.KiessigPanel import KiessigPanel
from sas.qtgui.Calculators.ResolutionCalculatorPanel import ResolutionCalculatorPanel
from sas.qtgui.Calculators.Shape2SAS.DesignWindow import DesignWindow as Shape2SAS
from sas.qtgui.Calculators.SldPanel import SldPanel
from sas.qtgui.Calculators.SlitSizeCalculator import SlitSizeCalculator
from sas.qtgui.Utilities.FileConverter import FileConverterWidget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolSpec:
    id: str
    menu_text: str
    cls: type


SEPARATOR = None

TOOLS: list[ToolSpec | None] = [
    ToolSpec("file_converter", "File Converter", FileConverterWidget),
    SEPARATOR,
    ToolSpec("sld", "SLD Calculator", SldPanel),
    ToolSpec("density", "Density/Volume Calculator", DensityPanel),
    ToolSpec("slit", "Slit Size Calculator", SlitSizeCalculator),
    ToolSpec("kiessig", "Kiessig Thickness Calculator", KiessigPanel),
    ToolSpec("resolution", "Q Resolution Estimator", ResolutionCalculatorPanel),
    ToolSpec("shape2sas", "Shape2SAS Calculator (Experimental)", Shape2SAS),
]


def build_tools_menu(menu: QMenu, after: QAction, open_tool: Callable[[ToolSpec], None]) -> list[QAction]:
    """Insert an action for each entry in ``TOOLS`` into ``menu``, right after ``after``.

    Returns the inserted actions, separators included.
    """
    actions = menu.actions()
    index = actions.index(after)
    anchor = actions[index + 1] if index + 1 < len(actions) else None
    inserted = []
    for spec in TOOLS:
        if spec is SEPARATOR:
            separator = QAction(menu)
            separator.setSeparator(True)
            menu.insertAction(anchor, separator)
            inserted.append(separator)
            continue
        action = QAction(spec.menu_text, menu)
        action.setObjectName(f"actionTool_{spec.id}")
        action.triggered.connect(partial(open_tool, spec))
        menu.insertAction(anchor, action)
        inserted.append(action)
    return inserted


class ToolWindows:
    """Creates each tool on first use and keeps it, so reopening shows the same window."""

    def __init__(self, parent, data_manager):
        self._parent = parent
        self._data_manager = data_manager
        self._tools = {}

    def get(self, spec: ToolSpec):
        """The tool's window, or None if it hasn't been opened yet."""
        return self._tools.get(spec.id)

    def open(self, spec: ToolSpec, *_):
        # *_ swallows the 'checked' argument of QAction.triggered.
        try:
            tool = self._tools.get(spec.id)
            if tool is None:
                tool = self._tools[spec.id] = spec.cls(self._parent, data_manager=self._data_manager)
            tool.show()
            tool.raise_()
            tool.activateWindow()
        except Exception:
            logger.exception("Unable to open %s", spec.menu_text)

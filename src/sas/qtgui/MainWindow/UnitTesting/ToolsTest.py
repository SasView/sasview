"""Tests for the Tools-menu registry (sas.qtgui.MainWindow.tools)."""
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from PySide6 import QtWidgets

from sas.qtgui.Calculators.calculator_tool import CalculatorTool
from sas.qtgui.MainWindow.tools import SEPARATOR, TOOLS, ToolSpec, ToolWindows, build_tools_menu

SPECS = [spec for spec in TOOLS if spec is not SEPARATOR]

# Shape2SAS's 3D viewer needs OpenGL and crashes the interpreter under the
# offscreen platform that the test suite uses (see conftest.py), so it is
# constructed in a separate process on the native platform instead.
OFFSCREEN_UNSAFE = {"shape2sas"}


@pytest.mark.parametrize("spec", [s for s in SPECS if s.id not in OFFSCREEN_UNSAFE], ids=lambda s: s.id)
def test_tool_constructs_and_follows_the_contract(qapp, spec):
    tool = spec.cls(None)
    try:
        assert isinstance(tool, CalculatorTool)
        assert isinstance(tool, QtWidgets.QWidget)
        assert tool.data_manager is None
        assert tool.help_url is not None and tool.help_url.startswith("/user/")
    finally:
        tool.close()


def _has_display() -> bool:
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


@pytest.mark.skipif(not _has_display(), reason="needs a display (Shape2SAS crashes under offscreen Qt)")
@pytest.mark.parametrize("spec", [s for s in SPECS if s.id in OFFSCREEN_UNSAFE], ids=lambda s: s.id)
def test_offscreen_unsafe_tool_constructs_in_a_subprocess(spec):
    # A crash here is a test failure, instead of ending the whole pytest run.
    module, name = spec.cls.__module__, spec.cls.__name__
    script = (
        "import sys\n"
        "from PySide6 import QtWidgets\n"
        "app = QtWidgets.QApplication(sys.argv)\n"
        "from sas.qtgui.Calculators.calculator_tool import CalculatorTool\n"
        f"from {module} import {name} as Tool\n"
        "tool = Tool(None)\n"
        "assert isinstance(tool, CalculatorTool)\n"
        "assert tool.help_url and tool.help_url.startswith('/user/')\n"
        "print('constructed')\n"
    )
    env = {key: value for key, value in os.environ.items() if key != "QT_QPA_PLATFORM"}
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, f"exit code {result.returncode}\n{result.stderr[-2000:]}"
    assert "constructed" in result.stdout


def test_tool_ids_and_menu_texts_are_unique():
    assert len({spec.id for spec in SPECS}) == len(SPECS)
    assert len({spec.menu_text for spec in SPECS}) == len(SPECS)


def test_menu_is_inserted_after_the_anchor_in_list_order(qapp):
    menu = QtWidgets.QMenu()
    first = menu.addAction("first")
    last = menu.addAction("last")
    opened = []

    build_tools_menu(menu, first, opened.append)

    actions = menu.actions()
    assert actions[0] is first
    assert actions[-1] is last
    inserted = actions[1:-1]
    assert len(inserted) == len(TOOLS)
    for action, spec in zip(inserted, TOOLS):
        if spec is SEPARATOR:
            assert action.isSeparator()
        else:
            assert action.text() == spec.menu_text
            assert action.objectName() == f"actionTool_{spec.id}"

    sld = next(a for a in inserted if a.objectName() == "actionTool_sld")
    sld.trigger()
    assert [spec.id for spec in opened] == ["sld"]


def test_menu_can_be_appended_after_the_last_action(qapp):
    menu = QtWidgets.QMenu()
    only = menu.addAction("only")
    build_tools_menu(menu, only, lambda spec: None)
    assert menu.actions()[0] is only
    assert len(menu.actions()) == 1 + len(TOOLS)


class _FakeTool(QtWidgets.QDialog):
    instances = 0

    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        _FakeTool.instances += 1


def test_tool_is_created_once_and_given_the_data_manager(qapp):
    _FakeTool.instances = 0
    data_manager = object()
    windows = ToolWindows(None, data_manager)
    spec = ToolSpec("fake", "Fake", _FakeTool)

    windows.open(spec, False)  # QAction.triggered passes 'checked'
    windows.open(spec)

    tool = windows.get(spec)
    assert _FakeTool.instances == 1
    assert tool.isVisible()
    assert tool.data_manager is data_manager
    tool.close()


def test_failing_tool_is_logged_not_raised(qapp, caplog):
    class Broken(QtWidgets.QDialog):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("boom")

    windows = ToolWindows(None, None)
    windows.open(ToolSpec("broken", "Broken", Broken))
    assert "Unable to open Broken" in caplog.text
    assert windows.get(ToolSpec("broken", "Broken", Broken)) is None


# Modules that have been moved off the legacy data classes. Add a tool here when
# its data migration lands; never remove one.
LEGACY_FREE = [
    "sas.qtgui.Calculators.calculator_tool",
    "sas.qtgui.MainWindow.tools",
    "sas.qtgui.Calculators.SldPanel",
    "sas.qtgui.Calculators.DensityPanel",
    "sas.qtgui.Calculators.KiessigPanel",
    "sas.qtgui.Calculators.ResolutionCalculatorPanel",
    "sas.qtgui.Calculators.Shape2SAS.DesignWindow",
]
LEGACY = re.compile(r"PlotterData|data_info|dataloader\.loader|sasdata\.file_converter|createModelItemWithPlot")


@pytest.mark.parametrize("module", LEGACY_FREE)
def test_module_does_not_use_legacy_data_classes(module):
    source = Path(importlib.util.find_spec(module).origin).read_text(encoding="utf-8")
    assert not LEGACY.search(source), f"{module} uses a legacy data class: {LEGACY.search(source).group()}"


def test_registered_menu_actions_have_no_ui_duplicates():
    # The .ui file must not still define actions for registered tools.
    ui = Path(importlib.util.find_spec("sas.qtgui.MainWindow").origin).parent / "UI" / "MainWindowUI.ui"
    text = ui.read_text(encoding="utf-8")
    for spec in SPECS:
        assert f"<string>{spec.menu_text}</string>" not in text, spec.menu_text

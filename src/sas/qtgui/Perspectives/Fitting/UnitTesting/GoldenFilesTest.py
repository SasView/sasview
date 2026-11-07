"""
Golden-file characterization of the fit page's legacy outputs (FW-MVC-DESIGN.md, Phase 0).

Every refactor phase must leave these outputs unchanged. To regenerate the
goldens after a deliberate behaviour change (one listed in the design's
decision register), run with ``SASVIEW_UPDATE_GOLDENS=1``.
"""
import os
from unittest.mock import MagicMock

import pytest

from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support

UPDATE = os.environ.get("SASVIEW_UPDATE_GOLDENS") == "1"


@pytest.fixture(autouse=True)
def _no_message_boxes(monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())


@pytest.mark.parametrize("case", sorted(golden_support.CASES))
def testGoldenOutputs(qapp, case):
    pages = golden_support.build_and_capture(case)
    if UPDATE:
        golden_support.write_golden(case, pages)
    expected = golden_support.load_golden(case)
    assert len(pages) == len(expected)
    for page, golden in zip(pages, expected):
        assert set(page) == set(golden)
        for key in golden:
            assert page[key] == golden[key], f"{case}: '{key}' differs from the golden file"

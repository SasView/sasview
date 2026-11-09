"""Tests for behaviour provided by the Perspective base class."""

import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest

from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
from sas.qtgui.Perspectives.Invariant.InvariantPerspective import InvariantWindow
from sas.qtgui.Perspectives.perspective import Perspective
from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionPerspective import SizeDistributionWindow


class _DialogPerspective(Perspective, QtWidgets.QDialog):
    """Minimal QDialog-based perspective, following the documented base-class order."""

    name = "Dummy"
    title = "Dummy"

    def setData(self, data_item=None, is_batch=False):
        pass

    def isSerializable(self):
        return False


class TestPerspectiveReject:
    """Esc must not hide a perspective - see issue #4001."""

    def testEscapeDoesNotHideWindow(self, qapp):
        window = _DialogPerspective()
        window.show()
        assert window.isVisible()
        QTest.keyClick(window, QtCore.Qt.Key_Escape)
        assert window.isVisible()

    @pytest.mark.parametrize("cls", [CorfuncWindow, InvariantWindow, SizeDistributionWindow])
    def testDialogPerspectivesUseBaseReject(self, cls):
        """QDialog-based perspectives must resolve reject() to the base-class override."""
        assert cls.reject is Perspective.reject

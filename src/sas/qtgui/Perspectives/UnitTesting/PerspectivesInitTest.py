"""
Tests for the lazily loaded perspective registry in ``sas.qtgui.Perspectives``.
"""
import subprocess
import sys

import pytest

# matplotlib's Qt backend, used by the perspective windows, needs a Qt binding
# imported first, as it is in the application.
from PySide6 import QtWidgets  # noqa: F401


def _run_isolated(code: str) -> subprocess.CompletedProcess:
    """Run *code* in a fresh interpreter, so sys.modules starts empty."""
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120
    )


class PerspectivesInitTest:
    """Test the lazy loading of the perspective windows."""

    def testImportDoesNotLoadPerspectives(self):
        """Importing the package or a submodule loads neither Qt nor any window."""
        code = (
            "import sys\n"
            "import sas.qtgui.Perspectives\n"
            "import sas.qtgui.Perspectives.Fitting.Constraint\n"
            "loaded = sorted(m for m in sys.modules\n"
            "                if m.startswith(('PySide6', 'matplotlib'))\n"
            "                or m.endswith('Perspective'))\n"
            "assert not loaded, loaded\n"
        )
        result = _run_isolated(code)
        assert result.returncode == 0, result.stderr

    def testRegistryContentsAndOrder(self):
        """PERSPECTIVES holds the same windows, in the same (menu) order, as before."""
        import sas.qtgui.Perspectives as Perspectives
        from sas.qtgui.Perspectives.Corfunc.CorfuncPerspective import CorfuncWindow
        from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
        from sas.qtgui.Perspectives.Invariant.InvariantPerspective import InvariantWindow
        from sas.qtgui.Perspectives.Inversion.InversionPerspective import InversionWindow
        from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionPerspective import (
            SizeDistributionWindow,
        )

        expected = [FittingWindow, InvariantWindow, InversionWindow,
                    CorfuncWindow, SizeDistributionWindow]
        assert list(Perspectives.PERSPECTIVES) == [w.name for w in expected]
        assert list(Perspectives.PERSPECTIVES.values()) == expected

    def testWindowClassesAreExported(self):
        """The window classes stay importable from the package."""
        import sas.qtgui.Perspectives as Perspectives
        from sas.qtgui.Perspectives import PERSPECTIVES, FittingWindow

        assert PERSPECTIVES is Perspectives.PERSPECTIVES
        assert PERSPECTIVES[FittingWindow.name] is FittingWindow
        for name in Perspectives.__all__:
            assert name in dir(Perspectives)

    def testUnknownAttributeRaises(self):
        """Names that are not in __all__ still raise AttributeError."""
        import sas.qtgui.Perspectives as Perspectives

        with pytest.raises(AttributeError):
            Perspectives.NoSuchPerspective

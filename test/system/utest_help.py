"""Unit tests for sas.system._help"""

from pathlib import Path, PurePosixPath
from unittest.mock import patch

from sas.system._help import _HelpSystem, _release_version


class PosixTestPath(PurePosixPath):
    """Pure POSIX path with the minimal filesystem API used by _HelpSystem."""

    def exists(self):
        return False


class TestReleaseVersion:
    """Tests for _release_version()"""

    def test_release_version(self):
        assert _release_version("6.1.2") == "6.1.2"

    def test_dev_version_stripped(self):
        assert _release_version("6.1.2.dev159+g77be83657") == "6.1.2"

    def test_pre_release_stripped(self):
        assert _release_version("6.2.0a1") == "6.2.0"

    def test_post_release_stripped(self):
        assert _release_version("6.1.2.post1") == "6.1.2"


class TestHelpSystemOnlineUrl:
    """Tests for _HelpSystem._online_url()"""

    def setup_method(self):
        self.hs = _HelpSystem()
        self.hs.path = None

    @patch("sas.system._help.HELP_SYSTEM")
    def test_online_url_basic(self, _mock):
        with patch("sas.system.version.__version__", "6.1.2"):
            url = self.hs._online_url(
                Path("user/qtgui/Perspectives/Fitting/fitting_help.html")
            )
        assert url == (
            "https://www.sasview.org/docs/v6.1.2"
            "/user/qtgui/Perspectives/Fitting/fitting_help.html"
        )

    def test_online_url_dev_version(self):
        with patch("sas.system.version.__version__", "6.1.2.dev159+g77be83657"):
            url = self.hs._online_url(
                Path("user/qtgui/Perspectives/Fitting/fitting_help.html")
            )
        assert url.startswith("https://www.sasview.org/docs/v6.1.2/")
        assert "+g77be83657" not in url
        assert ".dev159" not in url

    def test_online_url_with_fragment(self):
        with patch("sas.system.version.__version__", "6.1.2"):
            url = self.hs._online_url(
                Path("user/qtgui/Perspectives/Fitting/fitting_help.html"),
                "simultaneous-fits",
            )
        assert url.endswith("fitting_help.html#simultaneous-fits")

    def test_online_url_uses_posix_separators(self):
        with patch("sas.system.version.__version__", "6.1.2"):
            url = self.hs._online_url(
                Path("user") / "qtgui" / "Perspectives" / "Fitting" / "fitting_help.html"
            )
        assert "\\" not in url


class TestShowHelp:
    """Tests for _HelpSystem.show_help()"""

    def setup_method(self):
        self.hs = _HelpSystem()

    @patch("sas.system._help.webbrowser")
    def test_local_docs_opened(self, mock_wb, tmp_path):
        """When local docs exist, open them via file URI."""
        doc = tmp_path / "user" / "fitting.html"
        doc.parent.mkdir(parents=True)
        doc.write_text("<html></html>")

        self.hs.path = tmp_path
        self.hs.show_help("user/fitting.html")

        mock_wb.open.assert_called_once()
        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url.startswith("file:///")
        assert "fitting.html" in opened_url

    @patch("sas.system._help.webbrowser")
    def test_local_docs_with_fragment(self, mock_wb, tmp_path):
        """Fragment (#anchor) must be preserved for local files."""
        doc = tmp_path / "user" / "fitting.html"
        doc.parent.mkdir(parents=True)
        doc.write_text("<html></html>")

        self.hs.path = tmp_path
        self.hs.show_help("user/fitting.html#constraints")

        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url.endswith("#constraints")

    @patch("sas.system._help.webbrowser")
    def test_online_fallback_when_local_missing(self, mock_wb, tmp_path):
        """When local docs don't exist, fall back to online URL."""
        self.hs.path = tmp_path  # empty dir — no docs
        with patch("sas.system.version.__version__", "6.1.2"):
            self.hs.show_help("user/fitting.html")

        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url == (
            "https://www.sasview.org/docs/v6.1.2/user/fitting.html"
        )

    @patch("sas.system._help.webbrowser")
    def test_online_fallback_no_absolute_path_leak(self, mock_wb, tmp_path):
        """The online URL must never contain the local filesystem path."""
        self.hs.path = tmp_path
        with patch("sas.system.version.__version__", "6.1.2"):
            self.hs.show_help("user/fitting.html")

        opened_url = mock_wb.open.call_args[0][0]
        assert str(tmp_path) not in opened_url
        assert "C:" not in opened_url
        assert "Users" not in opened_url

    @patch("sas.system._help.webbrowser")
    def test_online_fallback_when_path_is_none(self, mock_wb):
        """When HELP_SYSTEM.path is None, fall back to online."""
        self.hs.path = None
        with patch("sas.system.version.__version__", "6.1.2"):
            self.hs.show_help("user/fitting.html")

        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url.startswith("https://www.sasview.org/docs/v6.1.2/")

    @patch("sas.system._help.webbrowser")
    def test_absolute_path_stripped_for_online(self, mock_wb, tmp_path):
        """If an absolute path under HELP_SYSTEM.path is passed, the local
        root should be stripped when building the online fallback URL."""
        self.hs.path = tmp_path  # empty — no local docs
        absolute_url = tmp_path / "user" / "fitting.html"
        with patch("sas.system.version.__version__", "6.1.2"):
            self.hs.show_help(str(absolute_url))

        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url == (
            "https://www.sasview.org/docs/v6.1.2/user/fitting.html"
        )

    @patch("sas.system._help.webbrowser")
    def test_posix_absolute_path_stripped_for_online(self, mock_wb):
        """POSIX absolute paths should also be reduced to doc-relative URLs."""
        self.hs.path = PosixTestPath("/tmp/sasview-docs")
        absolute_url = "/tmp/sasview-docs/user/fitting.html"

        with patch("sas.system._help.Path", PosixTestPath):
            with patch("sas.system.version.__version__", "6.1.2"):
                self.hs.show_help(absolute_url)

        opened_url = mock_wb.open.call_args[0][0]
        assert opened_url == (
            "https://www.sasview.org/docs/v6.1.2/user/fitting.html"
        )

    @patch("sas.system._help.webbrowser")
    def test_leading_slashes_stripped(self, mock_wb, tmp_path):
        """Leading slashes on the relative URL are stripped."""
        doc = tmp_path / "user" / "fitting.html"
        doc.parent.mkdir(parents=True)
        doc.write_text("<html></html>")

        self.hs.path = tmp_path
        self.hs.show_help("//user/fitting.html")

        opened_url = mock_wb.open.call_args[0][0]
        assert "fitting.html" in opened_url

    @patch("sas.system._help.webbrowser")
    def test_path_object_accepted(self, mock_wb, tmp_path):
        """A Path object should be accepted as input."""
        doc = tmp_path / "user" / "fitting.html"
        doc.parent.mkdir(parents=True)
        doc.write_text("<html></html>")

        self.hs.path = tmp_path
        self.hs.show_help(Path("user/fitting.html"))

        mock_wb.open.assert_called_once()

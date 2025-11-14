import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open
from collections import defaultdict

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtGui import QPixmap

from sas.qtgui.Utilities.WhatsNew.WhatsNew import WhatsNew, WhatsNewBrowser, whats_new_messages


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Create QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_config():
    """Mock the config module."""
    with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.config') as mock_cfg:
        mock_cfg.LAST_WHATS_NEW_HIDDEN_VERSION = "6.0.0"
        yield mock_cfg


@pytest.fixture
def mock_version():
    """Mock the sasview_version."""
    with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.sasview_version', '6.1.0'):
        yield


@pytest.fixture
def mock_resources():
    """Mock importlib.resources for testing."""
    with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
        yield mock_res


class TestWhatsNewMessages:
    """Tests for the whats_new_messages function."""

    def test_whats_new_messages_only_recent_true(self, mock_resources, mock_config):
        """Test whats_new_messages with only_recent=True."""
        # Setup mock directory structure
        mock_message_dir = MagicMock()
        mock_resources.files.return_value = mock_message_dir
        
        # Create mock directories for versions
        mock_dir_600 = MagicMock()
        mock_dir_600.is_dir.return_value = True
        mock_dir_600.name = "6.0.0"
        
        mock_dir_601 = MagicMock()
        mock_dir_601.is_dir.return_value = True
        mock_dir_601.name = "6.0.1"
        
        mock_dir_610 = MagicMock()
        mock_dir_610.is_dir.return_value = True
        mock_dir_610.name = "6.1.0"
        
        mock_message_dir.iterdir.return_value = [mock_dir_600, mock_dir_601, mock_dir_610]
        
        # Create mock HTML files
        mock_file1 = MagicMock()
        mock_file1.name = "feature1.html"
        
        mock_file2 = MagicMock()
        mock_file2.name = "feature2.html"
        
        mock_file_txt = MagicMock()
        mock_file_txt.name = "readme.txt"
        
        # Only 6.0.1 and 6.1.0 should be included (newer than 6.0.0)
        mock_dir_600.iterdir.return_value = []
        mock_dir_601.iterdir.return_value = [mock_file1, mock_file_txt]
        mock_dir_610.iterdir.return_value = [mock_file2]
        
        result = whats_new_messages(only_recent=True)
        
        # Should only include versions strictly newer than 6.0.0
        assert "6.0.0" not in result
        assert "6.0.1" in result
        assert "6.1.0" in result
        assert mock_file1 in result["6.0.1"]
        assert mock_file_txt not in result["6.0.1"]  # .txt files should be excluded
        assert mock_file2 in result["6.1.0"]

    def test_whats_new_messages_only_recent_false(self, mock_resources, mock_config):
        """Test whats_new_messages with only_recent=False."""
        # Setup mock directory structure
        mock_message_dir = MagicMock()
        mock_resources.files.return_value = mock_message_dir
        
        mock_dir_600 = MagicMock()
        mock_dir_600.is_dir.return_value = True
        mock_dir_600.name = "6.0.0"
        
        mock_message_dir.iterdir.return_value = [mock_dir_600]
        
        mock_file = MagicMock()
        mock_file.name = "test.html"
        mock_dir_600.iterdir.return_value = [mock_file]
        
        result = whats_new_messages(only_recent=False)
        
        # Should include all versions
        assert "6.0.0" in result
        assert mock_file in result["6.0.0"]

    def test_whats_new_messages_invalid_version_directory(self, mock_resources, mock_config):
        """Test that invalid version directories are skipped."""
        mock_message_dir = MagicMock()
        mock_resources.files.return_value = mock_message_dir
        
        # Create mock directory with invalid version name
        mock_dir_invalid = MagicMock()
        mock_dir_invalid.is_dir.return_value = True
        mock_dir_invalid.name = "not_a_version"
        
        mock_message_dir.iterdir.return_value = [mock_dir_invalid]
        
        result = whats_new_messages(only_recent=True)
        
        # Should return empty dict since no valid versions
        assert "not_a_version" not in result
        assert len(result) == 0

    def test_whats_new_messages_ignores_files_in_root(self, mock_resources, mock_config):
        """Test that files in the root messages directory are ignored."""
        mock_message_dir = MagicMock()
        mock_resources.files.return_value = mock_message_dir
        
        # Create a mock file (not directory)
        mock_file = MagicMock()
        mock_file.is_dir.return_value = False
        mock_file.name = "readme.txt"
        
        mock_message_dir.iterdir.return_value = [mock_file]
        
        result = whats_new_messages(only_recent=True)
        
        # Should return empty dict
        assert len(result) == 0


class TestWhatsNewBrowser:
    """Tests for the WhatsNewBrowser class."""

    def test_initialization(self):
        """Test WhatsNewBrowser initialization."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "body { color: blue; }"
            
            browser = WhatsNewBrowser()
            
            assert browser is not None
            assert isinstance(browser, WhatsNewBrowser)
            assert browser.css_data == "<style>\nbody { color: blue; }</style>"
            mock_res.read_text.assert_called_once_with(
                "sas.qtgui.Utilities.WhatsNew.css", "style.css"
            )

    def test_setHtml_injects_css(self):
        """Test that setHtml properly injects CSS."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "body { color: red; }"
            
            browser = WhatsNewBrowser()
            
            # Mock the parent setHtml to capture what's passed
            with patch.object(browser.__class__.__bases__[0], 'setHtml') as mock_set_html:
                html_content = "<html><head><!-- INJECT CSS HERE --></head><body>Test</body></html>"
                browser.setHtml(html_content)
                
                # Check that CSS was injected
                expected = "<html><head><style>\nbody { color: red; }</style></head><body>Test</body></html>"
                mock_set_html.assert_called_once_with(expected)

    def test_setHtml_no_injection_marker(self):
        """Test setHtml when there's no injection marker."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "body { color: green; }"
            
            browser = WhatsNewBrowser()
            
            with patch.object(browser.__class__.__bases__[0], 'setHtml') as mock_set_html:
                html_content = "<html><body>Test</body></html>"
                browser.setHtml(html_content)
                
                # Should pass through unchanged
                mock_set_html.assert_called_once_with(html_content)

    def test_loadResource_image_from_whatsnew(self):
        """Test loadResource for images in whatsnew directory."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "css"
            
            browser = WhatsNewBrowser()
            
            # Mock the resources.files for image loading
            mock_location = MagicMock()
            mock_res.files.return_value = mock_location
            
            # Chain the joinpath calls
            mock_location.joinpath.return_value.joinpath.return_value = Path("/fake/path/image.png")
            
            with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.QPixmap') as mock_pixmap:
                mock_pixmap.return_value = QPixmap()
                
                # Test with QUrl
                url = QUrl("whatsnew/6.0.0/image.png")
                result = browser.loadResource(2, url)  # 2 is the kind for images
                
                assert isinstance(result, QPixmap)

    def test_loadResource_image_from_whatsnew_string_url(self):
        """Test loadResource with string URL."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "css"
            
            browser = WhatsNewBrowser()
            
            mock_location = MagicMock()
            mock_res.files.return_value = mock_location
            mock_location.joinpath.return_value.joinpath.return_value = Path("/fake/path/image.png")
            
            with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.QPixmap') as mock_pixmap:
                mock_pixmap.return_value = QPixmap()
                
                result = browser.loadResource(2, "whatsnew/6.0.0/image.png")
                
                assert isinstance(result, QPixmap)

    def test_loadResource_non_whatsnew_resource(self):
        """Test loadResource for non-whatsnew resources."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "css"
            
            browser = WhatsNewBrowser()
            
            # Mock the parent loadResource
            with patch.object(browser.__class__.__bases__[0], 'loadResource') as mock_load:
                mock_load.return_value = "parent_result"
                
                # Test with non-whatsnew URL
                result = browser.loadResource(2, QUrl("http://example.com/image.png"))
                
                assert result == "parent_result"
                mock_load.assert_called_once()

    def test_loadResource_non_image_type(self):
        """Test loadResource for non-image resource types."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.resources') as mock_res:
            mock_res.read_text.return_value = "css"
            
            browser = WhatsNewBrowser()
            
            with patch.object(browser.__class__.__bases__[0], 'loadResource') as mock_load:
                mock_load.return_value = "parent_result"
                
                # Test with kind != 2 (not an image)
                result = browser.loadResource(1, "whatsnew/6.0.0/image.png")
                
                assert result == "parent_result"
                mock_load.assert_called_once()


class TestWhatsNew:
    """Tests for the WhatsNew dialog class."""

    def test_initialization_with_new_messages(self, mock_config, mock_version):
        """Test WhatsNew initialization when there are new messages."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            # Setup mock files
            mock_file1 = MagicMock()
            mock_file1.__str__ = lambda x: "/path/to/6.1.0/feature1.html"
            mock_file2 = MagicMock()
            mock_file2.__str__ = lambda x: "/path/to/6.0.1/feature2.html"
            
            mock_messages.return_value = {
                "6.1.0": [mock_file1],
                "6.0.1": [mock_file2]
            }
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                
                assert dialog is not None
                assert dialog.windowTitle() == "What's New in SasView 6.1.0"
                assert dialog.browser is not None
                assert dialog.showAgain is not None
                assert dialog.showAgain.isChecked() is True
                assert len(dialog.all_messages) == 2
                assert dialog.max_index == 2
                assert dialog.current_index == 0

    def test_initialization_no_new_messages(self, mock_config, mock_version):
        """Test WhatsNew initialization when there are no new messages."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = True
            
            dialog = WhatsNew()
            
            assert len(dialog.all_messages) == 0
            assert dialog.max_index == 0

    def test_initialization_up_to_date(self, mock_config):
        """Test initialization when version is not newer than last hidden."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.sasview_version', '6.0.0'), \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = False
            
            dialog = WhatsNew()
            
            # Should not show the "Show on Startup" checkbox
            assert dialog.showAgain is None

    def test_next_file(self, mock_config, mock_version):
        """Test navigating to next file."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file1 = MagicMock()
            mock_file1.__str__ = lambda x: "/path/to/file1.html"
            mock_file2 = MagicMock()
            mock_file2.__str__ = lambda x: "/path/to/file2.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file1, mock_file2]}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                
                assert dialog.current_index == 0
                dialog.next_file()
                assert dialog.current_index == 1
                
                # Should wrap around
                dialog.next_file()
                assert dialog.current_index == 0

    def test_prev_file(self, mock_config, mock_version):
        """Test navigating to previous file."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file1 = MagicMock()
            mock_file1.__str__ = lambda x: "/path/to/file1.html"
            mock_file2 = MagicMock()
            mock_file2.__str__ = lambda x: "/path/to/file2.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file1, mock_file2]}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                
                assert dialog.current_index == 0
                dialog.prev_file()
                assert dialog.current_index == 1  # Should wrap to last
                
                dialog.prev_file()
                assert dialog.current_index == 0

    def test_set_enable_disable_prev_next_first_item(self, mock_config, mock_version):
        """Test button states when on first item."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file1 = MagicMock()
            mock_file1.__str__ = lambda x: "/path/to/file1.html"
            mock_file2 = MagicMock()
            mock_file2.__str__ = lambda x: "/path/to/file2.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file1, mock_file2]}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                dialog.current_index = 0
                dialog.set_enable_disable_prev_next()
                
                assert dialog.prevButton.isEnabled() is False
                assert dialog.nextButton.isEnabled() is True

    def test_set_enable_disable_prev_next_last_item(self, mock_config, mock_version):
        """Test button states when on last item."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file1 = MagicMock()
            mock_file1.__str__ = lambda x: "/path/to/file1.html"
            mock_file2 = MagicMock()
            mock_file2.__str__ = lambda x: "/path/to/file2.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file1, mock_file2]}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                dialog.current_index = 1
                dialog.set_enable_disable_prev_next()
                
                assert dialog.prevButton.isEnabled() is True
                assert dialog.nextButton.isEnabled() is False

    def test_set_enable_disable_prev_next_middle_item(self, mock_config, mock_version):
        """Test button states when on middle item."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_files = [MagicMock() for _ in range(3)]
            for i, f in enumerate(mock_files):
                f.__str__ = lambda x, i=i: f"/path/to/file{i}.html"
            
            mock_messages.return_value = {"6.1.0": mock_files}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                dialog.current_index = 1
                dialog.set_enable_disable_prev_next()
                
                assert dialog.prevButton.isEnabled() is True
                assert dialog.nextButton.isEnabled() is True

    def test_show_file_with_messages(self, mock_config, mock_version):
        """Test show_file when messages exist."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file = MagicMock()
            mock_file.__str__ = lambda x: "/path/to/file.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file]}
            mock_newer.return_value = True
            
            html_content = "<html><body>Feature announcement</body></html>"
            with patch('builtins.open', mock_open(read_data=html_content)):
                dialog = WhatsNew()
                
                with patch.object(dialog.browser, 'setHtml') as mock_set_html:
                    dialog.show_file()
                    mock_set_html.assert_called_once_with(html_content)

    def test_show_file_no_messages(self, mock_config, mock_version):
        """Test show_file when there are no messages."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = True
            
            dialog = WhatsNew()
            
            with patch.object(dialog.browser, 'setHtml') as mock_set_html:
                dialog.show_file()
                mock_set_html.assert_called_once()
                call_args = mock_set_html.call_args[0][0]
                assert "You should not see this!!!" in call_args

    def test_close_me_with_show_again_unchecked(self, mock_config, mock_version):
        """Test close_me when 'Show on Startup' is unchecked."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.newest') as mock_newest:
            
            mock_file = MagicMock()
            mock_file.__str__ = lambda x: "/path/to/file.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file]}
            mock_newer.return_value = True
            mock_newest.return_value = "6.1.0"
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                dialog.showAgain.setChecked(False)
                
                with patch.object(dialog, 'close') as mock_close:
                    dialog.close_me()
                    
                    # Should update config
                    assert mock_config.LAST_WHATS_NEW_HIDDEN_VERSION == "6.1.0"
                    mock_close.assert_called_once()

    def test_close_me_with_show_again_checked(self, mock_config, mock_version):
        """Test close_me when 'Show on Startup' is checked."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file = MagicMock()
            mock_file.__str__ = lambda x: "/path/to/file.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file]}
            mock_newer.return_value = True
            
            original_version = mock_config.LAST_WHATS_NEW_HIDDEN_VERSION
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                dialog.showAgain.setChecked(True)
                
                with patch.object(dialog, 'close') as mock_close:
                    dialog.close_me()
                    
                    # Should NOT update config
                    assert mock_config.LAST_WHATS_NEW_HIDDEN_VERSION == original_version
                    mock_close.assert_called_once()

    def test_close_me_no_show_again_checkbox(self, mock_config):
        """Test close_me when showAgain checkbox doesn't exist."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.sasview_version', '6.0.0'), \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = False
            
            original_version = mock_config.LAST_WHATS_NEW_HIDDEN_VERSION
            
            dialog = WhatsNew()
            
            with patch.object(dialog, 'close') as mock_close:
                dialog.close_me()
                
                # Should NOT update config
                assert mock_config.LAST_WHATS_NEW_HIDDEN_VERSION == original_version
                mock_close.assert_called_once()

    def test_has_new_messages_true(self, mock_config, mock_version):
        """Test has_new_messages when there are messages."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_file = MagicMock()
            mock_file.__str__ = lambda x: "/path/to/file.html"
            
            mock_messages.return_value = {"6.1.0": [mock_file]}
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                
                assert dialog.has_new_messages() is True

    def test_has_new_messages_false(self, mock_config, mock_version):
        """Test has_new_messages when there are no messages."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = True
            
            dialog = WhatsNew()
            
            assert dialog.has_new_messages() is False

    def test_window_properties(self, mock_config, mock_version):
        """Test window properties are set correctly."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = True
            
            dialog = WhatsNew()
            
            # Check window is modal
            assert dialog.isModal() is True
            
            # Check fixed size
            assert dialog.width() == 800
            assert dialog.height() == 600

    def test_message_sorting_by_version(self, mock_config, mock_version):
        """Test that messages are sorted correctly by version (newest first)."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            # Create mock files for different versions
            mock_file_600 = MagicMock()
            mock_file_600.__str__ = lambda x: "/path/to/6.0.0/file.html"
            mock_file_601 = MagicMock()
            mock_file_601.__str__ = lambda x: "/path/to/6.0.1/file.html"
            mock_file_610 = MagicMock()
            mock_file_610.__str__ = lambda x: "/path/to/6.1.0/file.html"
            
            # Return unsorted messages
            mock_messages.return_value = {
                "6.0.0": [mock_file_600],
                "6.1.0": [mock_file_610],
                "6.0.1": [mock_file_601]
            }
            mock_newer.return_value = True
            
            with patch('builtins.open', mock_open(read_data="<html><body>Test</body></html>")):
                dialog = WhatsNew()
                
                # First message should be from newest version (6.1.0)
                assert str(dialog.all_messages[0]) == "/path/to/6.1.0/file.html"

    def test_only_recent_parameter(self, mock_config, mock_version):
        """Test that only_recent parameter is passed correctly."""
        with patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.whats_new_messages') as mock_messages, \
             patch('sas.qtgui.Utilities.WhatsNew.WhatsNew.strictly_newer_than') as mock_newer:
            
            mock_messages.return_value = {}
            mock_newer.return_value = True
            
            # Test with only_recent=True (default)
            dialog1 = WhatsNew(only_recent=True)
            mock_messages.assert_called_with(only_recent=True)
            
            # Test with only_recent=False
            dialog2 = WhatsNew(only_recent=False)
            mock_messages.assert_called_with(only_recent=False)

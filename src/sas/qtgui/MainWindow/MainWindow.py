import logging
import os
import sys
from importlib import resources

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QMdiArea, QSplashScreen

import sas.system.config as config

# Local UI
from sas.qtgui.UI import main_resources_rc  # noqa: F401
from sas.system.version import __version__

from ..Utilities.NewVersion.NewVersionAvailable import maybe_prompt_new_version_download
from .UI.MainWindowUI import Ui_SasView

logger = logging.getLogger(__name__)

class MainSasViewWindow(QMainWindow, Ui_SasView):
    # Main window of the application
    def __init__(self, parent=None):
        super(MainSasViewWindow, self).__init__(parent)

        self.setupUi(self)

        # Add the version number to window title
        self.setWindowTitle(f"SasView {__version__}")
        # define workspace for dialogs.
        self.workspace = QMdiArea(self)
        # some perspectives are fixed size.
        # the two scrollbars will help managing the workspace.
        self.workspace.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.workspace.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.workspace)
        QTimer.singleShot(100, self.showMaximized)
        # Temporary solution for problem with menubar on Mac
        if sys.platform == "darwin":  # Mac
            self.menubar.setNativeMenuBar(False)

        # Create the gui manager
        from .GuiManager import GuiManager
        try:
            self.guiManager = GuiManager(self)
        except Exception as ex:
            logger.error("Application failed with: "+str(ex))
            raise ex

    def closeEvent(self, event):
        if self.guiManager.quitApplication():
            event.accept()
        else:
            event.ignore()

def SplashScreen():
    """
    Displays splash screen as soon as humanely possible.
    The screen will disappear as soon as the event loop starts.
    """

    with resources.open_binary("sas.qtgui.images", "SVwelcome_mini.png") as file:
        image_data = file.read()

        pixmap = QPixmap()
        pixmap.loadFromData(image_data)

        splashScreen = QSplashScreen(pixmap)

        return splashScreen

def get_highdpi_scaling():
    return 1.0

def run_sasview():
    # Disable GPU. This is a workaround for the issue with the QtWebEngine on some Win 10 systems
    # https://github.com/SasView/sasview/issues/3384
    # TODO: remove when the issue is fixed in QtWebEngine
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"

    # Check for updates
    maybe_prompt_new_version_download()
    config.save()

    # Make the event loop interruptable quickly
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
    QGuiApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGLRhi)
    # Note: Qt environment variables are initialized in sas.system.lib.setup_qt_env
    # Main must have reference to the splash screen, so making it explicit
    app = QApplication([])
    app.setAttribute(Qt.AA_ShareOpenGLContexts)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setStyleSheet("* {font-size: 11pt;}")


    splash = SplashScreen()
    splash.show()

    # Main application style.
    # app.setStyle('Fusion')

    # fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
    if 'twisted.internet.reactor' in sys.modules:
        del sys.modules['twisted.internet.reactor']

    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    from sas.qtgui.Utilities import ReactorCore
    # Using the Qt5 reactor wrapper from https://github.com/ghtdak/qtreactor
    ReactorCore.install()

    # DO NOT move the following import to the top!
    from twisted.internet import reactor

    # Show the main SV window
    mainwindow = MainSasViewWindow()

    # no more splash screen
    splash.finish(mainwindow)

    # Time for the welcome window
    mainwindow.guiManager.showWelcomeMessage()

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    # No need to .exec_ - the reactor takes care of it.
    reactor.run()

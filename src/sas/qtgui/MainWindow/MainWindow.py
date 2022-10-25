# UNLESS EXEPTIONALLY REQUIRED TRY TO AVOID IMPORTING ANY MODULES HERE
# ESPECIALLY ANYTHING IN SAS, SASMODELS NAMESPACE
import os
import sys
import logging

from sas.system.version import __version__

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Local UI
from .UI.MainWindowUI import Ui_SasView

logger = logging.getLogger(__name__)

class MainSasViewWindow(QMainWindow, Ui_SasView):
    # Main window of the application
    def __init__(self, screen_resolution, parent=None):
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
        self.screen_width = screen_resolution.width()
        self.screen_height = screen_resolution.height()
        self.setCentralWidget(self.workspace)

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
    pixmap_path = "images/SVwelcome_mini.png"
    if os.path.splitext(sys.argv[0])[1].lower() == ".py":
        pixmap_path = "src/sas/qtgui/images/SVwelcome_mini.png"
    pixmap = QPixmap(pixmap_path)
    splashScreen = QSplashScreen(pixmap)
    return splashScreen

def run_sasview():
    # Make the event loop interruptable quickly
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication([])

    # Main must have reference to the splash screen, so making it explicit
    splash = SplashScreen()
    splash.show()
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    # Main application style.
    #app.setStyle('Fusion')

    # fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
    if 'twisted.internet.reactor' in sys.modules:
        del sys.modules['twisted.internet.reactor']

    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    import qt5reactor
    # Using the Qt5 reactor wrapper from https://github.com/ghtdak/qtreactor
    qt5reactor.install()

    # DO NOT move the following import to the top!
    from twisted.internet import reactor

    screen_resolution = app.desktop().screenGeometry()

    # Show the main SV window
    mainwindow = MainSasViewWindow(screen_resolution)
    mainwindow.showMaximized()

    # no more splash screen
    splash.finish(mainwindow)

    # Time for the welcome window
    mainwindow.guiManager.showWelcomeMessage()

    # No need to .exec_ - the reactor takes care of it.
    reactor.run()

# UNLESS EXEPTIONALLY REQUIRED TRY TO AVOID IMPORTING ANY MODULES HERE
# ESPECIALLY ANYTHING IN SAS, SASMODELS NAMESPACE
import logging
import os
import sys

from sas import config
from sas.system import env, version

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

# Local UI
from .UI.MainWindowUI import Ui_SasView

class MainSasViewWindow(QMainWindow, Ui_SasView):
    # Main window of the application
    def __init__(self, screen_resolution, parent=None):
        super(MainSasViewWindow, self).__init__(parent)

        self.setupUi(self)

        # Add the version number to window title
        self.setWindowTitle(f"SasView {version.__version__}")
        # define workspace for dialogs.
        self.workspace = QMdiArea(self)
        # some perspectives are fixed size.
        # the two scrollbars will help managing the workspace.
        self.workspace.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.workspace.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.screen_width = screen_resolution.width()
        self.screen_height = screen_resolution.height()
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
            import logging
            logging.error("Application failed with: "+str(ex))
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
    app = QApplication([])

    #Initialize logger
    from sas.system.log import SetupLogger
    SetupLogger(__name__).config_development()

    # initialize sasmodels settings
    from sas.system.user import get_user_dir
    if "SAS_DLL_PATH" not in os.environ:
        os.environ["SAS_DLL_PATH"] = os.path.join(
            get_user_dir(), "compiled_models")

    # Set open cl config from environment variable, if it is set

    if env.sas_opencl is not None:
        logging.getLogger(__name__).info("Getting OpenCL settings from environment variables")
        config.SAS_OPENCL = env.sas_opencl
    else:
        logging.getLogger(__name__).info("Getting OpenCL settings from config")
        env.sas_opencl = config.SAS_OPENCL

    # Make the event loop interruptable quickly
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

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

    # no more splash screen
    splash.finish(mainwindow)

    # Time for the welcome window
    mainwindow.guiManager.showWelcomeMessage()

    # No need to .exec_ - the reactor takes care of it.
    reactor.run()

# UNLESS EXEPTIONALLY REQUIRED TRY TO AVOID IMPORTING ANY MODULES HERE
# ESPECIALLY ANYTHING IN SAS, SASMODELS NAMESPACE
from PyQt4 import QtGui

# Local UI
from sas.qtgui.UI import main_resources_rc
from .UI.MainWindowUI import Ui_MainWindow

# Initialize logging
import sas.qtgui.Utilities.SasviewLogger

class MainSasViewWindow(QtGui.QMainWindow, Ui_MainWindow):
    # Main window of the application
    def __init__(self, parent=None):
        super(MainSasViewWindow, self).__init__(parent)
        self.setupUi(self)

        # define workspace for dialogs.
        self.workspace = QtGui.QWorkspace(self)
        self.setCentralWidget(self.workspace)

        # Create the gui manager
        from .GuiManager import GuiManager
        self.guiManager = GuiManager(self)

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
    # TODO: standardize path to images
    pixmap = QtGui.QPixmap("src/sas/qtgui/images/SVwelcome_mini.png")
    splashScreen = QtGui.QSplashScreen(pixmap)
    return splashScreen

def run():
    app = QtGui.QApplication([])

    # Main must have reference to the splash screen, so making it explicit
    splash = SplashScreen()
    splash.show()

    # fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
    import sys
    if 'twisted.internet.reactor' in sys.modules:
        del sys.modules['twisted.internet.reactor']

    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    import qt4reactor
    # Using the Qt4 reactor wrapper from https://github.com/ghtdak/qtreactor
    qt4reactor.install()

    # DO NOT move the following import to the top!
    from twisted.internet import reactor

    # Show the main SV window
    mainwindow = MainSasViewWindow()
    mainwindow.showMaximized()

    # no more splash screen
    splash.finish(mainwindow)

    # No need to .exec_ - the reactor takes care of it.
    reactor.run()

if __name__ == "__main__":
    run()

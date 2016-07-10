# UNLESS EXEPTIONALLY REQUIRED TRY TO AVOID IMPORTING ANY MODULES HERE
# ESPECIALLY ANYTHING IN SAS, SASMODELS NAMESPACE
from PyQt4 import QtGui

# Local UI
from UI.MainWindowUI import MainWindow

# Initialize logging
import SasviewLogger

class MainSasViewWindow(MainWindow):
    # Main window of the application
    def __init__(self, reactor, parent=None):
        super(MainSasViewWindow, self).__init__(parent)

        # define workspace for dialogs.
        self.workspace = QtGui.QWorkspace(self)
        self.setCentralWidget(self.workspace)

        # Create the gui manager
        from GuiManager import GuiManager
        self.guiManager = GuiManager(self, reactor, self)

    def closeEvent(self, event):
        self.guiManager.quitApplication()


def SplashScreen():
    """
    Displays splash screen as soon as humanely possible.
    The screen will disappear as soon as the event loop starts.
    """
    pixmap = QtGui.QPixmap("images/SVwelcome_mini.png")
    splashScreen = QtGui.QSplashScreen(pixmap)
    return splashScreen


if __name__ == "__main__":
    app = QtGui.QApplication([])

    # Main must have reference to the splash screen, so making it explicit
    splash = SplashScreen()
    splash.show()

    # DO NOT move the following import to the top!
    # (unless you know what you're doing)
    import qt4reactor
    # Using the Qt4 reactor wrapper from https://github.com/ghtdak/qtreactor
    qt4reactor.install()

    # DO NOT move the following import to the top!
    from twisted.internet import reactor

    # Show the main SV window
    mainwindow = MainSasViewWindow(reactor)
    #mainwindow.show()
    mainwindow.showMaximized()

    # no more splash screen
    splash.finish(mainwindow)

    # No need to .exec_ - the reactor takes care of it.
    reactor.run()


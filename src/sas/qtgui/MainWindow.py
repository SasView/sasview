# UNLESS EXEPTIONALLY REQUIRED TRY TO AVOID IMPORTING ANY MODULES HERE
# ESPECIALLY ANYTHING IN SAS, SASMODELS NAMESPACE
from PyQt4 import QtGui

# Local UI
from UI.MainWindowUI import Ui_MainWindow

# Initialize logging
import SasviewLogger

def updatePaths():
    # Update paths
    # TEMPORARY KLUDGE TO ALLOW INSTALL-LESS RUNS
    # THIS WILL GO AWAY ONCE MERGED
    #######################################################################
    import imp
    import os
    import sys
    def addpath(path):
        """
        Add a directory to the python path environment, and to the PYTHONPATH
        environment variable for subprocesses.
        """
        path = os.path.abspath(path)
        if 'PYTHONPATH' in os.environ:
            PYTHONPATH = path + os.pathsep + os.environ['PYTHONPATH']
        else:
            PYTHONPATH = path
        os.environ['PYTHONPATH'] = PYTHONPATH
        sys.path.insert(0, path)

    def import_package(modname, path):
        """Import a package into a particular point in the python namespace"""
        mod = imp.load_source(modname, os.path.abspath(os.path.join(path,'__init__.py')))
        sys.modules[modname] = mod
        mod.__path__ = [os.path.abspath(path)]
        return mod

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    addpath(os.path.join(root, 'src'))
    #addpath(os.path.join(root, '../sasmodels/'))
    import sas
    from distutils.util import get_platform
    sas.sasview = import_package('sas.sasview', os.path.join(root,'sasview'))
    platform = '%s-%s'%(get_platform(),sys.version[:3])
    build_path = os.path.join(root, 'build','lib.'+platform)
    sys.path.append(build_path)
    #######################################################################

class MainSasViewWindow(QtGui.QMainWindow, Ui_MainWindow):
    # Main window of the application
    def __init__(self, reactor, parent=None):
        super(MainSasViewWindow, self).__init__(parent)
        self.setupUi(self)

        # define workspace for dialogs.
        self.workspace = QtGui.QWorkspace(self)
        self.setCentralWidget(self.workspace)

        updatePaths()

        # Create the gui manager
        from GuiManager import GuiManager
        self.guiManager = GuiManager(self, reactor, self)

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


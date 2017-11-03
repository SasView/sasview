from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from PyQt5 import QtSvg

def new_load_qt(api_options):
    return QtCore, QtGui, QtSvg, 'pyqt'

def qtconsole_new_load_qt(api_options):
    # Alias PyQt-specific functions for PySide compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    return QtCore, QtGui, QtSvg, 'pyqt'

from IPython.external import  qt_loaders
from qtconsole import qt_loaders as qtconsole_qt_loaders
# Do some monkey patching to satisfy pyinstaller complaining
# about pyside/pyqt confusion
#qt_loaders.load_qt = new_load_qt
#qtconsole_qt_loaders.load_qt = qtconsole_new_load_qt

from qtconsole.rich_jupyter_widget import RichJupyterWidget

MODULES_TO_IMPORT = [
    ('sas', 'sas'),
    ('sasmodels', 'sasmodels'),
    ('numpy', 'np')]

class IPythonWidget(RichJupyterWidget):
    def __init__(self, parent=None, **kwargs):
        super(self.__class__, self).__init__(parent)
        from qtconsole.inprocess import QtInProcessKernelManager
        from IPython.lib import guisupport
        app = guisupport.get_app_qt4()

        # Create an in-process kernel
        kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel = kernel_manager.kernel
        kernel.gui = 'qt4'

        kernel_client = kernel_manager.client()
        kernel_client.start_channels()

        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client

        self.kernel_manager.kernel.shell.run_code(
            '\n'.join('import %s as %s' % t for t in MODULES_TO_IMPORT))

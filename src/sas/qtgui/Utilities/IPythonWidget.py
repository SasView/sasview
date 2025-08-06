

from qtconsole.rich_jupyter_widget import RichJupyterWidget

from sas.qtgui.Utilities import GuiUtils

MODULES_TO_IMPORT = [
    ('sas', 'sas'),
    ('sasmodels', 'sasmodels'),
    ('numpy', 'np')]

class IPythonWidget(RichJupyterWidget):
    def __init__(self, parent=None, **kwargs):
        super(self.__class__, self).__init__(parent)
        from IPython.lib import guisupport
        from qtconsole.inprocess import QtInProcessKernelManager
        app = guisupport.get_app_qt4()

        font = GuiUtils.getMonospaceFont()
        self.font = font

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

"""
    Corfunc perspective
"""
import wx
import logging
from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sasgui.perspectives.corfunc.corfunc_panel import CorfuncPanel

class Plugin(PluginBase):
    """
    This class defines the interface for a plugin class for a correlation
    function perspective
    """

    def __init__(self):
        PluginBase.__init__(self, name="Correlation Function")
        logging.info("Correlation function plug-in started")
        self._always_active = True

    def get_panels(self, parent):
        """
        Define the GUI panels
        """
        self.parent = parent
        self.frame = MDIFrame(self.parent, None, 'None', (100,200))
        # self.test_panel = PanelBase(parent=self.frame)
        # self.test_panel.set_manager(self)
        # self.frame.set_panel(self.test_panel)
        # self.perspective.append("testwindow")
        self.corfunc_panel = CorfuncPanel(parent=self.frame)
        self.frame.set_panel(self.corfunc_panel)
        self.corfunc_panel.set_manager(self)
        self.perspective.append(self.corfunc_panel.window_name)

        return [self.corfunc_panel]

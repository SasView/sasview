"""
File Converter Plugin
"""

import logging
from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.perspectives.file_converter.converter_panel import ConverterWindow

logger = logging.getLogger(__name__)

class Plugin(PluginBase):
    """
    This class defines the interface for a Plugin class
    for File Converter perspective
    """

    def __init__(self):
        PluginBase.__init__(self, name="File Converter")
        logger.info("File Converter plug-in started")
        self._sub_menu = "Tool"
        self.converter_frame = None

    def get_tools(self):
        """
        Returns a set of menu entries
        """
        help_txt = "Convert ASCII or BSL/OTOKO data to CanSAS or NXcanSAS formats"
        return [("File Converter", help_txt, self.on_file_converter)]

    def on_file_converter(self, event):
        if self.converter_frame is None:
            frame = ConverterWindow(parent=self.parent, base=self.parent,
                manager=self)
            self.put_icon(frame)
            self.converter_frame = frame
        else:
            self.converter_frame.Show(False)
        self.converter_frame.Show(True)

    def put_icon(self, frame):
        """
        Put icon in the frame title bar
        """
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass

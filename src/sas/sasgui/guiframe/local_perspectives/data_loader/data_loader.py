
"""
plugin DataLoader responsible of loading data
"""
import os
import sys
import wx
import logging

logger = logging.getLogger(__name__)

from sas import get_local_config

from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.loader_exceptions import NoKnownLoaderException

from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME
from sas.sasgui.guiframe.gui_manager import DEFAULT_OPEN_FOLDER

config = get_local_config()
extension_list = []
if config.APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(config.APPLICATION_STATE_EXTENSION)
EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS + extension_list
PLUGINS_WLIST = config.PLUGINS_WLIST
APPLICATION_WLIST = config.APPLICATION_WLIST


class Plugin(PluginBase):

    def __init__(self):
        PluginBase.__init__(self, name="DataLoader")
        # Default location
        self._default_save_location = DEFAULT_OPEN_FOLDER
        self.loader = Loader()
        self._data_menu = None

    def populate_file_menu(self):
        """
        get a menu item and append it under file menu of the application
        add load file menu item and load folder item
        """
        # menu for data files
        data_file_hint = "load one or more data in the application"
        menu_list = [('&Load Data File(s)', data_file_hint, self.load_data)]
        gui_style = self.parent.get_style()
        style = gui_style & GUIFRAME.MULTIPLE_APPLICATIONS
        if style == GUIFRAME.MULTIPLE_APPLICATIONS:
            # menu for data from folder
            data_folder_hint = "load multiple data in the application"
            menu_list.append(('&Load Data Folder', data_folder_hint,
                              self._load_folder))
        return menu_list

    def load_data(self, event):
        """
        Load data
        """
        path = None
        self._default_save_location = self.parent._default_save_location
        if self._default_save_location is None:
            self._default_save_location = os.getcwd()

        cards = self.loader.get_wildcards()
        temp = [APPLICATION_WLIST] + PLUGINS_WLIST
        for item in temp:
            if item in cards:
                cards.remove(item)
        wlist = '|'.join(cards)
        style = wx.OPEN | wx.FD_MULTIPLE
        dlg = wx.FileDialog(self.parent,
                            "Choose a file",
                            self._default_save_location, "",
                            wlist,
                            style=style)
        if dlg.ShowModal() == wx.ID_OK:
            file_list = dlg.GetPaths()
            if len(file_list) >= 0 and file_list[0] is not None:
                self._default_save_location = os.path.dirname(file_list[0])
                path = self._default_save_location
        dlg.Destroy()

        if path is None or not file_list or file_list[0] is None:
            return
        self.parent._default_save_location = self._default_save_location
        self.get_data(file_list)

    def can_load_data(self):
        """
        if return True, then call handler to laod data
        """
        return True

    def _load_folder(self, event):
        """
        Load entire folder
        """
        path = None
        self._default_save_location = self.parent._default_save_location
        if self._default_save_location is None:
            self._default_save_location = os.getcwd()
        dlg = wx.DirDialog(self.parent, "Choose a directory",
                           self._default_save_location,
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = path
        dlg.Destroy()
        if path is not None:
            self._default_save_location = os.path.dirname(path)
        else:
            return
        file_list = self.get_file_path(path)
        self.get_data(file_list)
        self.parent._default_save_location = self._default_save_location

    def load_error(self, error=None):
        """
        Pop up an error message.

        :param error: details error message to be displayed
        """
        if error is not None or str(error).strip() != "":
            dial = wx.MessageDialog(self.parent, str(error),
                                    'Error Loading File',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()

    def get_file_path(self, path):
        """
        Receive a list containing folder then return a list of file
        """
        if os.path.isdir(path):
            return [os.path.join(os.path.abspath(path), filename) for filename
                    in os.listdir(path)]

    def _process_data_and_errors(self, item, p_file, output, message):
        """
        Check to see if data set loaded with any errors. If so, append to
            error message to be sure user knows the issue.
        """
        data_error = False
        if hasattr(item, 'errors'):
            for error_data in item.errors:
                data_error = True
                message += "\tError: {0}\n".format(error_data)
        else:
            logger.error("Loader returned an invalid object:\n %s" % str(item))
            data_error = True

        data = self.parent.create_gui_data(item, p_file)
        output[data.id] = data
        return output, message, data_error

    def get_data(self, path, format=None):
        """
        """
        file_errors = {}
        output = {}
        exception_occurred = False

        for p_file in path:
            basename = os.path.basename(p_file)
            # Skip files that start with a period
            if basename.startswith("."):
                msg = "The folder included a potential hidden file - %s." \
                      % basename
                msg += " Do you wish to load this file as data?"
                msg_box = wx.MessageDialog(None, msg, 'Warning',
                                           wx.OK | wx.CANCEL)
                if msg_box.ShowModal() == wx.ID_CANCEL:
                    continue
            _, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                log_msg = "Data Loader cannot "
                log_msg += "load: {}\n".format(str(p_file))
                log_msg += "Please try to open that file from \"open project\""
                log_msg += "or \"open analysis\" menu."
                logger.info(log_msg)
                file_errors[basename] = [log_msg]
                continue

            try:
                message = "Loading {}...\n".format(p_file)
                self.load_update(output=output, message=message, info="info")
                temp = self.loader.load(p_file, format)
                if not isinstance(temp, list):
                    temp = [temp]
                for item in temp:
                    error_message = ""
                    output, error_message, data_error = \
                        self._process_data_and_errors(item,
                                                      p_file,
                                                      output,
                                                      error_message)
                    if data_error:
                        if basename in file_errors.keys():
                            file_errors[basename] += [error_message]
                        else:
                            file_errors[basename] = [error_message]
                        self.load_update(output=output,
                            message=error_message, info="warning")

                self.load_update(output=output,
                message="Loaded {}\n".format(p_file),
                info="info")

            except NoKnownLoaderException as e:
                exception_occurred = True
                logger.error(e.message)

                error_message = "Loading data failed!\n" + e.message
                self.load_update(output=None, message=e.message, info="warning")

            except Exception as e:
                exception_occurred = True
                logger.error(e.message)

                file_err = "The Data file you selected could not be "
                file_err += "loaded.\nMake sure the content of your file"
                file_err += " is properly formatted.\n"
                file_err += "When contacting the SasView team, mention the"
                file_err += " following:\n"
                file_err += e.message
                file_errors[basename] = [file_err]

        if len(file_errors) > 0:
            error_message = ""
            for filename, error_array in file_errors.iteritems():
                error_message += "The following errors occured whilst "
                error_message += "loading {}:\n".format(filename)
                for message in error_array:
                    error_message += message + "\n"
                error_message += "\n"
            if not exception_occurred: # Some data loaded but with errors
                self.load_update(output=output, message=error_message, info="error")

        if not exception_occurred: # Everything loaded as expected
            self.load_complete(output=output, message="Loading data complete!",
                               info="info")
        else:
            self.load_complete(output=None, message=error_message, info="error")


    def load_update(self, output=None, message="", info="warning"):
        """
        print update on the status bar
        """
        if message != "":
            wx.PostEvent(self.parent, StatusEvent(status=message, info=info,
                                                  type="progress"))

    def load_complete(self, output, message="", info="warning"):
        """
         post message to status bar and return list of data
        """
        wx.PostEvent(self.parent, StatusEvent(status=message, info=info,
                                              type="stop"))
        if output is not None:
            self.parent.add_data(data_list=output)

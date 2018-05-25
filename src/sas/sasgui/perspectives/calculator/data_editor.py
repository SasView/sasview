
import wx
import sys
import os
from copy import deepcopy

from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Data2D
from .detector_editor import DetectorDialog
from .collimation_editor import CollimationDialog
from .console import ConsoleDialog

from sas.sasgui.guiframe.events import StatusEvent


_QMIN_DEFAULT = 0.001
_QMAX_DEFAULT = 0.13
_NPTS_DEFAULT = 50
#Control panel width 
if sys.platform.count("darwin") == 0:
    PANEL_WIDTH = 500
    PANEL_HEIGTH = 350
    FONT_VARIANT = 0
    _BOX_WIDTH = 51
    ON_MAC = False
else:
    _BOX_WIDTH = 76
    PANEL_WIDTH = 550
    PANEL_HEIGTH = 400
    FONT_VARIANT = 1
    ON_MAC = True

def load_error(error=None):
    """
        Pop up an error message.

        @param error: details error message to be displayed
    """
    message = "You had to try this, didn't you?\n\n"
    message += "The data file you selected could not be loaded.\n"
    message += "Make sure the content of your file is properly formatted.\n\n"

    if error is not None:
        message += "When contacting the SasView team,"
        message += " mention the following:\n%s" % str(error)

    dial = wx.MessageDialog(None, message,
                            'Error Loading File', wx.OK | wx.ICON_EXCLAMATION)
    dial.ShowModal()


class DataEditorPanel(wx.ScrolledWindow):
    """
    :param data: when not empty the class can
        same information into a dat object
        and post event containing the changed data object to some other frame
    """
    def __init__(self, parent, data=[], *args, **kwds):
        kwds['name'] = "Data Editor"
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGTH)
        wx.ScrolledWindow.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self._data = data
        self._reset_data = deepcopy(data)
        self.reader = None
        self._notes = ""
        self._description = "Edit Data"
        self._default_save_location = os.getcwd()
        self._do_layout()
        self.reset_panel()
        self.bt_apply.Disable()
        if data:
            self.complete_loading(data=data)
            self.bt_apply.Enable()

    def _define_structure(self):
        """
        define initial sizer
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        name_box = wx.StaticBox(self, -1, "Load Data")
        self.name_sizer = wx.StaticBoxSizer(name_box, wx.HORIZONTAL)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.run_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.instrument_sizer = wx.BoxSizer(wx.HORIZONTAL)

        edit_box = wx.StaticBox(self, -1, "Edit ")
        self.edit_sizer = wx.StaticBoxSizer(edit_box, wx.HORIZONTAL)

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_name(self):
        """
        Do the layout for data name related widgets
        """
        #data name [string]
        data_name_txt = wx.StaticText(self, -1, 'Data : ')
        self.data_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.data_cbox, -1, self.on_select_data)
        hint_data = "Loaded data."
        self.data_cbox.SetToolTipString(hint_data)
        id = wx.NewId()
        self.browse_button = wx.Button(self, id, "Browse")
        hint_on_browse = "Click on this button to import data in this panel."
        self.browse_button.SetToolTipString(hint_on_browse)
        self.Bind(wx.EVT_BUTTON, self.on_click_browse, id=id)
        self.name_sizer.AddMany([(data_name_txt, 0, wx.LEFT, 15),
                                       (self.data_cbox, 0, wx.LEFT, 10),
                                       (self.browse_button, 0, wx.LEFT, 10)])

    def _layout_title(self):
        """
        Do the layout for data title related widgets
        """
        #title name [string]
        data_title_txt = wx.StaticText(self, -1, 'Title : ')
        self.data_title_tcl = wx.TextCtrl(self, -1, size=(PANEL_WIDTH * 3 / 5, -1))
        self.data_title_tcl.Bind(wx.EVT_TEXT_ENTER, self.on_change_title)
        hint_title = "Data's title."
        self.data_title_tcl.SetToolTipString(hint_title)
        self.title_sizer.AddMany([(data_title_txt, 0, wx.LEFT, 15),
                                       (self.data_title_tcl, 0, wx.LEFT, 10)])

    def _layout_run(self):
        """
        Do the layout for data run related widgets
        """
        data_run_txt = wx.StaticText(self, -1, 'Run : ')
        data_run_txt.SetToolTipString('')
        self.data_run_tcl = wx.TextCtrl(self, -1, size=(PANEL_WIDTH * 3 / 5, -1),
                                         style=wx.TE_MULTILINE)
        hint_run = "Data's run."
        self.data_run_tcl.SetToolTipString(hint_run)
        self.run_sizer.AddMany([(data_run_txt, 0, wx.LEFT, 15),
                                       (self.data_run_tcl, 0, wx.LEFT, 10)])

    def _layout_instrument(self):
        """
        Do the layout for instrument related widgets
        """
        instrument_txt = wx.StaticText(self, -1, 'Instrument : ')
        hint_instrument_txt = ''
        instrument_txt.SetToolTipString(hint_instrument_txt)
        self.instrument_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH * 5, 20))
        hint_instrument = "Instrument."
        self.instrument_tcl.SetToolTipString(hint_instrument)
        self.instrument_sizer.AddMany([(instrument_txt, 0, wx.LEFT, 15),
                                (self.instrument_tcl, 0, wx.LEFT, 10)])

    def _layout_editor(self):
        """
        Do the layout for sample related widgets
        """
        self.detector_rb = wx.RadioButton(self, -1, "Detector",
                                           style=wx.RB_GROUP)
        self.sample_rb = wx.RadioButton(self, -1, "Sample")
        self.source_rb = wx.RadioButton(self, -1, "Source")
        self.collimation_rb = wx.RadioButton(self, -1, "Collimation")

        self.bt_edit = wx.Button(self, -1, "Edit")
        self.bt_edit.SetToolTipString("Edit data.")
        self.bt_edit.Bind(wx.EVT_BUTTON, self.on_edit)
        self.edit_sizer.AddMany([(self.detector_rb, 0, wx.ALL, 10),
                        (self.sample_rb, 0, wx.RIGHT | wx.BOTTOM | wx.TOP, 10),
                        (self.source_rb, 0, wx.RIGHT | wx.BOTTOM | wx.TOP, 10),
                    (self.collimation_rb, 0, wx.RIGHT | wx.BOTTOM | wx.TOP, 10),
                    (self.bt_edit, 0,
                                  wx.RIGHT | wx.BOTTOM | wx.TOP, 10)])
        self.reset_radiobox()


    def _layout_source(self):
        """
            Do the layout for source related widgets
        """
        source_txt = wx.StaticText(self, -1, 'Source ')
        hint_source_txt = ''
        source_txt.SetToolTipString(hint_source_txt)
        self.bt_edit_source = wx.Button(self, -1, "Edit")
        self.bt_edit_source.SetToolTipString("Edit data's sample.")
        self.bt_edit_source.Bind(wx.EVT_BUTTON, self.edit_source)
        #self.source_sizer.AddMany([(source_txt, 0, wx.ALL, 10),
        #                        (self.bt_edit_source, 0,
        #                          wx.RIGHT|wx.BOTTOM|wx.TOP, 10)])

    def _layout_summary(self):
        """
            Layout widgets related to data's summary
        """
        self.data_summary = wx.TextCtrl(self, -1,
                                         style=wx.TE_MULTILINE | wx.HSCROLL,
                                        size=(-1, 200))
        summary = 'No data info available...'
        self.data_summary.SetValue(summary)
        #self.summary_sizer.Add(self.data_summary, 1, wx.EXPAND|wx.ALL, 10)  

    def _layout_button(self):
        """
            Do the layout for the button widgets
        """
        self.bt_summary = wx.Button(self, -1, "View", size=(_BOX_WIDTH, -1))
        self.bt_summary.SetToolTipString("View final changes on data.")
        self.bt_summary.Bind(wx.EVT_BUTTON, self.on_click_view)

        self.bt_save = wx.Button(self, -1, "Save As", size=(_BOX_WIDTH, -1))
        self.bt_save.SetToolTipString("Save changes in a file.")
        self.bt_save.Bind(wx.EVT_BUTTON, self.on_click_save)

        self.bt_apply = wx.Button(self, -1, "Apply", size=(_BOX_WIDTH, -1))
        self.bt_apply.SetToolTipString("Save changes into the imported data.")
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)

        self.bt_reset = wx.Button(self, -1, 'Reset', size=(_BOX_WIDTH, -1))
        self.bt_reset.Bind(wx.EVT_BUTTON, self.on_click_reset)
        self.bt_reset.SetToolTipString("Reset data to its initial state.")

        self.bt_close = wx.Button(self, -1, 'Close', size=(_BOX_WIDTH, -1))
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this panel.")

        self.button_sizer.AddMany([(self.bt_save, 0, wx.LEFT, 120),
                                   (self.bt_apply, 0, wx.LEFT, 10),
                                   (self.bt_reset, 0, wx.LEFT | wx.RIGHT, 10),
                                   (self.bt_summary, 0, wx.RIGHT, 10),
                                   (self.bt_close, 0, wx.RIGHT, 10)])

    def _do_layout(self):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_title()
        self._layout_run()
        self._layout_editor()
        self._layout_button()
        self.main_sizer.AddMany([(self.name_sizer, 0, wx.EXPAND | wx.ALL, 10),
                                (self.title_sizer, 0,
                                         wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                (self.run_sizer, 0,
                                         wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                (self.instrument_sizer, 0,
                                         wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                (self.edit_sizer, 0,
                                        wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10),
                                (self.button_sizer, 0,
                                          wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetScrollbars(20, 20, 25, 65)
        self.SetAutoLayout(True)

    def fill_data_combox(self):
        """
        fill the current combobox with the available data
        """
        if not self._data:
            return
        self.data_cbox.Clear()
        for data in self._data:
            name = data.title
            if data.run:
                name = data.run[0]
            if name.lstrip().rstrip() == "":
                name = data.filename
            pos = self.data_cbox.Append(str(name))
            self.data_cbox.SetClientData(pos, data)
            self.data_cbox.SetSelection(pos)
            self.data_cbox.SetStringSelection(str(name))

    def reset_panel(self):
        """
        """
        self.enable_data_cbox()
        self.data_title_tcl.SetValue("")
        self.data_run_tcl.SetValue("")

    def on_select_data(self, event=None):
        """
        """
        data, _, _ = self.get_current_data()
        self.reset_panel()
        if data is None:
            return
        self.data_title_tcl.SetValue(str(data.title))
        text = ""
        if data.run:
            for item in data.run:
                text += item + "\n"
        self.data_run_tcl.SetValue(str(text))

    def get_current_data(self):
        """
        """
        position = self.data_cbox.GetSelection()
        if position == wx.NOT_FOUND:
            return None, None, None
        data_name = self.data_cbox.GetStringSelection()
        data = self.data_cbox.GetClientData(position)
        return data, data_name, position

    def enable_data_cbox(self):
        """
        """
        if self._data:
            self.data_cbox.Enable()
            self.bt_summary.Enable()
            self.bt_reset.Enable()
            self.bt_save.Enable()
            self.bt_edit.Enable()
        else:
            self.data_cbox.Disable()
            self.bt_summary.Disable()
            self.bt_reset.Disable()
            self.bt_save.Disable()
            self.bt_edit.Disable()

    def reset_radiobox(self):
        """
        """
        self.detector_rb.SetValue(True)
        self.source_rb.SetValue(False)
        self.sample_rb.SetValue(False)
        self.collimation_rb.SetValue(False)

    def set_sample(self, sample, notes=None):
        """
        set sample for data
        """
        data, _, _ = self.get_current_data()
        if data is None:
            return
        data.sample = sample
        if notes is not None:
            data.process.append(notes)

    def set_source(self, source, notes=None):
        """
        set source for data
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        data.source = source
        if notes is not None:
            data.process.append(notes)

    def set_detector(self, detector, notes=None):
        """
        set detector for data
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        data.detector = detector
        if notes is not None:
            data.process.append(notes)

    def set_collimation(self, collimation, notes=None):
        """
        set collimation for data
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        data.collimation = collimation
        if notes is not None:
            data.process.append(notes)

    def edit_collimation(self):
        """
        Edit the selected collimation
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        dlg = CollimationDialog(collimation=data.collimation)
        dlg.set_manager(self)
        dlg.ShowModal()

    def edit_detector(self):
        """
        Edit the selected detector
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        dlg = DetectorDialog(detector=data.detector)
        dlg.set_manager(self)
        dlg.ShowModal()

    def edit_sample(self):
        """
        Open the dialog to edit the sample of the current data
        """
        data, _, _ = self.get_current_data()
        if data is None:
            return
        from .sample_editor import SampleDialog
        dlg = SampleDialog(parent=self, sample=data.sample)
        dlg.set_manager(self)
        dlg.ShowModal()

    def edit_source(self):
        """
        Open the dialog to edit the saource of the current data
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        from .source_editor import SourceDialog
        dlg = SourceDialog(parent=self, source=data.source)
        dlg.set_manager(self)
        dlg.ShowModal()

    def choose_data_file(self, location=None):
        """
        Open a file dialog to allow loading a file
        """
        path = None
        if location is None:
            location = os.getcwd()

        l = Loader()
        cards = l.get_wildcards()
        wlist = '|'.join(cards)

        dlg = wx.FileDialog(self, "Choose a file", location, "", wlist, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
        dlg.Destroy()
        return path


    def complete_loading(self, data=None, filename=''):
        """
        Complete the loading and compute the slit size
        """
        self.done = True
        self._data = []
        if data is None:
            msg = "Couldn't load data"
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg,
                                             info="warning", type='stop'))
            return
        if not  data.__class__.__name__ == "list":
            self._data.append(data)
            self._reset_data.append(deepcopy(data))
        else:
            self._data = deepcopy(data)
            self._reset_data = deepcopy(data)
        self.set_values()
        if self.parent.parent is None:
            return
        msg = "Load Complete"
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg,
                                                info="info", type='stop'))

    def set_values(self):
        """
        take the aperture values of the current data and display them
        through the panel
        """
        if self._data:
            self.fill_data_combox()
            self.on_select_data(event=None)

    def get_data(self):
        """
        return the current data
        """
        return self._data

    def get_notes(self):
        """
        return notes
        """
        return self._notes

    def on_change_run(self, event=None):
        """
        Change run
        """
        run = []
        data, _, _ = self.get_current_data()
        for i in range(self.data_run_tcl.GetNumberOfLines()):
            text = self.data_run_tcl.GetLineText(i).lstrip().rstrip()
            if text != "":
                run.append(text)
        if data.run != run:
            self._notes += "Change data 's "
            self._notes += "run from %s to %s \n" % (data.run, str(run))
            data.run = run
        if event is not None:
            event.Skip()

    def on_change_title(self, event=None):
        """
        Change title
        """
        data, _, _ = self.get_current_data()
        #Change data's name
        title = self.data_title_tcl.GetValue().lstrip().rstrip()

        if data.title != title:
            self._notes += "Change data 's "
            self._notes += "title from %s to %s \n" % (data.title, str(title))
            data.title = title
        if event is not None:
            event.Skip()

    def on_click_browse(self, event):
        """
        Open a file dialog to allow the user to select a given file.
        Display the loaded data if available.
        """
        path = self.choose_data_file(location=self._default_save_location)
        if path is None:
            return
        if self.parent.parent is not None:
            wx.PostEvent(self.parent.parent, StatusEvent(status="Loading...",
                                        info="info", type="progress"))

        self.done = False
        self._default_save_location = path
        try:
            #Load data
            from .load_thread import DataReader
            ## If a thread is already started, stop it
            if self.reader is not None and self.reader.isrunning():
                self.reader.stop()
            self.reader = DataReader(path=path,
                                    completefn=self.complete_loading,
                                    updatefn=None)
            self.reader.queue()
        except:
            msg = "Data Editor: %s" % (sys.exc_info()[1])
            load_error(msg)
            return
        event.Skip()

    def on_edit(self, event):
        """
        """
        if self.detector_rb.GetValue():
            self.edit_detector()
        if self.sample_rb.GetValue():
            self.edit_sample()
        if self.source_rb.GetValue():
            self.edit_source()
        if self.collimation_rb.GetValue():
            self.edit_collimation()
        event.Skip()

    def on_click_apply(self, event):
        """
        changes are saved in data object imported to edit
        """
        data, _, _ = self.get_current_data()
        if data is None:
            return
        self.on_change_run(event=None)
        self.on_change_title(event=None)
        #must post event here
        event.Skip()

    def on_click_save(self, event):
        """
        Save change into a file
        """
        if not self._data:
            return
        self.on_change_run(event=None)
        self.on_change_title(event=None)
        path = None
        wildcard = "CanSAS 1D files(*.xml)|*.xml"
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location, "", wildcard , wx.SAVE)

        for data in self._data:
            if issubclass(data.__class__, Data2D):
                msg = "No conventional writing format for \n\n"
                msg += "Data2D at this time.\n"
                dlg = wx.MessageDialog(None, msg, 'Error Loading File',
                                             wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
            else:
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    mypath = os.path.basename(path)
                    loader = Loader()
                    format = ".xml"
                    if os.path.splitext(mypath)[1].lower() == format:
                        loader.save(path, data, format)
                    try:
                        self._default_save_location = os.path.dirname(path)
                    except:
                        pass
                    dlg.Destroy()
        event.Skip()

    def on_click_view(self, event):
        """
        Display data info
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        self.on_change_run(event=None)
        self.on_change_title(event=None)
        dlg = ConsoleDialog(data=data)
        dlg.ShowModal()
        event.Skip()

    def on_click_reset(self, event):
        """
        """
        data, data_name, position = self.get_current_data()
        if data is None:
            return
        self._data[position] = deepcopy(self._reset_data[position])
        self.set_values()
        event.Skip()

    def on_close(self, event):
        """
        leave data as it is and close
        """
        self.parent.Close()
        event.Skip()

class DataEditorWindow(wx.Frame):
    def __init__(self, parent, manager, data=None, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGTH)
        wx.Frame.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self.panel = DataEditorPanel(parent=self, data=data)
        self.Show()

    def get_data(self):
        """
            return the current data
        """
        return self.panel.get_data()

if __name__ == "__main__":

    app = wx.App()
    window = DataEditorWindow(parent=None, data=[], title="Data Editor")
    app.MainLoop()

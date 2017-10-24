"""
Console Module display Python console
"""
import sys
import os

import numpy as np

import wx
from wx.lib.dialogs import ScrolledMessageDialog
from wx.lib import layoutf

import wx.py.editor as editor

if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 800
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 830
    PANEL_HEIGHT = 730
    FONT_VARIANT = 1
ID_CHECK_MODEL = wx.NewId()
ID_RUN = wx.NewId()

def check_model(path):
    """
    Check that the model on the path can run.
    """
    # try running the model
    from sasmodels.sasview_model import load_custom_model
    Model = load_custom_model(path)
    model = Model()
    q =  np.array([0.01, 0.1])
    Iq = model.evalDistribution(q)
    qx, qy =  np.array([0.01, 0.01]), np.array([0.1, 0.1])
    Iqxy = model.evalDistribution([qx, qy])

    # check the model's unit tests run
    from sasmodels.model_test import run_one
    result = run_one(path)

    return result

def show_model_output(parent, fname):
    # Make sure we have a python file; not sure why we care though...
    if not (fname and os.path.exists(fname) and fname.endswith('.py')):
        mssg = "\n This is not a python file."
        wx.MessageBox(str(mssg), 'Error', style=wx.ICON_ERROR)
        return False

    try:
        result, errmsg = check_model(fname), None
    except Exception:
        import traceback
        result, errmsg = None, traceback.format_exc()

    parts = ["Running model '%s'..." % os.path.basename(fname)]
    if errmsg is not None:
        parts.extend(["", "Error occurred:", errmsg, ""])
        title, icon = "Error", wx.ICON_ERROR
    else:
        parts.extend(["", "Success:", result, ""])
        title, icon = "Info", wx.ICON_INFORMATION
    text = "\n".join(parts)
    dlg = ResizableScrolledMessageDialog(parent, text, title, size=((550, 250)))
    fnt = wx.Font(10, wx.TELETYPE, wx.NORMAL, wx.NORMAL)
    dlg.GetChildren()[0].SetFont(fnt)
    dlg.GetChildren()[0].SetInsertionPoint(0)
    dlg.ShowModal()
    dlg.Destroy()
    return errmsg is None

class ResizableScrolledMessageDialog(wx.Dialog):
    """
    Custom version of wx ScrolledMessageDialog, allowing border resize
    """
    def __init__(self, parent, msg, caption,
        pos=wx.DefaultPosition, size=(500,300),
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER ):
        # Notice, that style can be overrriden in the caller.
        wx.Dialog.__init__(self, parent, -1, caption, pos, size, style)
        x, y = pos
        if x == -1 and y == -1:
            self.CenterOnScreen(wx.BOTH)

        text = wx.TextCtrl(self, -1, msg, style=wx.TE_MULTILINE | wx.TE_READONLY)
        ok = wx.Button(self, wx.ID_OK, "OK")

        # Mysterious constraint layouts from
        # https://www.wxpython.org/docs/api/wx.lib.layoutf.Layoutf-class.html
        lc = layoutf.Layoutf('t=t5#1;b=t5#2;l=l5#1;r=r5#1', (self,ok))
        text.SetConstraints(lc)
        lc = layoutf.Layoutf('b=b5#1;x%w50#1;w!80;h!25', (self,))
        ok.SetConstraints(lc)

        self.SetAutoLayout(1)
        self.Layout()

class PyConsole(editor.EditorNotebookFrame):
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Custom Model Editor"
    ## Name to appear on the window title bar
    window_caption = "Plugin Model Editor"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = False
    def __init__(self, parent=None, base=None, manager=None, panel=None,
                    title='Python Shell/Editor', filename=None,
                    size=(PANEL_WIDTH, PANEL_HEIGHT)):
        self.config = None

        editor.EditorNotebookFrame.__init__(self, parent=parent,
                                        title=title, size=size)
        self.parent = parent
        self._manager = manager
        self.base = base
        self.panel = panel
        self._add_menu()
        if filename is not None:
            dataDir = os.path.dirname(filename)
        elif self.parent is not None:
            dataDir = self.parent._default_save_location
        else:
             dataDir = None
        self.dataDir = dataDir
        self.Centre()

        # See if there is a corresponding C file
        if filename is not None:
            c_filename = os.path.splitext(filename)[0] + ".c"
            if os.path.isfile(c_filename):
                self.bufferCreate(c_filename)

            # If not, just open the requested .py, if any.
            # Needs to be after the C file so the tab focus is correct.
            if os.path.isfile(filename):
                    self.bufferCreate(filename)

        self.Bind(wx.EVT_MENU, self.OnNewFile, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAsFile, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnCheckModel, id=ID_CHECK_MODEL)
        self.Bind(wx.EVT_MENU, self.OnRun, id=ID_RUN)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateCompileMenu, id=ID_CHECK_MODEL)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateCompileMenu, id=ID_RUN)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        if not title.count('Python Shell'):
            # Delete menu item (open and new) if not python shell
            #self.fileMenu.Delete(wx.ID_NEW)
            self.fileMenu.Delete(wx.ID_OPEN)


    def _add_menu(self):
        """
        Add menu
        """
        self.compileMenu = wx.Menu()
        self.compileMenu.Append(ID_CHECK_MODEL, 'Check model',
                 'Loading and run the model')
        self.compileMenu.AppendSeparator()
        self.compileMenu.Append(ID_RUN, 'Run in Shell',
                 'Run the file in the Python Shell')
        self.MenuBar.Insert(3, self.compileMenu, '&Run')

    def OnHelp(self, event):
        """
        Show a help dialog.
        """
        import  wx.lib.dialogs
        title = 'Help on key bindings'
        text = wx.py.shell.HELP_TEXT
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, text, title,
                                                   size=((700, 540)))
        fnt = wx.Font(10, wx.TELETYPE, wx.NORMAL, wx.NORMAL)
        dlg.GetChildren()[0].SetFont(fnt)
        dlg.GetChildren()[0].SetInsertionPoint(0)
        dlg.ShowModal()
        dlg.Destroy()

    def set_manager(self, manager):
        """
        Set the manager of this window
        """
        self._manager = manager

    def OnAbout(self, event):
        """
        On About
        """
        message = ABOUT
        dial = wx.MessageDialog(self, message, 'About',
                           wx.OK | wx.ICON_INFORMATION)
        dial.ShowModal()

    def OnNewFile(self, event):
        """
        OnFileOpen
        """
        self.OnFileNew(event)

    def OnOpenFile(self, event):
        """
        OnFileOpen
        """
        self.OnFileOpen(event)
        self.Show(False)
        self.Show(True)

    def OnSaveFile(self, event):
        """
        OnFileSave overwrite
        """
        self.OnFileSave(event)
        self.Show(False)
        self.Show(True)

    def OnSaveAsFile(self, event):
        """
        OnFileSaveAs overwrite
        """
        self.OnFileSaveAs(event)
        self.Show(False)
        self.Show(True)

    def bufferOpen(self):
        """
        Open file in buffer, bypassing editor bufferOpen
        """
        if self.bufferHasChanged():
            cancel = self.bufferSuggestSave()
            if cancel:
                return cancel
        filedir = ''
        if self.buffer and self.buffer.doc.filedir:
            filedir = self.buffer.doc.filedir
        if not filedir:
            filedir = self.dataDir
        result = editor.openSingle(directory=filedir,
                            wildcard='Python Files (*.py)|*.py')
        if result.path:
            self.bufferCreate(result.path)

        # See if there is a corresponding C file
        if result.path is not None:
            c_filename = os.path.splitext(result.path)[0] + ".c"
            if os.path.isfile(c_filename):
                self.bufferCreate(c_filename)

        cancel = False
        return cancel

    def bufferSaveAs(self):
        """
        Save buffer to a new filename: Bypassing editor bufferSaveAs
        """
        filedir = ''
        if self.buffer and self.buffer.doc.filedir:
            filedir = self.buffer.doc.filedir
        if not filedir:
            filedir = self.dataDir
        result = editor.saveSingle(directory=filedir,
                                   filename='untitled.py',
                                   wildcard='Python Files (*.py)|*.py')
        if result.path:
            self.buffer.confirmed = True
            self.buffer.saveAs(result.path)
            cancel = False
        else:
            cancel = True
        return cancel

    def OnRun(self, event):
        """
        Run
        """
        if not self._check_saved():
            return True
        if self.buffer and self.buffer.doc.filepath:
            self.editor.setFocus()
            # Why we have to do this (Otherwise problems on Windows)?
            forward_path = self.buffer.doc.filepath.replace('\\', '/')
            self.shell.Execute("execfile('%s')" % forward_path)
            self.shell.Hide()
            self.shell.Show(True)
            return self.shell.GetText().split(">>>")[-2]
        else:
            mssg = "\n This is not a python file."
            title = 'Error'
            icon = wx.ICON_ERROR
            wx.MessageBox(str(mssg), title, style=icon)
            return False

    def OnCheckModel(self, event):
        """
        Compile
        """
        if not self._check_saved():
            return True
        fname = self.editor.getStatus()[0]
        success = show_model_output(self, fname)

        # Update plugin model list in fitpage combobox
        if success and self._manager is not None and self.panel is not None:
            self._manager.set_edit_menu_helper(self.parent)
            wx.CallAfter(self._manager.update_custom_combo)

    def _check_saved(self):
        """
        If content was changed, suggest to save it first
        """
        if self.bufferHasChanged() and self.buffer.doc.filepath:
            cancel = self.bufferSuggestSave()
            return not cancel
        return True

    def OnUpdateCompileMenu(self, event):
        """
        Update Compile menu items based on current tap.
        """
        win = wx.Window.FindFocus()
        id = event.GetId()
        event.Enable(True)
        try:
            if id == ID_CHECK_MODEL or id == ID_RUN:
                menu_on = False
                if self.buffer and self.buffer.doc.filepath:
                    menu_on = True
                event.Enable(menu_on)
        except AttributeError:
            # This menu option is not supported in the current context.
            event.Enable(False)

    def on_close(self, event):
        """
        Close event
        """
        if self.base is not None:
            self.base.py_frame = None
        self.Destroy()

ABOUT = "Welcome to Python %s! \n\n" % sys.version.split()[0]
ABOUT += "This uses Py Shell/Editor in wx (developed by Patrick K. O'Brien).\n"
ABOUT += "If this is your first time using Python, \n"
ABOUT += "you should definitely check out the tutorial "
ABOUT += "on the Internet at http://www.python.org/doc/tut/."


if __name__ == "__main__":

    app = wx.App()
    dlg = PyConsole()
    dlg.Show()
    app.MainLoop()

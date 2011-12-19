"""
Console Module display Python console
"""
import sys
import os
import wx
import wx.lib.dialogs
import wx.py.editor as editor
import wx.py.frame as frame
import py_compile

if sys.platform.count("win32")>0:
    PANEL_WIDTH = 800
    PANEL_HEIGHT = 600
    FONT_VARIANT = 0
else:
    PANEL_WIDTH = 830
    PANEL_HEIGHT = 620
    FONT_VARIANT = 1
ID_COMPILE = wx.NewId() 
ID_RUN = wx.NewId()  

def compile_file(path):
    """
    Compile a python file
    """
    try:
        import py_compile
        py_compile.compile(file=path, doraise=True)
    except:
        type, value, traceback = sys.exc_info()
        return value
    return None 

class PyConsole(editor.EditorNotebookFrame):
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Custom Model Editor"
    ## Name to appear on the window title bar
    window_caption = "Custom Model Editor"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = False
    def __init__(self, parent=None, manager=None, panel=None,
                    title='Python Shell/Editor', filename=None,
                    size=(PANEL_WIDTH, PANEL_HEIGHT)):
        self.config = None
        editor.EditorNotebookFrame.__init__(self, parent=parent, 
                                        title=title, size=size,
                                        filename=filename)
        self.parent = parent
        self._manager = manager
        self.panel = panel
        self._add_menu()
        if filename != None:
            dataDir = os.path.dirname(filename)
        elif self.parent != None:
            dataDir = self.parent._default_save_location
        else:
             dataDir = None
        self.dataDir = dataDir
        self.Centre()
        self.fileMenu.FindItemById(wx.ID_NEW).Enable(False)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAsFile, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnCompile, id=ID_COMPILE)
        self.Bind(wx.EVT_MENU, self.OnRun, id=ID_RUN)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateCompileMenu, id=ID_COMPILE)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateCompileMenu, id=ID_RUN)
        
    def _add_menu(self):
        """
        Add menu
        """
        self.compileMenu = wx.Menu()
        self.compileMenu.Append(ID_COMPILE, 'Compile',
                 'Compile the file')
        self.compileMenu.AppendSeparator()
        self.compileMenu.Append(ID_RUN, 'Run',
                 'Run the file in the Python Shell')
        self.MenuBar.Insert(3, self.compileMenu, '&Compile')
    
    def OnHelp(self, event):
        """
        Show a help dialog.
        """
        import  wx.lib.dialogs
        title = 'Help on key bindings'
        text = wx.py.shell.HELP_TEXT
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, text, title,
                                                   size = ((700, 540)))
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
                           wx.OK|wx.ICON_INFORMATION)  
        dial.ShowModal()

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

    def bufferSaveAs(self):
        """
        Save buffer to a new filename: Bypass the annoying suggest save 
        """
        filedir = ''
        if self.buffer and self.buffer.doc.filedir:
            filedir = self.buffer.doc.filedir
        result = editor.saveSingle(directory=filedir)
        if result.path:
            self.buffer.saveAs(result.path)
            cancel = False
        else:
            cancel = True
        return cancel
    
    def update_custom_combo(self):
        """
        Update custom model combo box in fit_panel
        """
        try:
            page = self.panel.get_current_page()
            temp = self.panel.reset_pmodel_list()
            if temp:
                page.model_list_box = temp
                current_val = page.formfactorbox.GetValue()
                pos = page.formfactorbox.GetSelection()
                page._show_combox_helper()
                page.formfactorbox.SetSelection(pos)
                page.formfactorbox.SetValue(current_val)
        except:
            pass
        
    def OnRun(self, event):
        """
        Run
        """
        if self._check_changed():
            return True
        if self.buffer and self.buffer.doc.filepath:
            self.editor.setFocus()
            # Why we have to do this (Otherwise problems on Windows)?
            forward_path = self.buffer.doc.filepath.replace('\\', '/')
            self.shell.Execute("execfile('%s')"% forward_path)
            self.shell.Hide()
            self.shell.Show(True)
            self.shell.SetFocus()
        else:
            mssg = "\n This is not a python file."
            title = 'Error'
            icon = wx.ICON_ERROR
            wx.MessageBox(str(mssg), title, style=icon)
        
    def OnCompile(self, event):
        """
        Compile
        """
        if self._check_changed():
            return True
        if self._get_err_msg():
            if self._manager != None and self.panel != None:
                self._manager.set_edit_menu(self.parent)
                wx.CallAfter(self.update_custom_combo)
    
    def _check_changed(self):   
        """
        If content was changed, suggest to save it first
        """
        if self.bufferHasChanged() and self.buffer.doc.filepath:
            cancel = self.bufferSuggestSave()
            if cancel:
                return cancel
             
    def _get_err_msg(self):
        """
        Get err_msg
        """
        name = None
        mssg = "\n This is not a python file."
        title = 'Error'
        icon = wx.ICON_ERROR
        try:
            fname = self.editor.getStatus()[0]
            name = os.path.basename(fname)
            if name.split('.')[-1] != 'py':
                wx.MessageBox(str(mssg), title, style=icon)
                return False
            msg = compile_file(fname)
        except:
            msg = None
        if name == None:
            wx.MessageBox(str(mssg), title, style=icon)
            return False
        mssg = "Compiling '%s'...\n"% name
        if msg != None:
            mssg += "Error occurred:\n"
            mssg += str(msg)
            title = 'Warning'
            icon = wx.ICON_WARNING
        else:
            mssg += "Successful."
            title = 'Info'
            icon = wx.ICON_INFORMATION
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, mssg, title, 
                                                   size = ((550, 250)))
        fnt = wx.Font(10, wx.TELETYPE, wx.NORMAL, wx.NORMAL)
        dlg.GetChildren()[0].SetFont(fnt)
        dlg.GetChildren()[0].SetInsertionPoint(0)
        dlg.ShowModal()
        dlg.Destroy()
        return True
    
    def OnUpdateCompileMenu(self, event):
        """
        Update Compile menu items based on current tap.
        """
        win = wx.Window.FindFocus()
        id = event.GetId()
        event.Enable(True)
        try:
            if id == ID_COMPILE or id == ID_RUN:
                menu_on = False
                if self.buffer and self.buffer.doc.filepath:
                    menu_on = True
                event.Enable(menu_on)
        except AttributeError:
            # This menu option is not supported in the current context.
            event.Enable(False)
            
ABOUT =  "Welcome to Python %s! \n\n"% sys.version.split()[0]
ABOUT += "This uses Py Shell/Editor in wx (developed by Patrick K. O'Brien).\n"
ABOUT += "If this is your first time using Python, \n"
ABOUT += "you should definitely check out the tutorial "
ABOUT += "on the Internet at http://www.python.org/doc/tut/."
 
        
if __name__ == "__main__":
   
    app  = wx.App()
    dlg = PyConsole()
    dlg.Show()
    app.MainLoop()
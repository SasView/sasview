"""
    Panel class to show the model history
"""
#TODO: when a model change is followed by a parameter change,
#      we end up with the same model twice in a row in the history
#TODO: implement aging of history items

import wx
import wx.lib.newevent
import config

# History events
(HistoryEvent, EVT_HISTORY) = wx.lib.newevent.NewEvent()

# Maximum number of full history events in the buffer
MAX_BUFF_LEN = 30

isWindows = False
import sys
if sys.platform.count("win32")>0:
    isWindows = True
    
if isWindows:
    from ctypes import *
    from ctypes.wintypes import DWORD

    SIZE_T = c_ulong

    class _MEMORYSTATUS(Structure):
        _fields_ = [("dwLength", DWORD),
                    ("dwMemoryLength", DWORD),
                    ("dwTotalPhys", SIZE_T),
                    ("dwAvailPhys", SIZE_T),
                    ("dwTotalPageFile", SIZE_T),
                    ("dwAvailPageFile", SIZE_T),
                    ("dwTotalVirtual", SIZE_T),
                    ("dwAvailVirtualPhys", SIZE_T)]
        def show(self):
            for field_name, field_type in self._fields_:
                print field_name, getattr(self, field_name)
    



class HistoryPanel(wx.Panel):
    """
        Panel to show history items
    """
    #TODO: show units
    #TODO: order parameters properly
    ## Internal name for the AUI manager
    window_name = "historyPanel"
    ## Title to appear on top of the window
    window_caption = "historyPanel"
    
    CENTER_PANE = False
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Listen to history events
        self.parent.Bind(EVT_HISTORY, self.onEVT_HISTORY)

        # Internal counter of history items
        self.counter = 0
        
        # Buffer filled flag
        self.buffer_filled = False
        
        # Set up the layout
        self._set_layout()
        
        # Save current flag
        self.current_saved = False
        
    def _set_layout(self):
        """
            Set up the layout of the panel
        """
        self.sizer = wx.GridBagSizer(0,5)
        
        title = wx.StaticText(self, -1, "History", style=wx.ALIGN_LEFT)         
        self.sizer.Add(title, (0,0), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)

        self.view_box = wx.ListBox(self, 101, wx.DefaultPosition, (295, 200), 
                                   [], wx.LB_SINGLE | wx.LB_HSCROLL)
        
        self.sizer.Add(self.view_box, (1,0), flag=wx.TOP, border=0)
        
        self.SetSizer(self.sizer)
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowPopup, id=101)
        self.Bind(wx.EVT_LISTBOX, self.onSelect, id=101)
        
    def onRemove(self, ev):
        """
            Remove an item
        """
        indices = self.view_box.GetSelections()
        if len(indices)>0:
            self.view_box.Delete(indices[0])
        
    def onRename(self, ev):
        """
            Rename an item
        """
        indices = self.view_box.GetSelections()
        if len(indices)>0:
            print "NOT YET IMPLMENTED"
            print "renaming", self.view_box.GetString(indices[0])
        
    def onShowPopup(self, event):
        """
            Popup context menu event
        """
        # menu
        popupmenu = wx.Menu()
        id = wx.NewId()
        popupmenu.Append(id, "&Remove Selected")
        #popupmenu.Append(102, "&Rename Selected")
        wx.EVT_MENU(self, id, self.onRemove)
        #wx.EVT_MENU(self, 102, self.onRename)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(popupmenu, pos)

    def onSelect(self, event):
        """
            Process item selection events
        """
        index = event.GetSelection()
        view_name = self.view_box.GetString(index)
        view = event.GetClientData()

        wx.PostEvent(self.parent, view)
                
    def onEVT_HISTORY(self, event):
        """
            Process EVT_HISTORY events
            When a history event arrives, put it in the list
            of history items
            
            @param event: EVT_HISTORY event
        """
        print "onEVT_HISTORY",event.name
        #TODO: this will only work on Windows
        import distutils.util
        isWindows = False
        if sys.platform.count("win32")>0:
            isWindows = True
            
        if isWindows:
            memstatus = _MEMORYSTATUS()
            windll.kernel32.GlobalMemoryStatus(byref(memstatus))
            size_0   = getattr(memstatus, 'dwAvailPhys')
            size_obj = 1000.0
            if not event.item.state._data_2D == None:
                size_obj = len(event.item.state._data_2D)*len(event.item.state._data_2D)*32.0
        
        #print "HistoryPanel.EVT_HISTORY"
        self.counter += 1
        self.view_box.Insert("%d: %s" % (self.counter, event.name), 
                             self.view_box.GetCount(), event.item)
                
        deleteOldItem = False
        if isWindows:
            # This break our scheme of the history panel not knowing
            # about the events, but we need to protect against 
            # filling up the memory. 
            # TODO: fix this
        
            if size_0/size_obj < 10:
                deleteOldItem = True
                
        else:
        
            # If the buffer is already full, write the earlier ones
            # in a file.
            if self.view_box.GetCount() > MAX_BUFF_LEN:
                deleteOldItem = True
            
        if deleteOldItem:
            #item_0 = self.view_box.GetString(0)
            #import os
            # Write it
            #filename = "history_%i.dat" % os.getpid()
            #fd = open(filename,'a')
            #fd.write("test\n")    
        
            # For now, delete item from list 
            if not self.buffer_filled:
                evt = config.StatusBarEvent( \
                    message = "Memory running low, oldest history events will be deleted")
                    #message = "Maximum number of history events reached (%g)" % MAX_BUFF_LEN)
                wx.PostEvent(self.parent, evt)
                self.buffer_filled = True
            
            self.view_box.Delete(0)



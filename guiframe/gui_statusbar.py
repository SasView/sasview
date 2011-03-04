import wx
from wx import StatusBar as wxStatusB
from wx.lib import newevent

#numner of fields of the status bar 
NB_FIELDS = 4
#position of the status bar's fields
ICON_POSITION = 0
MSG_POSITION  = 1
GAUGE_POSITION  = 2
CONSOLE_POSITION  = 3
BUTTON_SIZE = 40

CONSOLE_WIDTH = 340
CONSOLE_HEIGHT = 240

class ConsolePanel(wx.Panel):
    """
    """
    def __init__(self, parent, *args, **kwargs):
        """
        """
        wx.Panel.__init__(self, parent=parent, *args, **kwargs)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.msg_txt = wx.TextCtrl(self, size=(CONSOLE_WIDTH-40,
                                                CONSOLE_HEIGHT-60), 
                                        style=wx.TE_MULTILINE)
        self.msg_txt.SetEditable(False)
        self.msg_txt.SetValue('No message available')
        self.sizer.Add(self.msg_txt, 1, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self.sizer)
        
    def set_message(self, status=""):
        """
        """
        msg = status + "\n"  
        self.msg_txt.AppendText(str(msg))
        
class Console(wx.Frame):
    """
    """
    def __init__(self, parent=None, status="", *args, **kwds):
        kwds["size"] = (CONSOLE_WIDTH, CONSOLE_HEIGHT)
        kwds["title"] = "Console"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.panel = ConsolePanel(self)
        self.panel.set_message(status=status)
        wx.EVT_CLOSE(self, self.Close)
        self.Show(True)
        
    def set_multiple_messages(self, messages=[]):
        """
        """
        if messages:
            for status in messages:
                self.panel.set_message(status)
                
    def set_message(self, message):
        """
        """
        self.panel.set_message(str(message))
        
    def Close(self, event):
        """
        """
        self.Hide()
        
class StatusBar(wxStatusB):
    """
    """
    def __init__(self, parent, *args, **kargs):
        wxStatusB.__init__(self, parent, *args, **kargs)
        """
        Implement statusbar functionalities 
        """
        self.parent = parent
        self.parent.SetStatusBarPane(MSG_POSITION)
        #Layout of status bar
        self.SetFieldsCount(NB_FIELDS) 
        self.SetStatusWidths([BUTTON_SIZE, -2, -1, BUTTON_SIZE])
        #display default message
        self.msg_position = MSG_POSITION 
        #save the position of the gauge
        width, height = self.GetSize()
        self.gauge = wx.Gauge(self, size=(width/10, height-3),
                               style=wx.GA_HORIZONTAL)
        self.gauge.Hide()
        #status bar icon
        self.bitmap_bt_warning = wx.BitmapButton(self, -1,
                                                 size=(BUTTON_SIZE,-1),
                                                  style=wx.NO_BORDER)
        console_bmp = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_TOOLBAR)
        self.bitmap_bt_console = wx.BitmapButton(self, -1, 
                                 size=(BUTTON_SIZE-5, height-4))
        self.bitmap_bt_console.SetBitmapLabel(console_bmp)
        console_hint = "History of status bar messages"
        self.bitmap_bt_console.SetToolTipString(console_hint)
        self.bitmap_bt_console.Bind(wx.EVT_BUTTON, self._onMonitor,
                                            id=self.bitmap_bt_console.GetId())
        
        self.reposition()
        ## Current progress value of the bar 
        self.nb_start = 0
        self.nb_progress = 0
        self.nb_stop = 0
        self.frame = None
        self.list_msg = []
        self.frame = Console(parent=self)
        self.frame.set_multiple_messages(self.list_msg)
        self.frame.Hide()
        self.progress = 0      
        self.timer = wx.Timer(self, -1) 
        self.timer_stop = wx.Timer(self, -1) 
        self.thread = None
        self.Bind(wx.EVT_TIMER, self._on_time, self.timer) 
        self.Bind(wx.EVT_TIMER, self._on_time_stop, self.timer_stop) 
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
    def reposition(self):
        """
        """
        rect = self.GetFieldRect(GAUGE_POSITION)
        self.gauge.SetPosition((rect.x + 5, rect.y - 2))
        rect = self.GetFieldRect(ICON_POSITION)
        self.bitmap_bt_warning.SetPosition((rect.x + 5, rect.y - 2))
        rect = self.GetFieldRect(CONSOLE_POSITION)
        self.bitmap_bt_console.SetPosition((rect.x - 5, rect.y - 2))
        self.sizeChanged = False
        
    def OnIdle(self, event):
        """
        """
        if self.sizeChanged:
            self.reposition()
            
    def OnSize(self, evt):
        """
        """
        self.reposition() 
        self.sizeChanged = True
        
    def get_msg_position(self):
        """
        """
        return self.msg_position
    
    def SetStatusText(self, text="", number=MSG_POSITION):
        """
        """
        wxStatusB.SetStatusText(self, text, number)
        self.list_msg.append(text)
        icon_bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR)
        self.bitmap_bt_warning.SetBitmapLabel(icon_bmp)
      
        if self.frame is not None :
            self.frame.set_message(text)
        
    def PopStatusText(self, *args, **kwds):
        """
        Override status bar 
        """
        wxStatusB.PopStatusText(self, field=MSG_POSITION)
      
    def PushStatusText(self, *args, **kwds):
        """
        """
        wxStatusB.PushStatusText(self, field=MSG_POSITION, string=string)
        
    def enable_clear_gauge(self):
        """
        clear the progress bar
        """
        flag = False
        if (self.nb_start <= self.nb_stop) or \
            (self.nb_progress <= self.nb_stop):
            flag = True
        return flag
    
    def _on_time_stop(self, evt): 
        """
        Clear the progress bar
        
        :param evt: wx.EVT_TIMER 
  
        """ 
        count = 0
        while(count <= 100):
            count += 1
        self.timer_stop.Stop() 
        self.clear_gauge(msg="")
        self.nb_progress = 0 
        self.nb_start = 0 
        self.nb_stop = 0
       
    def _on_time(self, evt): 
        """
        Update the progress bar while the timer is running 
        
        :param evt: wx.EVT_TIMER 
  
        """ 
        # Check stop flag that can be set from non main thread 
        if self.timer.IsRunning(): 
            self.gauge.Pulse()
   
    def clear_gauge(self, msg=""):
        """
        Hide the gauge
        """
        self.progress = 0
        self.gauge.SetValue(0)
        self.gauge.Hide() 
         
    def set_icon(self, event):
        """
        display icons related to the type of message sent to the statusbar
        when available
        """
        if not hasattr(event, "info"):
            return 
        msg = event.info.lower()
        if msg == "warning":
            icon_bmp =  wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_TOOLBAR)
            self.bitmap_bt_warning.SetBitmapLabel(icon_bmp)
        if msg == "error":
            icon_bmp =  wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_TOOLBAR)
            self.bitmap_bt_warning.SetBitmapLabel(icon_bmp)
        if msg == "info":
            icon_bmp =  wx.ArtProvider.GetBitmap(wx.ART_INFORMATION,
                                                 wx.ART_TOOLBAR)
            self.bitmap_bt_warning.SetBitmapLabel(icon_bmp)
    
    def set_message(self, event):
        """
        display received message on the statusbar
        """
        if hasattr(event, "status"):
            self.SetStatusText(str(event.status))
       
 
    def set_gauge(self, event):
        """
        change the state of the gauge according the state of the current job
        """
        if not hasattr(event, "type"):
            return
        type = event.type
        self.gauge.Show(True)
        if type.lower() == "start":
            self.nb_start += 1
            #self.timer.Stop()
            self.progress += 10
            self.gauge.SetValue(int(self.progress)) 
            self.progress += 10
            if self.progress < self.gauge.GetRange() - 20:
                self.gauge.SetValue(int(self.progress)) 
        if type.lower() == "progress":
            self.nb_progress += 1
            self.timer.Start(1)
            self.gauge.Pulse()
        if type.lower() == "update":
            self.progress += 10
            if self.progress < self.gauge.GetRange()- 20:
                self.gauge.SetValue(int(self.progress))   
        if type.lower() == "stop":
            self.nb_stop += 1
            self.gauge.Show(True)
            if self.enable_clear_gauge():
                self.timer.Stop()
                self.progress = 0
                self.gauge.SetValue(90) 
                self.timer_stop.Start(3) 
                    
    def set_status(self, event):
        """
        Update the status bar .
        
        :param type: type of message send.
            type  must be in ["start","progress","update","stop"]
        :param msg: the message itself  as string
        :param thread: if updatting using a thread status 
        
        """
        self.set_message(event=event)
        self.set_icon(event=event)
        self.set_gauge(event=event)
    
    def _onMonitor(self, event):
        """
        Pop up a frame with messages sent to the status bar
        """
        self.frame.Show(True)
        
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = wx.Frame(None, wx.ID_ANY, 'test frame')
    statusBar = StatusBar(frame, wx.ID_ANY)
    frame.SetStatusBar(statusBar)
    frame.Show(True)
    event = MessageEvent()
    event.type = "progress"
    event.status  = "statusbar...."
    event.info = "error"
    statusBar.set_status(event=event)
    app.MainLoop()


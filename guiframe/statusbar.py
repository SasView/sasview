import wx
from wx import StatusBar as wxStatusB
import wx.lib
from wx.lib import newevent
#numner of fields of the status bar 
NB_FIELDS = 3
#position of the status bar's fields
ICON_POSITION = 0
MSG_POSITION  = 1
GAUGE_POSITION  = 2
BUTTON_SIZE = 40
class StatusBar(wxStatusB):
    def __init__(self, parent, *args, **kargs):
         wxStatusB.__init__(self, parent, *args, **kargs)
         """
             Implement statusbar functionalities 
         """
         self.parent= parent
         self.parent.SetStatusBarPane(MSG_POSITION)
       
         #Layout of status bar
         self.SetFieldsCount(NB_FIELDS) 
         self.SetStatusWidths([BUTTON_SIZE, -2, -1])
         
         #display default message
         self.msg_position = MSG_POSITION 
       
         #save the position of the gauge
         width, height = self.GetSize()
         self.gauge = wx.Gauge(self, size=(width/10,height-3),
                               style= wx.GA_HORIZONTAL)
         rect = self.GetFieldRect(GAUGE_POSITION)
         self.gauge.SetPosition((rect.x+5, rect.y-2))
         self.gauge.Hide()
         
         #status bar icon
         icon_bmp =  wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR)
         self.bitmap_bt_warning = wx.BitmapButton(self, -1, size=(BUTTON_SIZE,-1),
                                                  style=wx.NO_BORDER)
         self.bitmap_bt_warning.SetBitmapLabel(icon_bmp)
         rect = self.GetFieldRect(ICON_POSITION)
         self.bitmap_bt_warning.SetPosition((rect.x+5, rect.y-2))
        
         ## Current progress value of the bar 
         self.progress = 0      
         self.timer = wx.Timer(self, -1) 
         self.timer_stop = wx.Timer(self, -1) 
         self.thread = None
         self.Bind(wx.EVT_TIMER,self.OnTimer, self.timer) 
         self.Bind(wx.EVT_TIMER,self.OnTimer_stop, self.timer_stop) 
        
    def get_msg_position(self):
        """
        """
        return self.msg_position
    
    def SetStatusText(self, text="", number=MSG_POSITION):
        """
        """
        wxStatusB.SetStatusText(self, text, MSG_POSITION)
        
    def PopStatusText(self, *args, **kwds):
        wxStatusB.PopStatusText(self, field=MSG_POSITION)
      
    def PushStatusText(self, *args, **kwds):
        wxStatusB.PushStatusText(self, field=MSG_POSITION,string=string)
        
    def OnTimer_stop(self, evt): 
        """Clear the progress bar
        @param evt: wx.EVT_TIMER 
  
        """ 
        count = 0
        while(count <= 100):
            count += 1
        self.timer_stop.Stop() 
        self.clear_gauge(msg="Complete")
       
    def OnTimer(self, evt): 
        """Update the progress bar while the timer is running 
        @param evt: wx.EVT_TIMER 
  
        """ 
        # Check stop flag that can be set from non main thread 
        if self.timer.IsRunning(): 
            self.gauge.Pulse()
    """   
    def set_progress(self): 
        #Set the gauge value given the status of a thread
        self.gauge.Show(True)
        if self.timer.IsRunning(): 
            while(self.thread.isrunning()):
                self.progress += 1
                # Update the progress value if it is less than the range 
                if self.progress < self.gauge.GetRange()-20: 
                    self.gauge.SetValue(int(self.progress)) 
                else:
                    self.gauge.SetValue(70) 
                    self.progress = 0
                    self.timer.Stop()
            self.timer.Stop()
            self.gauge.SetValue(90) 
            self.progress =0
    """        
    def clear_gauge(self, msg=""):
        """
            Hide the gauge
        """
        self.SetStatusText(str(msg), MSG_POSITION)
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
            icon_bmp =  wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR)
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
        if type.lower()=="start":
            self.timer.Stop()
            self.progress += 10
            self.gauge.SetValue(int(self.progress)) 
            self.progress += 10
            if self.progress < self.gauge.GetRange()-20:
                self.gauge.SetValue(int(self.progress)) 
        if type.lower()=="progress":
            self.timer.Start(100)
            self.gauge.Pulse()
        if type.lower()=="update":
            self.timer.Stop()
            self.progress += 10
            if self.progress < self.gauge.GetRange()-20:
                self.gauge.SetValue(int(self.progress))   
        if type.lower()=="stop":
            self.gauge.Show(True)
            self.timer.Stop()
            self.progress = 0
            self.gauge.SetValue(90) 
            self.timer_stop.Start(3) 
                    
    def set_status(self, event):
        """
            Update the status bar .
            @param type: type of message send.
            type  must be in ["start","progress","update","stop"]
            @param msg: the message itself  as string
            @param thread: if updatting using a thread status 
        """
        self.set_icon(event=event)
        self.set_message(event=event)
        self.set_gauge(event=event)
        
if __name__ == "__main__":
     app = wx.PySimpleApp()
     frame= wx.Frame(None,wx.ID_ANY,'test frame')
     statusBar = StatusBar(frame, wx.ID_ANY)
     frame.SetStatusBar(statusBar)
     frame.Show(True)
     (NewPlotEvent, EVT_NEW_PLOT) = wx.lib.newevent.NewEvent()
     event = NewPlotEvent()
     event.type = "progress"
     event.status  = "statusbar...."
     event.info = "info"
     statusBar.set_status(event=event)
     app.MainLoop()


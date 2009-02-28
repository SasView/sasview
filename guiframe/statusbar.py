import wx
class MyStatusBar(wx.StatusBar):
    def __init__(self,*args,**kargs):
         wx.StatusBar.__init__(self, *args,**kargs)
         #Layout of status bar
         self.SetFieldsCount(2) 
         width,height = self.GetSize()
         self.gauge = wx.Gauge(self, size=(-1,height-4),style= wx.GA_HORIZONTAL)
         self.SetStatusWidths([-4, -1])
         rect = self.GetFieldRect(1)
         self.gauge.SetPosition((rect.x+5, rect.y-2))
         
         self.gauge.Hide()
         
         #Progess 

         self.progress = 0       # Current progress value of the bar 
         self.timer = wx.Timer(self,-1) 
         self.timer_stop = wx.Timer(self,-1) 
         self.thread= None
         self.Bind(wx.EVT_TIMER,self.OnTimer, self.timer) 
         self.Bind(wx.EVT_TIMER,self.OnTimer_stop, self.timer_stop) 
         self.count=0
         
    def OnTimer_stop(self, evt): 
        """Update the progress bar while the timer is running 
        @param evt: wx.EVT_TIMER 
  
        """ 
        self.count +=1
        if self.count ==45:
            self.timer_stop.Stop() 
            self.gauge.Hide()
            self.SetStatusText( "", 0)
            self.count=0
    def OnTimer(self, evt): 
        """Update the progress bar while the timer is running 
        @param evt: wx.EVT_TIMER 
  
        """ 
        # Check stop flag that can be set from non main thread 
        if self.timer.IsRunning(): 
            self.gauge.Pulse()
       
       
    def set_progress(self):
        self.gauge.Show(True)
        if self.timer.IsRunning(): 
            while(self.thread.isrunning()):
                self.progress += 1
                # Update the progress value if it is less than the range 
                if self.progress < self.gauge.GetRange()-20: 
                    self.gauge.SetValue(int(self.progress)) 
                else:
                    self.gauge.SetValue(70) 
                    self.progress =0
                    self.timer.Stop()
                    #self.gauge.Hide()
            self.timer.Stop()
            self.gauge.SetValue(90) 
            self.progress =0
            
    def clear_gauge(self, msg=""):
        self.timer.Stop()
        self.SetStatusText( str(msg), 0)
        self.progress =0
        self.gauge.SetValue(0)
        self.gauge.Hide() 
         
    def set_status(self, type=None,msg="", thread=None):
        if type==None:
            self.SetStatusText(str(msg),0)
        
        else:
            self.thread= thread
            self.gauge.Show(True)
            if type.lower()=="start":
                self.timer.Stop()
                self.SetStatusText( str(msg), 0)
                self.progress +=10
                self.gauge.SetValue(int(self.progress)) 
                #self.timer.Start(1000)
                #print "went here"
                #self.set_progress()
                self.progress +=10
                if self.progress < self.gauge.GetRange()-20:
                    self.gauge.SetValue(int(self.progress)) 
            if type.lower()=="progress":
                self.timer.Start(100)
                self.SetStatusText( str(msg), 0)
                self.gauge.Pulse()
                #print "in progress"
                
            if  type.lower()=="update":
                
                self.timer.Stop()
                self.SetStatusText( str(msg), 0)
                self.progress +=10
                if self.progress < self.gauge.GetRange()-20:
                    self.gauge.SetValue(int(self.progress)) 
                    
            if type.lower()=="stop":
                self.gauge.Show(True)
                self.timer.Stop()
                self.SetStatusText( str(msg), 0)
                self.progress =0
                self.gauge.SetValue(90) 
                self.timer_stop.Start(3)    
            
   
    
if __name__ == "__main__":
     app = wx.PySimpleApp()
     frame= wx.Frame(None,wx.ID_ANY,'test frame')
     statusBar= MyStatusBar(frame,wx.ID_ANY)
     frame.SetStatusBar(statusBar)
     frame.Show(True)
     statusBar.SetStatusText("status text..")
     statusBar.set_status( "progress","progessing")
     
     
     app.MainLoop()


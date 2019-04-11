"""
Defines and draws the status bar that should appear along the bottom of the
main SasView window.
"""
import wx
import sys
import logging
import datetime
from wx import StatusBar as wxStatusB
from wx.lib import newevent
import wx.richtext
from sas.sasgui.guiframe.gui_style import GUIFRAME_ICON

logger = logging.getLogger(__name__)

# Number of fields on the status bar
NB_FIELDS = 4
#position of the status bar's fields
ICON_POSITION = 0
MSG_POSITION = 1
GAUGE_POSITION = 2
CONSOLE_POSITION = 3
BUTTON_SIZE = 40
STATUS_BAR_ICON_SIZE = 12
CONSOLE_WIDTH = 500
CONSOLE_HEIGHT = 300

if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
else:
    FONT_VARIANT = 1

GREEN = wx.Colour(95, 190, 95)
YELLOW = wx.Colour(247, 214, 49)
RED = wx.Colour(234, 89, 78)

class ConsolePanel(wx.Panel):
    """
    Interaction class for adding messages to the Console log.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent=parent, *args, **kwargs)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.msg_txt = wx.richtext.RichTextCtrl(self, size=(CONSOLE_WIDTH-40,
                                                CONSOLE_HEIGHT-60),
                                   style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER)

        self.msg_txt.SetEditable(False)
        timestamp = datetime.datetime.now()
        status = '{:%Y-%m-%d %H:%M:%S} : No message available'.format(timestamp)
        self.msg_txt.SetValue(status)
        self.sizer.Add(self.msg_txt, 1, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self.sizer)

    def set_message(self, status="", event=None):
        """
        Adds a message to the console log as well as the main sasview.log

        :param status: A status message to be sent to the console log.
        :param event: A wx event.
        """
        status = str(status)
        if status.strip() == "":
            return
        # Add timestamp
        timestamp = datetime.datetime.now()
        status = '{:%Y-%m-%d %H:%M:%S} : '.format(timestamp) + status
        color = (0, 0, 0) #black
        icon_bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR)
        if hasattr(event, "info"):
            icon_type = event.info.lower()
            if icon_type == "warning":
                logger.warning(status)
                color = (0, 0, 255) # blue
                icon_bmp = wx.ArtProvider.GetBitmap(wx.ART_WARNING,
                                                    wx.ART_TOOLBAR)
            if icon_type == "error":
                logger.error(status)
                color = (255, 0, 0) # red
                icon_bmp = wx.ArtProvider.GetBitmap(wx.ART_ERROR,
                                                    wx.ART_TOOLBAR)
            if icon_type == "info":
                icon_bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION,
                                                    wx.ART_TOOLBAR)
        self.msg_txt.Newline()
        # wx 3 has WriteImage and WriteBitmap; not sure if there
        # is any difference between them.  wx 4 has only WriteImage.
        self.msg_txt.WriteImage(icon_bmp)
        self.msg_txt.BeginTextColour(color)
        self.msg_txt.WriteText("\t")
        self.msg_txt.AppendText(status)
        self.msg_txt.EndTextColour()


class Console(wx.Frame):
    """
    The main class defining the Console window.
    """
    def __init__(self, parent=None, status="", *args, **kwds):
        kwds["size"] = (CONSOLE_WIDTH, CONSOLE_HEIGHT)
        kwds["title"] = "Console"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.SetWindowVariant(FONT_VARIANT)
        self.panel = ConsolePanel(self)
        self.panel.set_message(status=status)
        wx.EVT_CLOSE(self, self.Close)

    def set_multiple_messages(self, messages=[]):
        """
        Method to send an arbitrary number of messages to the console log

        :param messages: A list of strings to be sent to the console log. 
        """
        if messages:
            for status in messages:
                self.panel.set_message(status=status)

    def set_message(self, status, event=None):
        """
        Exposing the base ConsolePanel set_message

        :param status: A status message to be sent to the console log.
        :param event: A wx event.
        """
        self.panel.set_message(status=str(status), event=event)

    def Close(self, event):
        """
        Calling close on the panel will hide the panel.

        :param event: A wx event.
        """
        self.Hide()

class StatusBar(wxStatusB):
    """
        Application status bar
    """
    def __init__(self, parent, id):
        wxStatusB.__init__(self, parent, id)
        self.parent = parent
        self.parent.SetStatusBarPane(MSG_POSITION)

        #Layout of status bar
        width = STATUS_BAR_ICON_SIZE
        height = STATUS_BAR_ICON_SIZE
        self.SetFieldsCount(NB_FIELDS)
        # Leave some space for the resize handle in the last field
        console_btn_width = 80
        self.SetStatusWidths([width+4, -2, -1, width+console_btn_width])
        self.SetMinHeight(height + 10)

        #display default message
        self.msg_position = MSG_POSITION

        # Create progress bar
        gauge_width = 5 * width
        self.gauge = wx.Gauge(self, size=(gauge_width, height),
                              style=wx.GA_HORIZONTAL)
        self.gauge.Hide()

        # Create status bar icon reflecting the type of status
        # for the last message
        self.status_color = wx.StaticText(self, id=wx.NewId(), label="   ",
                                          size=wx.Size(15, 15))
        self.status_color.SetBackgroundColour(GREEN)
        self.status_color.SetForegroundColour(GREEN)

        # Create the button used to show the console dialog
        self.console_button = wx.Button(self, wx.NewId(), "Console",
                                        size=(console_btn_width, -1))
        font = self.console_button.GetFont()
        _, pixel_h = font.GetPixelSize()
        font.SetPixelSize(wx.Size(0, int(pixel_h*0.9)))
        self.console_button.SetFont(font)
        self.console_button.SetToolTipString("History of status bar messages")
        self.console_button.Bind(wx.EVT_BUTTON, self._onMonitor,
                                 id=self.console_button.GetId())

        self.reposition()
        ## Current progress value of the bar
        self.nb_start = 0
        self.nb_progress = 0
        self.nb_stop = 0
        self.frame = None
        self.list_msg = []
        self.frame = Console(parent=self)
        if hasattr(self.frame, "IsIconized"):
            if not self.frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    self.frame.SetIcon(icon)
                except:
                    try:
                        FRAME_ICON = wx.Icon(GUIFRAME_ICON.FRAME_ICON_PATH,
                                             wx.BITMAP_TYPE_ICO)
                        self.frame.SetIcon(FRAME_ICON)
                    except:
                        pass
        self.frame.set_multiple_messages(self.list_msg)
        self.frame.Hide()
        self.progress = 0
        self.timer = wx.Timer(self, -1)
        self.timer_stop = wx.Timer(self, -1)
        self.thread = None
        self.Bind(wx.EVT_TIMER, self._on_time, self.timer)
        self.Bind(wx.EVT_TIMER, self._on_time_stop, self.timer_stop)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def reposition(self):
        """
        Place the various fields in their proper position
        """
        rect = self.GetFieldRect(GAUGE_POSITION)
        self.gauge.SetPosition((rect.x, rect.y))
        rect = self.GetFieldRect(ICON_POSITION)
        self.status_color.SetPosition((rect.x, rect.y))
        rect = self.GetFieldRect(CONSOLE_POSITION)
        self.console_button.SetPosition((rect.x, rect.y))
        self.size_changed = False

    def on_idle(self, event):
        """
        When the window is idle, check if the window has been resized
        """
        if self.size_changed:
            self.reposition()

    def on_size(self, evt):
        """
        If the window is resized, redraw the window.
        """
        self.reposition() 
        self.size_changed = True

    def get_msg_position(self):
        """
        Get the last known message that was displayed on the console window.
        """
        return self.msg_position

    def SetStatusText(self, text="", number=MSG_POSITION, event=None):
        """
        Set the text that will be displayed in the status bar.
        """
        wxStatusB.SetStatusText(self, text.split('\n', 1)[0], number)
        self.list_msg.append(text)
        self.status_color.SetBackgroundColour(GREEN)
        self.status_color.SetForegroundColour(GREEN)

        if self.frame is not None:
            self.frame.set_message(status=text, event=event)

    def PopStatusText(self, *args, **kwds):
        """
        Override status bar
        """
        wxStatusB.PopStatusText(self, field=MSG_POSITION)

    def PushStatusText(self, *args, **kwds):
        """
        PushStatusText
        """
        text = "PushStatusText: What is this string?"
        wxStatusB.PushStatusText(self, field=MSG_POSITION, string=text)

    def enable_clear_gauge(self):
        """
        clear the progress bar
        """
        flag = True
        # Why we do this?
        #if (self.nb_start <= self.nb_stop) or \
        #    (self.nb_progress <= self.nb_stop):
        #    flag = True
        return flag

    def _on_time_stop(self, evt):
        """
        Clear the progress bar

        :param evt: wx.EVT_TIMER
        """
        count = 0
        while count <= 100:
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
        Display icons related to the type of message sent to the statusbar
        when available. No icon is displayed if the message is empty
        """
        if hasattr(event, "status"):
            status = str(event.status)
            if status.strip() == "":
                return
        else:
            return
        if not hasattr(event, "info"):
            return

        # Get the size of the button images
        height = STATUS_BAR_ICON_SIZE

        msg = event.info.lower()
        if msg == "warning":
            self.status_color.SetBackgroundColour(YELLOW)
            self.status_color.SetForegroundColour(YELLOW)
        elif msg == "error":
            self.status_color.SetBackgroundColour(RED)
            self.status_color.SetForegroundColour(RED)
        else:
            self.status_color.SetBackgroundColour(GREEN)
            self.status_color.SetForegroundColour(GREEN)

    def set_dialog(self, event):
        """
        Display dialogbox
        """
        if not hasattr(event, "info"):
            return
        msg = event.info.lower()
        if msg == "error":
            e_msg = "Error(s) Occurred:\n"
            e_msg += "\t" + event.status + "\n\n"
            e_msg += "Further information might be available in "
            e_msg += "the Console log (bottom right corner)."
            wx.MessageBox(e_msg, style=wx.ICON_ERROR)
        if msg == "warning":
            e_msg = "Warning:\n"
            e_msg += "\t" + event.status + "\n\n"
            e_msg += "Further information might be available in "
            e_msg += "the Console log (bottom right corner)."
            wx.MessageBox(e_msg, style=wx.ICON_EXCLAMATION)

    def set_message(self, event):
        """
        display received message on the statusbar
        """
        if hasattr(event, "status"):
            self.SetStatusText(text=str(event.status), event=event)
  
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
            self.progress += 5
            self.gauge.SetValue(int(self.progress))
            self.progress += 5
            if self.progress < self.gauge.GetRange() - 20:
                self.gauge.SetValue(int(self.progress))
        if type.lower() == "progress":
            self.nb_progress += 1
            self.timer.Start(1)
            self.gauge.Pulse()
        if type.lower() == "update":
            self.progress += 5
            if self.progress < self.gauge.GetRange()- 20:
                self.gauge.SetValue(int(self.progress))
        if type.lower() == "stop":
            self.nb_stop += 1
            self.gauge.Show(True)
            if self.enable_clear_gauge():
                self.timer.Stop()
                self.progress = 0
                self.gauge.SetValue(100)
                self.timer_stop.Start(5)

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
        # dialog on error
        self.set_dialog(event=event)

    def _onMonitor(self, event):
        """
        Pop up a frame with messages sent to the status bar
        """
        self.frame.Show(False)
        self.frame.Show(True)


class SPageStatusbar(wxStatusB):
    def __init__(self, parent, timeout=None, *args, **kwds):
        wxStatusB.__init__(self, parent, *args, **kwds)
        self.SetFieldsCount(1)
        self.timeout = timeout
        width, height = parent.GetSizeTuple()
        self.gauge = wx.Gauge(self, style=wx.GA_HORIZONTAL,
                              size=(width, height/10))
        rect = self.GetFieldRect(0)
        self.gauge.SetPosition((rect.x , rect.y ))
        if self.timeout is not None:
            self.gauge.SetRange(int(self.timeout))
        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self._on_time, self.timer)
        self.timer.Start(1)
        self.pos = 0

    def _on_time(self, evt):
        """
        Update the progress bar while the timer is running

        :param evt: wx.EVT_TIMER

        """
        # Check stop flag that can be set from non main thread
        if self.timeout is None and self.timer.IsRunning():
            self.gauge.Pulse()


if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = wx.Frame(None, wx.ID_ANY, 'test frame')
    #statusBar = StatusBar(frame, wx.ID_ANY)
    statusBar = SPageStatusbar(frame)
    frame.SetStatusBar(statusBar)
    frame.Show(True)
    #event = MessageEvent()
    #event.type = "progress"
    #event.status  = "statusbar...."
    #event.info = "error"
    #statusBar.set_status(event=event)
    app.MainLoop()


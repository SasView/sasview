import wx

class FrameSelectDialog(wx.Dialog):

    def __init__(self, n_frames):
        wx.Dialog.__init__(self, None, title="Select Frames")

        sizer = wx.GridBagSizer(10, 10)

        y = 0
        instructions = ("The file you've selected has {} frames. "
            "Please select a subset of frames to convert to CanSAS "
            "format").format(n_frames)
        instructions_label = wx.StaticText(self, -1, instructions)
        instructions_label.Wrap(self.GetSize().width - 20)
        sizer.Add(instructions_label, (y,0), (1,2), wx.ALL, 5)
        y += 1

        first_label = wx.StaticText(self, -1, "First Frame (0-{}): ".format(n_frames-1))
        sizer.Add(first_label, (y,0), (1,1), wx.ALL, 5)

        self.first_input = wx.TextCtrl(self, -1)
        sizer.Add(self.first_input, (y,1), (1,1))
        y += 1

        last_label = wx.StaticText(self, -1, "Last Frame (0-{}): ".format(n_frames-1))
        sizer.Add(last_label, (y,0), (1,1), wx.ALL, 5)

        self.last_input = wx.TextCtrl(self, -1)
        sizer.Add(self.last_input, (y,1), (1,1))
        y += 1

        increment_label = wx.StaticText(self, -1, "Increment: ")
        sizer.Add(increment_label, (y,0), (1,1), wx.ALL, 5)

        self.increment_input = wx.TextCtrl(self, -1)
        sizer.Add(self.increment_input, (y,1), (1,1))
        y += 1

        done_btn = wx.Button(self, wx.ID_OK)
        sizer.Add(done_btn, (y,0), (1,1), wx.LEFT | wx.TOP | wx.BOTTOM, 15)

        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        sizer.Add(cancel_btn, (y,1), (1,1), wx.ALL, 15)

        self.SetSizer(sizer)

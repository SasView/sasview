'''
Created on Feb 18, 2015

@author: jkrzywon
'''

__id__ = "$Id: acknoweldgebox.py 2015-18-02 jkrzywon $"
__revision__ = "$Revision: 1193 $"

import wx
import wx.richtext
import wx.lib.hyperlink
import random
import os.path
import os
try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
      (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
        fObj, path, descr = imp.find_module('local_config', [path])
        config = imp.load_module('local_config', fObj, path, descr)
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default
    import config


class GpuOptions(wx.Dialog):
    """
    "Acknowledgement" Dialog Box

    Shows the current method for acknowledging SasView in
    scholarly publications.

    """

    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        try:
            from sasmodels.kernelcl import environment
            env = environment()
            clinfo = [ctx.devices[0].name
                    for ctx in env.context]
            clinfo.append("No OpenCL")
        except ImportError:
            clinfo = None

        #####################################
        self.panel1 = wx.Panel(self, -1)
        static_box1 = wx.StaticBox(self.panel1, -1, "OpenCL Options")

        #contextes = ("Intel(R) Iris(TM) Graphics 6100",
        #             "Intel(R) Core(TM) i7-5557U CPU @ 3.10GHz",
        #             "No OpenCL")
        rows = len(clinfo)

        flexsizer = wx.FlexGridSizer(rows, 1, hgap=20, vgap=10)
        self.fitter_button = {}
        for fitter in clinfo:
            button = wx.RadioButton(self.panel1, -1,
                    label=fitter, name=fitter)
            self.fitter_button[fitter] = button
            #self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, id=button.GetId())
            flexsizer.Add(button, 0, 0)

        fit_hsizer = wx.StaticBoxSizer(static_box1, orient=wx.VERTICAL)
        fit_hsizer.Add(flexsizer, 0, wx.ALL, 5)

        self.panel1.SetSizer(fit_hsizer)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.panel1, 0, wx.ALL, 10)
        ###########################################
        #self.preamble = wx.StaticText(self, -1, config._acknowledgement_preamble)
        #items = [config._acknowledgement_preamble_bullet1,
        #         config._acknowledgement_preamble_bullet2,
        #         config._acknowledgement_preamble_bullet3,
        #         config._acknowledgement_preamble_bullet4]
        #self.list1 = wx.StaticText(self, -1, "\t(1) " + items[0])
        #self.list2 = wx.StaticText(self, -1, "\t(2) " + items[1])
        #self.list3 = wx.StaticText(self, -1, "\t(3) " + items[2])
        #self.list4 = wx.StaticText(self, -1, "\t(4) " + items[3])
        #self.static_line = wx.StaticLine(self, 0)
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        """
        :TODO - add method documentation
        """
        # begin wxGlade: DialogAbout.__set_properties
        #self.preamble.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        #self.preamble.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.SetTitle("Fitting on GPU Options")
        #Increased size of box from (525, 225), SMK, 04/10/16
        self.SetSize((400, 150))
        # end wxGlade

    def __do_layout(self):
        """
        :TODO - add method documentation
        """
        # begin wxGlade: DialogAbout.__do_layout
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        #sizer_titles = wx.BoxSizer(wx.VERTICAL)
        #sizer_titles.Add(self.preamble, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_titles.Add(self.list1, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_titles.Add(self.list2, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_titles.Add(self.list3, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_titles.Add(self.list4, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_titles.Add(self.static_line, 0, wx.ALL|wx.EXPAND, 0)
        #sizer_titles.Add(self.ack, 0, wx.ALL|wx.EXPAND, 5)
        #sizer_main.Add(sizer_titles, -1, wx.ALL|wx.EXPAND, 5)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade


##### testing code ############################################################
class MyApp(wx.App):
    """
    Class for running module as stand alone for testing
    """
    def OnInit(self):
        """
        Defines an init when running as standalone
        """
        wx.InitAllImageHandlers()
        dialog = GpuOptions(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.ShowModal()
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()

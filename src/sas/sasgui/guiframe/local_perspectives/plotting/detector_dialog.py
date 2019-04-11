"""
    Widget to display a 2D map of the detector
"""
import wx
import sys
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.events import StatusEvent
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
import matplotlib as mpl
from matplotlib import pylab
# FONT size
if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
else:
    FONT_VARIANT = 1

DEFAULT_CMAP = pylab.cm.get_cmap('jet')

class DetectorDialog(wx.Dialog):
    """
    Dialog box to let the user edit detector settings
    """

    def __init__(self, parent, id=1, base=None, dpi=None,
                 cmap=DEFAULT_CMAP, reset_zmin_ctl=None,
                 reset_zmax_ctl=None, *args, **kwds):
        """
        """
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, parent, id=1, *args, **kwds)
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.parent = base
        self.dpi = dpi
        self.cmap = cmap
        self.reset_zmin_ctl = reset_zmin_ctl
        self.reset_zmax_ctl = reset_zmax_ctl
        self.label_xnpts = wx.StaticText(self, -1, "Detector width in pixels")
        self.label_ynpts = wx.StaticText(self, -1, "Detector Height in pixels")
        self.label_qmax = wx.StaticText(self, -1, "Q max")
        self.label_zmin = wx.StaticText(self, -1,
                                        "Min amplitude for color map (optional)")
        self.label_zmax = wx.StaticText(self, -1,
                                        "Max amplitude for color map (optional)")
        self.label_beam = wx.StaticText(self, -1,
                                        "Beam stop radius in units of q")
        self.xnpts_ctl = wx.StaticText(self, -1, "")
        self.ynpts_ctl = wx.StaticText(self, -1, "")
        self.qmax_ctl = wx.StaticText(self, -1, "")
        self.beam_ctl = wx.StaticText(self, -1, "")
        self.zmin_ctl = wx.TextCtrl(self, -1, size=(60, 20))
        self.zmin_ctl.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.zmax_ctl = wx.TextCtrl(self, -1, size=(60, 20))
        self.zmax_ctl.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.static_line_3 = wx.StaticLine(self, -1)
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.button_reset = wx.Button(self, wx.NewId(), "Reset")
        self.Bind(wx.EVT_BUTTON, self.resetValues, self.button_reset)
        self.button_ok = wx.Button(self, wx.ID_OK, "OK")
        self.Bind(wx.EVT_BUTTON, self.checkValues, self.button_ok)
        self.__set_properties()
        self.__do_layout()
        self.Fit()

    class Event(object):
        """
        """
        xnpts = 0
        ynpts = 0
        qpax = 0
        beam = 0
        zmin = 0
        zmax = 0
        cmap = None
        sym4 = False

    def onSetFocus(self, event):
        """
        Highlight the txtcrtl
        """
        # Get a handle to the TextCtrl
        widget = event.GetEventObject()
        # Select the whole control, after this event resolves
        wx.CallAfter(widget.SetSelection, -1, -1)

    def resetValues(self, event):
        """
        reset detector info
        """
        try:
            zmin = self.reset_zmin_ctl
            zmax = self.reset_zmax_ctl
            if zmin is None:
                zmin = ""
            if zmax is None:
                zmax = ""
            self.zmin_ctl.SetValue(str(zmin))
            self.zmax_ctl.SetValue(str(zmax))
            self.cmap = DEFAULT_CMAP
            self.cmap_selector.SetStringSelection("jet")
            self._on_select_cmap(event=None)
        except Exception as exc:
            msg = "error occurs while resetting Detector: %s" % exc
            wx.PostEvent(self.parent, StatusEvent(status=msg))

    def checkValues(self, event):
        """
        Check the valitidity of zmin and zmax value
        zmax should be a float and zmin less than zmax
        """
        flag = True
        try:
            value = self.zmin_ctl.GetValue()
            self.zmin_ctl.SetBackgroundColour(wx.WHITE)
            self.zmin_ctl.Refresh()
        except:
            flag = False
            wx.PostEvent(self.parent, StatusEvent(status="Enter float value"))
            self.zmin_ctl.SetBackgroundColour("pink")
            self.zmin_ctl.Refresh()
        try:
            value = self.zmax_ctl.GetValue()
            if value and float(value) == 0.0:
                flag = False
                wx.PostEvent(self.parent,
                             StatusEvent(status="Enter number greater than zero"))
                self.zmax_ctl.SetBackgroundColour("pink")
                self.zmax_ctl.Refresh()
            else:
                self.zmax_ctl.SetBackgroundColour(wx.WHITE)
                self.zmax_ctl.Refresh()
        except:
            flag = False
            wx.PostEvent(self.parent, StatusEvent(status="Enter Integer value"))
            self.zmax_ctl.SetBackgroundColour("pink")
            self.zmax_ctl.Refresh()
        if flag:
            event.Skip(True)

    def setContent(self, xnpts, ynpts, qmax, beam,
                   zmin=None, zmax=None, sym=False):
        """
        received value and displayed them

        :param xnpts: the number of point of the x_bins of data
        :param ynpts: the number of point of the y_bins of data
        :param qmax: the maxmimum value of data pixel
        :param beam: the radius of the beam
        :param zmin:  the value to get the minimum color
        :param zmax:  the value to get the maximum color
        :param sym:

        """
        self.xnpts_ctl.SetLabel(str(format_number(xnpts)))
        self.ynpts_ctl.SetLabel(str(format_number(ynpts)))
        self.qmax_ctl.SetLabel(str(format_number(qmax)))
        self.beam_ctl.SetLabel(str(format_number(beam)))
        if zmin is not None:
            self.zmin_ctl.SetValue(str(format_number(zmin)))
        if zmax is not None:
            self.zmax_ctl.SetValue(str(format_number(zmax)))

    def getContent(self):
        """
        return event containing value to reset the detector of a given data
        """
        event = self.Event()
        t_min = self.zmin_ctl.GetValue()
        t_max = self.zmax_ctl.GetValue()
        v_min = None
        v_max = None
        if len(t_min.lstrip()) > 0:
            try:
                v_min = float(t_min)
            except:
                v_min = None
        if len(t_max.lstrip()) > 0:
            try:
                v_max = float(t_max)
            except:
                v_max = None
        event.zmin = v_min
        event.zmax = v_max
        event.cmap = self.cmap
        return event

    def __set_properties(self):
        """
        set proprieties of the dialog window
        """
        self.SetTitle("2D Color Map")
        self.SetSize((600, 595))

    def __do_layout(self):
        """
        fill the dialog window .
        """
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_params = wx.GridBagSizer(5, 5)
        sizer_colormap = wx.BoxSizer(wx.VERTICAL)
        sizer_selection = wx.BoxSizer(wx.HORIZONTAL)

        iy = 0
        sizer_params.Add(self.label_xnpts, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.xnpts_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_ynpts, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.ynpts_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_qmax, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.qmax_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_beam, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.beam_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_zmin, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.zmin_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        sizer_params.Add(self.label_zmax, (iy, 0), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        sizer_params.Add(self.zmax_ctl, (iy, 1), (1, 1),
                         wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        self.fig = mpl.figure.Figure(dpi=self.dpi, figsize=(4, 1))
        self.ax1 = self.fig.add_axes([0.05, 0.65, 0.9, 0.15])
        self.norm = mpl.colors.Normalize(vmin=0, vmax=100)
        self.cb1 = mpl.colorbar.ColorbarBase(self.ax1, cmap=self.cmap,
                                             norm=self.norm,
                                             orientation='horizontal')
        self.cb1.set_label('Detector Colors')
        self.canvas = Canvas(self, -1, self.fig)
        sizer_colormap.Add(self.canvas, 0, wx.LEFT | wx.EXPAND, 5)
        self.cmap_selector = wx.ComboBox(self, -1)
        self.cmap_selector.SetValue(str(self.cmap.name))
        maps = sorted(m for m in pylab.cm.datad if not m.endswith("_r"))

        for i, m in enumerate(maps):
            self.cmap_selector.Append(str(m), pylab.get_cmap(m))

        wx.EVT_COMBOBOX(self.cmap_selector, -1, self._on_select_cmap)
        sizer_selection.Add(wx.StaticText(self, -1, "Select Cmap: "), 0,
                            wx.LEFT | wx.ADJUST_MINSIZE, 5)
        sizer_selection.Add(self.cmap_selector, 0, wx.EXPAND | wx.ALL, 10)
        sizer_main.Add(sizer_params, 0, wx.EXPAND | wx.ALL, 5)
        sizer_main.Add(sizer_selection, 0, wx.EXPAND | wx.ALL, 5)
        note = "   Note: This is one time option. " + \
               "It will be reset on updating the image."
        note_txt = wx.StaticText(self, -1, note)
        sizer_main.Add(note_txt, 0, wx.EXPAND | wx.ALL, 5)
        sizer_main.Add(sizer_colormap, 1, wx.EXPAND | wx.ALL, 5)
        sizer_main.Add(self.static_line_3, 0, wx.EXPAND, 0)
        sizer_button.Add(self.button_reset, 0, wx.LEFT | wx.ADJUST_MINSIZE, 100)
        sizer_button.Add(self.button_ok, 0, wx.LEFT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.button_cancel, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        sizer_main.Add(sizer_button, 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 10)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade

    def _on_select_cmap(self, event):
        """
        display a new cmap
        """
        cmap_name = self.cmap_selector.GetCurrentSelection()
        current_cmap = self.cmap_selector.GetClientData(cmap_name)
        self.cmap = current_cmap
        self.cb1 = mpl.colorbar.ColorbarBase(self.ax1, cmap=self.cmap,
                                             norm=self.norm, orientation='horizontal')
        self.canvas.draw()

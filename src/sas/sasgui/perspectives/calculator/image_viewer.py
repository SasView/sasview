

import os
import sys
import wx
import numpy as np
import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from sas.sasgui.guiframe.local_perspectives.plotting.SimplePlot import PlotFrame
#import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as colors
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.perspectives.calculator.calculator_widgets import InputTextCtrl
from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.manipulations import reader2D_converter
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

_BOX_WIDTH = 60
IS_WIN = True
if sys.platform.count("win32") > 0:
    _DIALOG_WIDTH = 400
else:
    _DIALOG_WIDTH = 480
    IS_WIN = False

class ImageView:
    """
    Open a file dialog to allow the user to select a given file.
    Display the loaded data if available.
    """
    def __init__(self, parent=None):
        """
        Init
        """
        self.parent = parent

    def load(self):
        """
        load image files
        """
        parent = self.parent
        if parent is None:
            location = os.getcwd()
        else:
            location = parent._default_save_location
        path_list = self.choose_data_file(location=location)
        if path_list is None:
            return
        if len(path_list) >= 0 and path_list[0] is not None:
            if parent is not None:
                parent._default_save_location = os.path.dirname(path_list[0])
        err_msg = ''
        for file_path in path_list:
            basename = os.path.basename(file_path)
            _, extension = os.path.splitext(basename)
            try:
                # Note that matplotlib only reads png natively.
                # Any other formats (tiff, jpeg, etc) are passed
                # to PIL which seems to have a problem in version
                # 1.1.7 that causes a close error which shows up in 
                # the log file.  This does not seem to have any adverse
                # effects.  PDB   --- September 17, 2017.
                img = mpimg.imread(file_path)
                is_png = extension.lower() == '.png'
                plot_frame = ImageFrame(parent, -1, basename, img)
                plot_frame.Show(False)
                ax = plot_frame.plotpanel
                if not is_png:
                    ax.subplot.set_ylim(ax.subplot.get_ylim()[::-1])
                ax.subplot.set_xlabel('x [pixel]')
                ax.subplot.set_ylabel('y [pixel]')
                ax.figure.subplots_adjust(left=0.15, bottom=0.1,
                                          right=0.95, top=0.95)
                plot_frame.SetTitle('Picture -- %s --' % basename)
                plot_frame.Show(True)
                if parent is not None:
                    parent.put_icon(plot_frame)
            except:
                err_msg += "Failed to load '%s'.\n" % basename
        if err_msg:
            if parent is not None:
                wx.PostEvent(parent, StatusEvent(status=err_msg, info="error"))
            else:
                print(err_msg)

    def choose_data_file(self, location=None):
        """
        Open a file dialog to allow loading a file
        """
        path = None
        if location is None:
            location = os.getcwd()
        wildcard="Images (*.bmp;*.gif;*jpeg,*jpg;*.png;*tif;*.tiff)|*bmp;\
            *.gif; *.jpg; *.jpeg;*png;*.png;*.tif;*.tiff|"\
            "Bitmap (*.bmp)|*.bmp|"\
            "GIF (*.gif)|*.gif|"\
            "JPEG (*.jpg;*.jpeg)|*.jpg;*.jpeg|"\
            "PNG (*.png)|*.png|"\
            "TIFF (*.tif;*.tiff)|*.tif;*tiff|"\
            "All Files (*.*)|*.*|"

        dlg = wx.FileDialog(self.parent, "Image Viewer: Choose an image file",
                            location, "", wildcard, style=wx.FD_OPEN
                            | wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPaths()
        else:
            return None
        dlg.Destroy()
        return path

class ImageFrame(PlotFrame):
    """
    Frame for simple plot
    """
    def __init__(self, parent, id, title, image=None, scale='log_{10}',
                 size=wx.Size(550, 470)):
        """
        comment
        :Param data: image array got from imread() of matplotlib [narray]
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        PlotFrame.__init__(self, parent, id, title, scale, size,
            show_menu_icons=False)
        self.parent = parent
        self.data = image
        self.file_name = title

        menu = wx.Menu()
        id = wx.NewId()
        item = wx.MenuItem(menu, id, "&Convert to Data")
        menu.AppendItem(item)
        wx.EVT_MENU(self, id, self.on_set_data)
        self.menu_bar.Append(menu, "&Image")

        menu_help = wx.Menu()
        id = wx.NewId()
        item = wx.MenuItem(menu_help, id, "&HowTo")
        menu_help.AppendItem(item)
        wx.EVT_MENU(self, id, self.on_help)
        self.menu_bar.Append(menu_help, "&Help")

        self.SetMenuBar(self.menu_bar)
        self.im_show(image)

    def on_set_data(self, event):
        """
        Rescale the x y range, make 2D data and send it to data explore
        """
        title = self.file_name
        self.panel = SetDialog(parent=self, title=title, image=self.data)
        self.panel.ShowModal()

    def on_help(self, event):
        """
        Bring up Image Viewer Documentation from the image viewer window
        whenever the help menu item "how to" is clicked. Calls
        DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".

        :param evt: Triggers on clicking "how to" in help menu
        """

        _TreeLocation = "user/sasgui/perspectives/calculator/"
        _TreeLocation += "image_viewer_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Image Viewer Help")


class SetDialog(wx.Dialog):
    """
    Dialog for Data Set
    """
    def __init__(self, parent, id= -1, title="Convert to Data", image=None,
                 size=(_DIALOG_WIDTH, 270)):
        wx.Dialog.__init__(self, parent, id, title, size)
        # parent
        self.parent = parent
        self.base = parent.parent
        self.title = title
        self.image = np.array(image)
        self.z_ctrl = None
        self.xy_ctrls = []
        self.is_png = self._get_is_png()
        self._build_layout()
        my_title = "Convert Image to Data - %s -" % self.title
        self.SetTitle(my_title)
        self.SetSize(size)

    def _get_is_png(self):
        """
        Get if the image file is png
        """
        _, extension = os.path.splitext(self.title)
        return extension.lower() == '.png'

    def _build_layout(self):
        """
        Layout
        """
        vbox = wx.BoxSizer(wx.VERTICAL)
        zbox = wx.BoxSizer(wx.HORIZONTAL)
        xbox = wx.BoxSizer(wx.HORIZONTAL)
        ybox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox = wx.BoxSizer(wx.VERTICAL)

        sb_title = wx.StaticBox(self, -1, 'Transform Axes')
        boxsizer = wx.StaticBoxSizer(sb_title, wx.VERTICAL)
        z_title = wx.StaticText(self, -1, 'z values (range: 0 - 255) to:')
        ztime_title = wx.StaticText(self, -1, 'z *')
        x_title = wx.StaticText(self, -1, 'x values from pixel # to:')
        xmin_title = wx.StaticText(self, -1, 'xmin:')
        xmax_title = wx.StaticText(self, -1, 'xmax:')
        y_title = wx.StaticText(self, -1, 'y values from pixel # to:')
        ymin_title = wx.StaticText(self, -1, 'ymin: ')
        ymax_title = wx.StaticText(self, -1, 'ymax:')
        z_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH , 20),
                                style=wx.TE_PROCESS_ENTER)

        xmin_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
        xmax_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
        ymin_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
        ymax_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
        z_ctl.SetValue('1.0')
        xmin_ctl.SetValue('-0.3')
        xmax_ctl.SetValue('0.3')
        ymin_ctl.SetValue('-0.3')
        ymax_ctl.SetValue('0.3')
        z_ctl.Bind(wx.EVT_TEXT, self._on_z_enter)
        xmin_ctl.Bind(wx.EVT_TEXT, self._onparam)
        xmax_ctl.Bind(wx.EVT_TEXT, self._onparam)
        ymin_ctl.Bind(wx.EVT_TEXT, self._onparam)
        ymax_ctl.Bind(wx.EVT_TEXT, self._onparam)
        xbox.AddMany([(x_title , 0, wx.LEFT, 0),
                      (xmin_title , 0, wx.LEFT, 10),
                      (xmin_ctl , 0, wx.LEFT, 10),
                      (xmax_title , 0, wx.LEFT, 10),
                      (xmax_ctl , 0, wx.LEFT, 10)])
        ybox.AddMany([(y_title , 0, wx.LEFT, 0),
                      (ymin_title , 0, wx.LEFT, 10),
                      (ymin_ctl , 0, wx.LEFT, 10),
                      (ymax_title , 0, wx.LEFT, 10),
                      (ymax_ctl , 0, wx.LEFT, 10)])
        zbox.AddMany([(z_title , 0, wx.LEFT, 0),
                      (ztime_title, 0, wx.LEFT, 10),
                      (z_ctl , 0, wx.LEFT, 7),
                      ])
        msg = "The data rescaled will show up in the Data Explorer. \n"
        msg += "*Note: Recommend to use an image with 8 bit Grey \n"
        msg += "  scale (and with No. of pixels < 300 x 300).\n"
        msg += "  Otherwise, z = 0.299R + 0.587G + 0.114B."
        note_txt = wx.StaticText(self, -1, msg)
        note_txt.SetForegroundColour("black")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, -1, 'OK')
        okButton.Bind(wx.EVT_BUTTON, self.on_set)
        cancelButton = wx.Button(self, -1, 'Cancel')
        cancelButton.Bind(wx.EVT_BUTTON, self.OnClose)
        btnbox.Add(okButton, 0, wx.LEFT | wx.BOTTOM, 5)
        btnbox.Add(cancelButton, 0, wx.LEFT | wx.TOP, 5)
        hbox.Add(note_txt, 0, wx.LEFT, 5)
        hbox.Add(btnbox, 0, wx.LEFT, 15)
        vbox.Add((10, 15))
        boxsizer.Add(xbox, 1, wx.LEFT | wx.BOTTOM, 5)
        boxsizer.Add(ybox, 1, wx.LEFT | wx.BOTTOM, 5)
        boxsizer.Add(zbox, 1, wx.LEFT | wx.BOTTOM, 5)
        vbox.Add(boxsizer, 0, wx.LEFT, 20)
        vbox.Add(hbox, 0, wx.LEFT | wx.TOP, 15)
        okButton.SetFocus()
        # set sizer
        self.SetSizer(vbox)
        #pos = self.parent.GetPosition()
        #self.SetPosition(pos)
        self.z_ctrl = z_ctl
        self.xy_ctrls = [[xmin_ctl, xmax_ctl], [ymin_ctl, ymax_ctl]]

    def _onparamEnter(self, event=None):
        """
        By pass original txtcrl binding
        """
        pass

    def _onparam(self, event=None):
        """
        Set to default
        """
        item = event.GetEventObject()
        self._check_ctrls(item)

    def _check_ctrls(self, item, is_button=False):
        """
        """
        flag = True
        item.SetBackgroundColour("white")
        try:
            val = float(item.GetValue())
            if val < -10.0 or val > 10.0:
                item.SetBackgroundColour("pink")
                item.Refresh()
                flag = False
        except:
            item.SetBackgroundColour("pink")
            item.Refresh()
            flag = False
        if not flag and is_button:
            err_msg = "The allowed range of the min and max values are \n"
            err_msg += "between -10 and 10."
            if self.base is not None:
                wx.PostEvent(self.base, StatusEvent(status=err_msg,
                                                    info="error"))
            else:
                print(err_msg)
        return flag

    def _on_z_enter(self, event=None):
        """
        On z factor enter
        """
        item = event.GetEventObject()
        self._check_z_ctrl(item)

    def _check_z_ctrl(self, item, is_button=False):
        """
        """
        flag = True
        item.SetBackgroundColour("white")
        try:
            val = float(item.GetValue())
            if val <= 0:
                item.SetBackgroundColour("pink")
                item.Refresh()
                flag = False
        except:
            item.SetBackgroundColour("pink")
            item.Refresh()
            flag = False
        if not flag and is_button:
            err_msg = "The z scale value should be larger than 0."
            if self.base is not None:
                wx.PostEvent(self.base, StatusEvent(status=err_msg,
                                                    info="error"))
            else:
                print(err_msg)
        return flag

    def on_set(self, event):
        """
        Set image as data
        """
        event.Skip()
        # Check the textctrl values
        for item_list in self.xy_ctrls:
            for item in item_list:
                 if not self._check_ctrls(item, True):
                     return
        if not self._check_z_ctrl(self.z_ctrl, True):
            return
        try:
            image = self.image
            xmin = float(self.xy_ctrls[0][0].GetValue())
            xmax = float(self.xy_ctrls[0][1].GetValue())
            ymin = float(self.xy_ctrls[1][0].GetValue())
            ymax = float(self.xy_ctrls[1][1].GetValue())
            zscale = float(self.z_ctrl.GetValue())
            self.convert_image(image, xmin, xmax, ymin, ymax, zscale)
        except:
            err_msg = "Error occurred while converting Image to Data."
            if self.base is not None:
                wx.PostEvent(self.base, StatusEvent(status=err_msg,
                                                    info="error"))
            else:
                print(err_msg)

        self.OnClose(event)

    def convert_image(self, rgb, xmin, xmax, ymin, ymax, zscale):
        """
        Convert image to data2D
        """
        x_len = len(rgb[0])
        y_len = len(rgb)
        x_vals = np.linspace(xmin, xmax, num=x_len)
        y_vals = np.linspace(ymin, ymax, num=y_len)
        # Instantiate data object
        output = Data2D()
        output.filename = os.path.basename(self.title)
        output.id = output.filename
        detector = Detector()
        detector.pixel_size.x = None
        detector.pixel_size.y = None
        # Store the sample to detector distance
        detector.distance = None
        output.detector.append(detector)
        # Initiazed the output data object
        output.data = zscale * self.rgb2gray(rgb)
        output.err_data = np.zeros([x_len, y_len])
        output.mask = np.ones([x_len, y_len], dtype=bool)
        output.xbins = x_len
        output.ybins = y_len
        output.x_bins = x_vals
        output.y_bins = y_vals
        output.qx_data = np.array(x_vals)
        output.qy_data = np.array(y_vals)
        output.xmin = xmin
        output.xmax = xmax
        output.ymin = ymin
        output.ymax = ymax
        output.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
        output.yaxis('\\rm{Q_{y}}', '\AA^{-1}')
        # Store loading process information
        output.meta_data['loader'] = self.title.split('.')[-1] + "Reader"
        output.is_data = True
        output = reader2D_converter(output)
        if self.base is not None:
            data = self.base.create_gui_data(output, self.title)
            self.base.add_data({data.id:data})

    def rgb2gray(self, rgb):
        """
        RGB to Grey
        """
        if self.is_png:
            # png image limits: 0 to 1, others 0 to 255
            #factor = 255.0
            rgb = rgb[::-1]
        if rgb.ndim == 2:
            grey = np.rollaxis(rgb, axis=0)
        else:
            red, green, blue = np.rollaxis(rgb[..., :3], axis= -1)
            grey = 0.299 * red + 0.587 * green + 0.114 * blue
        max_i = rgb.max()
        factor = 255.0 / max_i
        grey *= factor
        return np.array(grey)

    def OnClose(self, event):
        """
        Close event
        """
        # clear event
        event.Skip()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    ImageView(None).load()
    app.MainLoop()

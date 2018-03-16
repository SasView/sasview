# pylint: disable=attribute-defined-outside-init
"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation.

See the license text in license.txt

copyright 2008, 2009, 2010 University of Tennessee
"""
import wx
import sys
import os
import matplotlib
import math
import logging
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar
from matplotlib.backend_bases import FigureManagerBase
# Wx-Pylab magic for displaying plots within an application's window.
from matplotlib import _pylab_helpers
# The Figure object is used to create backend-independent plot representations.
from matplotlib.figure import Figure

#from sas.guicomm.events import StatusEvent
from sas.sascalc.calculator.resolution_calculator import ResolutionCalculator
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.perspectives.calculator.calculator_widgets import OutputTextCtrl
from sas.sasgui.perspectives.calculator.calculator_widgets import InputTextCtrl
from wx.lib.scrolledpanel import ScrolledPanel
from math import fabs
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

logger = logging.getLogger(__name__)

_BOX_WIDTH = 100
_Q_DEFAULT = 0.0
#Slit length panel size
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    PANEL_WIDTH = 525
    PANEL_HEIGHT = 653
    FONT_VARIANT = 0
    IS_WIN = True
else:
    PANEL_TOP = 60
    PANEL_WIDTH = 540
    PANEL_HEIGHT = 662
    FONT_VARIANT = 1
    IS_WIN = False

_SOURCE_MASS = {'Alpha':6.64465620E-24,
                'Deuteron':3.34358320E-24,
                'Neutron':1.67492729E-24,
                'Photon': 0.0,
                'Proton':1.67262137E-24,
                'Triton':5.00826667E-24}

class ResolutionCalculatorPanel(ScrolledPanel):
    """
    Provides the Resolution calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Q Resolution Estimator"
    ## Name to appear on the window title bar
    window_caption = ""
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

    def __init__(self, parent, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH * 2, PANEL_HEIGHT)
        kwds["style"] = wx.FULL_REPAINT_ON_RESIZE
        ScrolledPanel.__init__(self, parent, *args, **kwds)
        self.SetupScrolling()
        self.parent = parent

        # input defaults
        self.qx = []
        self.qy = []
        # dQ defaults
        self.sigma_r = None
        self.sigma_phi = None
        self.sigma_1d = None
        # monchromatic or polychromatic
        self.wave_color = 'mono'
        self.num_wave = 10
        self.spectrum_dic = {}
        # dQ 2d image
        self.image = None
        # results of sigmas
        self.sigma_strings = ' '
        #Font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        # Object that receive status event
        self.resolution = ResolutionCalculator()
        # Source selection dic
        self.source_mass = _SOURCE_MASS
        #layout attribute
        self.hint_sizer = None
        # detector coordinate of estimation of sigmas
        self.det_coordinate = 'cartesian'
        self.source_cb = None
        self._do_layout()

    def _define_structure(self):
        """
        Define the main sizers building to build this application.
        """
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vertical_l_sizer = wx.BoxSizer(wx.VERTICAL)
        self.vertical_r_spacer = wx.BoxSizer(wx.VERTICAL)
        self.vertical_r_frame = wx.StaticBox(self, -1, '')
        self.vertical_r_sizer = wx.StaticBoxSizer(self.vertical_r_frame,
                                                  wx.VERTICAL)
        self.box_source = wx.StaticBox(self, -1, str(self.window_caption))
        self.boxsizer_source = wx.StaticBoxSizer(self.box_source, wx.VERTICAL)
        self.mass_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.intensity_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wavelength_spread_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.source_aperture_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample_aperture_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.source2sample_distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample2sample_distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample2detector_distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detector_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detector_pix_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.input_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_sizer = wx.BoxSizer(wx.VERTICAL)
        self.hint_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_mass(self):
        """
        Fill the sizer containing mass
        """
        # get the mass
        mass_value = str(self.resolution.mass)
        self.mass_txt = wx.StaticText(self, -1, 'Source: ')
        self.mass_hint = "Mass of Neutrons m = %s [g]" % str(self.resolution.mass)
        self.source_cb = wx.ComboBox(self, -1,
                                     style=wx.CB_READONLY,
                                     name='%s' % mass_value)
        # Sort source name because wx2.9 on Mac does not support CB_SORT
        # Custom sorting
        source_list = []
        for key, _ in self.source_mass.items():
            name_source = str(key)
            source_list.append(name_source)
        source_list.sort()
        for idx in range(len(source_list)):
            self.source_cb.Append(source_list[idx], idx)
        self.source_cb.SetStringSelection("Neutron")
        wx.EVT_COMBOBOX(self.source_cb, -1, self._on_source_selection)

        # combo box for color
        self.wave_color_cb = wx.ComboBox(self, -1,
                                         style=wx.CB_READONLY,
                                         name='color')
        # two choices
        self.wave_color_cb.Append('Monochromatic')
        self.wave_color_cb.Append('TOF')
        self.wave_color_cb.SetStringSelection("Monochromatic")
        wx.EVT_COMBOBOX(self.wave_color_cb, -1, self._on_source_color)

        source_hint = "Source Selection: Affect on"
        source_hint += " the gravitational contribution.\n"
        source_hint += "Mass of %s: m = %s [g]" % \
                            ('Neutron', str(self.resolution.mass))
        self.mass_txt.SetToolTipString(source_hint)
        self.mass_sizer.AddMany([(self.mass_txt, 0, wx.LEFT, 15),
                                 (self.source_cb, 0, wx.LEFT, 15),
                                 (self.wave_color_cb, 0, wx.LEFT, 15)])

    def _layout_intensity(self):
        """
        Fill the sizer containing intensity
        """
        # get the intensity
        intensity_value = str(self.resolution.intensity)
        intensity_unit_txt = wx.StaticText(self, -1, '[counts/s]')
        intensity_txt = wx.StaticText(self, -1, 'Intensity: ')
        self.intensity_tcl = InputTextCtrl(self, -1,
                                           size=(_BOX_WIDTH, -1))
        intensity_hint = "Intensity of Neutrons"
        self.intensity_tcl.SetValue(intensity_value)
        self.intensity_tcl.SetToolTipString(intensity_hint)
        self.intensity_sizer.AddMany([(intensity_txt, 0, wx.LEFT, 15),
                                      (self.intensity_tcl, 0, wx.LEFT, 15),
                                      (intensity_unit_txt, 0, wx.LEFT, 10)])


    def _layout_wavelength(self):
        """
        Fill the sizer containing wavelength
        """
        # get the wavelength
        wavelength_value = str(self.resolution.get_wavelength())
        wavelength_unit_txt = wx.StaticText(self, -1, '[A]')
        wavelength_txt = wx.StaticText(self, -1, 'Wavelength: ')
        self.wavelength_tcl = InputTextCtrl(self, -1,
                                            size=(_BOX_WIDTH, -1))
        wavelength_hint = "Wavelength of Neutrons"
        self.wavelength_tcl.SetValue(wavelength_value)
        self.wavelength_tcl.SetToolTipString(wavelength_hint)

        # get the spectrum
        spectrum_value = self.resolution.get_default_spectrum()
        self.spectrum_dic['Add new'] = ''
        self.spectrum_dic['Flat'] = spectrum_value

        self.spectrum_txt = wx.StaticText(self, -1, 'Spectrum: ')
        self.spectrum_cb = wx.ComboBox(self, -1,
                                       style=wx.CB_READONLY,
                                       size=(_BOX_WIDTH, -1),
                                       name='spectrum')
        self.spectrum_cb.Append('Add new')
        self.spectrum_cb.Append('Flat')
        wx.EVT_COMBOBOX(self.spectrum_cb, -1, self._on_spectrum_cb)
        spectrum_hint = "Wavelength Spectrum: Intensity vs. wavelength"
        self.spectrum_cb.SetStringSelection('Flat')
        self.spectrum_cb.SetToolTipString(spectrum_hint)
        self.wavelength_sizer.AddMany([(wavelength_txt, 0, wx.LEFT, 15),
                                       (self.wavelength_tcl, 0, wx.LEFT, 5),
                                       (wavelength_unit_txt, 0, wx.LEFT, 5),
                                       (self.spectrum_txt, 0, wx.LEFT, 20),
                                       (self.spectrum_cb, 0, wx.LEFT, 5)])
        self.spectrum_txt.Show(False)
        self.spectrum_cb.Show(False)

    def _layout_wavelength_spread(self):
        """
        Fill the sizer containing wavelength
        """
        # get the wavelength
        wavelength_spread_value = str(self.resolution.get_wavelength_spread())
        wavelength_spread_unit_txt = wx.StaticText(self, -1, '')
        wavelength_spread_txt = wx.StaticText(self, -1, 'Wavelength Spread: ')
        self.wavelength_spread_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        wavelength_spread_hint = "Wavelength  Spread of Neutrons"
        self.wavelength_spread_tcl.SetValue(wavelength_spread_value)
        self.wavelength_spread_tcl.SetToolTipString(wavelength_spread_hint)
        self.wavelength_spread_sizer.AddMany([(wavelength_spread_txt, 0,
                                               wx.LEFT, 15),
                                              (self.wavelength_spread_tcl, 0, wx.LEFT, 15),
                                              (wavelength_spread_unit_txt, 0, wx.LEFT, 10)])


    def _layout_source_aperture(self):
        """
        Fill the sizer containing source aperture size
        """
        # get the wavelength
        source_aperture_value = str(self.resolution.source_aperture_size[0])
        if len(self.resolution.source_aperture_size) > 1:
            source_aperture_value += ", "
            source_aperture_value += str(self.resolution.source_aperture_size[1])
        source_aperture_unit_txt = wx.StaticText(self, -1, '[cm]')
        source_aperture_txt = wx.StaticText(self, -1, 'Source Aperture Size: ')
        self.source_aperture_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        source_aperture_hint = "Source Aperture Size"
        self.source_aperture_tcl.SetValue(source_aperture_value)
        self.source_aperture_tcl.SetToolTipString(source_aperture_hint)
        self.source_aperture_sizer.AddMany([(source_aperture_txt, 0, wx.LEFT, 15),
                                            (self.source_aperture_tcl, 0, wx.LEFT, 15),
                                            (source_aperture_unit_txt, 0, wx.LEFT, 10)])

    def _layout_sample_aperture(self):
        """
        Fill the sizer containing sample aperture size
        """
        # get the wavelength
        sample_aperture_value = str(self.resolution.sample_aperture_size[0])
        if len(self.resolution.sample_aperture_size) > 1:
            sample_aperture_value += ", "
            sample_aperture_value += str(self.resolution.sample_aperture_size[1])
        sample_aperture_unit_txt = wx.StaticText(self, -1, '[cm]')
        sample_aperture_txt = wx.StaticText(self, -1, 'Sample Aperture Size: ')
        self.sample_aperture_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        sample_aperture_hint = "Sample Aperture Size"
        self.sample_aperture_tcl.SetValue(sample_aperture_value)
        self.sample_aperture_tcl.SetToolTipString(sample_aperture_hint)
        self.sample_aperture_sizer.AddMany([(sample_aperture_txt, 0, wx.LEFT, 15),
                                            (self.sample_aperture_tcl, 0, wx.LEFT, 15),
                                            (sample_aperture_unit_txt, 0, wx.LEFT, 10)])

    def _layout_source2sample_distance(self):
        """
        Fill the sizer containing souce2sample_distance
        """
        # get the wavelength
        source2sample_distance_value = str(self.resolution.source2sample_distance[0])

        source2sample_distance_unit_txt = wx.StaticText(self, -1, '[cm]')
        source2sample_distance_txt = wx.StaticText(self, -1,
                                                   'Source to Sample Aperture Distance: ')
        self.source2sample_distance_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        source2sample_distance_hint = "Source to Sample Aperture Distance"
        self.source2sample_distance_tcl.SetValue(source2sample_distance_value)
        self.source2sample_distance_tcl.SetToolTipString(source2sample_distance_hint)
        self.source2sample_distance_sizer.AddMany([(source2sample_distance_txt, 0, wx.LEFT, 15),
                                                   (self.source2sample_distance_tcl, 0, wx.LEFT, 15),
                                                   (source2sample_distance_unit_txt, 0, wx.LEFT, 10)])

    def _layout_sample2sample_distance(self):
        """
        Fill the sizer containing sampleslit2sample_distance
        """
        # get the distance
        sample2sample_distance_value = str(self.resolution.sample2sample_distance[0])

        sample2sample_distance_unit_txt = wx.StaticText(self, -1, '[cm]')
        sample2sample_distance_txt = wx.StaticText(self, -1, 'Sample Offset: ')
        self.sample2sample_distance_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        sample2sample_distance_hint = "Sample Aperture to Sample Distance"
        self.sample2sample_distance_tcl.SetValue(sample2sample_distance_value)
        self.sample2sample_distance_tcl.SetToolTipString(sample2sample_distance_hint)
        self.sample2sample_distance_sizer.AddMany([(sample2sample_distance_txt, 0, wx.LEFT, 15),
                                                   (self.sample2sample_distance_tcl, 0, wx.LEFT, 15),
                                                   (sample2sample_distance_unit_txt, 0, wx.LEFT, 10)])

    def _layout_sample2detector_distance(self):
        """
        Fill the sizer containing sample2detector_distance
        """
        # get the wavelength
        sample2detector_distance_value = str(self.resolution.sample2detector_distance[0])

        sample2detector_distance_unit_txt = wx.StaticText(self, -1, '[cm]')
        sample2detector_distance_txt = wx.StaticText(self, -1,
                                                     'Sample Aperture to Detector Distance: ')
        self.sample2detector_distance_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        sample2detector_distance_hint = "Sample Aperture to Detector Distance"
        self.sample2detector_distance_tcl.SetValue(sample2detector_distance_value)
        self.sample2detector_distance_tcl.SetToolTipString(sample2detector_distance_hint)
        self.sample2detector_distance_sizer.AddMany([\
                        (sample2detector_distance_txt, 0, wx.LEFT, 15),
                        (self.sample2detector_distance_tcl, 0, wx.LEFT, 15),
                        (sample2detector_distance_unit_txt, 0, wx.LEFT, 10)])

    def _layout_detector_size(self):
        """
        Fill the sizer containing detector size
        """
        # get the wavelength
        detector_size_value = str(self.resolution.detector_size[0])
        if len(self.resolution.detector_size) > 1:
            detector_size_value += ", "
            detector_size_value += str(self.resolution.detector_size[1])
        detector_size_unit_txt = wx.StaticText(self, -1, '')
        detector_size_txt = wx.StaticText(self, -1, 'Number of Pixels on Detector: ')
        self.detector_size_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        detector_size_hint = "Number of Pixels on Detector"
        self.detector_size_tcl.SetValue(detector_size_value)
        self.detector_size_tcl.SetToolTipString(detector_size_hint)
        self.detector_size_sizer.AddMany([(detector_size_txt, 0, wx.LEFT, 15),
                                          (self.detector_size_tcl, 0, wx.LEFT, 15),
                                          (detector_size_unit_txt, 0, wx.LEFT, 10)])

    def _layout_detector_pix_size(self):
        """
        Fill the sizer containing detector pixel size
        """
        # get the detector_pix_size
        detector_pix_size_value = str(self.resolution.detector_pix_size[0])
        if len(self.resolution.detector_pix_size) > 1:
            detector_pix_size_value += ", "
            detector_pix_size_value += str(self.resolution.detector_pix_size[1])
        detector_pix_size_unit_txt = wx.StaticText(self, -1, '[cm]')
        detector_pix_size_txt = wx.StaticText(self, -1, 'Detector Pixel Size: ')
        self.detector_pix_size_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        detector_pix_size_hint = "Detector Pixel Size"
        self.detector_pix_size_tcl.SetValue(detector_pix_size_value)
        self.detector_pix_size_tcl.SetToolTipString(detector_pix_size_hint)
        self.detector_pix_size_sizer.AddMany([(detector_pix_size_txt, 0, wx.LEFT, 15),
                                              (self.detector_pix_size_tcl, 0, wx.LEFT, 15),
                                              (detector_pix_size_unit_txt, 0, wx.LEFT, 10)])

    def _layout_input(self):
        """
        Fill the sizer containing inputs; qx, qy
        """

        q_title = wx.StaticText(self, -1, "[Q Location of the Estimation]:")
        # sizers for inputs
        inputQx_sizer = wx.BoxSizer(wx.HORIZONTAL)
        inputQy_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # get the default dq
        qx_value = str(_Q_DEFAULT)
        qy_value = str(_Q_DEFAULT)
        qx_unit_txt = wx.StaticText(self, -1, '[1/A]  ')
        qy_unit_txt = wx.StaticText(self, -1, '[1/A]  ')
        qx_name_txt = wx.StaticText(self, -1, 'Qx: ')
        qy_name_txt = wx.StaticText(self, -1, 'Qy: ')
        self.qx_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH * 3, -1))
        self.qy_tcl = InputTextCtrl(self, -1, size=(_BOX_WIDTH * 3, -1))
        qx_hint = "Type the Qx value."
        qy_hint = "Type the Qy value."
        self.qx_tcl.SetValue(qx_value)
        self.qy_tcl.SetValue(qy_value)
        self.qx_tcl.SetToolTipString(qx_hint)
        self.qy_tcl.SetToolTipString(qy_hint)
        inputQx_sizer.AddMany([(qx_name_txt, 0, wx.LEFT, 15),
                               (self.qx_tcl, 0, wx.LEFT, 15),
                               (qx_unit_txt, 0, wx.LEFT, 15)])
        inputQy_sizer.AddMany([(qy_name_txt, 0, wx.LEFT, 15),
                               (self.qy_tcl, 0, wx.LEFT, 15),
                               (qy_unit_txt, 0, wx.LEFT, 15)])
        self.input_sizer.AddMany([(q_title, 0, wx.LEFT, 15),
                                  (inputQx_sizer, 0,
                                   wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                  (inputQy_sizer, 0,
                                   wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])

    def _layout_output(self):
        """
        Fill the sizer containing dQ|| and dQ+
        """
        sigma_title = wx.StaticText(self, -1,
                                    "[Standard Deviation of the Resolution Distribution]:")
        # sizers for inputs
        outputQxy_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outputQ_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sigma_unit = '[' + '1/A' + ']'
        self.sigma_r_txt = wx.StaticText(self, -1, 'Sigma_x:   ')
        self.sigma_r_tcl = OutputTextCtrl(self, -1, size=(_BOX_WIDTH * 0.8, -1))
        self.sigma_phi_txt = wx.StaticText(self, -1, 'Sigma_y:')
        self.sigma_phi_tcl = OutputTextCtrl(self, -1, size=(_BOX_WIDTH * 0.8, -1))
        self.sigma_lamd_txt = wx.StaticText(self, -1, 'Sigma_lamd:')
        self.sigma_lamd_tcl = OutputTextCtrl(self, -1, size=(_BOX_WIDTH * 0.7, -1))
        sigma_1d_txt = wx.StaticText(self, -1, '( 1D:   Sigma:')
        self.sigma_1d_tcl = OutputTextCtrl(self, -1, size=(_BOX_WIDTH * 0.7, -1))
        sigmax_hint = " The x component of the geometric resolution,"
        sigmax_hint += " excluding sigma_lamda."
        sigmay_hint = " The y component of the geometric resolution,"
        sigmay_hint += " excluding sigma_lamda."
        sigma_hint_lamd = " The wavelength contribution in the radial direction"
        sigma_hint_lamd += ".\n Note: The phi component is always zero."
        sigma_hint_1d = " Resolution in 1-dimension (for 1D data)."
        self.sigma_r_tcl.SetToolTipString(sigmax_hint)
        self.sigma_phi_tcl.SetToolTipString(sigmay_hint)
        self.sigma_lamd_tcl.SetToolTipString(sigma_hint_lamd)
        self.sigma_1d_tcl.SetToolTipString(sigma_hint_1d)
        sigma_r_unit_txt = wx.StaticText(self, -1, sigma_unit)
        sigma_phi_unit_txt = wx.StaticText(self, -1, sigma_unit)
        sigma_lamd_unit_txt = wx.StaticText(self, -1, sigma_unit)
        sigma_1d_unit_txt = wx.StaticText(self, -1, sigma_unit + ' )')
        outputQxy_sizer.AddMany([(self.sigma_r_txt, 0, wx.LEFT, 15),
                                 (self.sigma_r_tcl, 0, wx.LEFT, 15),
                                 (sigma_r_unit_txt, 0, wx.LEFT, 15),
                                 (self.sigma_phi_txt, 0, wx.LEFT, 15),
                                 (self.sigma_phi_tcl, 0, wx.LEFT, 15),
                                 (sigma_phi_unit_txt, 0, wx.LEFT, 15)])
        outputQ_sizer.AddMany([(self.sigma_lamd_txt, 0, wx.LEFT, 15),
                               (self.sigma_lamd_tcl, 0, wx.LEFT, 15),
                               (sigma_lamd_unit_txt, 0, wx.LEFT, 15),
                               (sigma_1d_txt, 0, wx.LEFT, 15),
                               (self.sigma_1d_tcl, 0, wx.LEFT, 15),
                               (sigma_1d_unit_txt, 0, wx.LEFT, 15)])
        self.output_sizer.AddMany([(sigma_title, 0, wx.LEFT, 15),
                                   (outputQxy_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (outputQ_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])

    def _layout_hint(self):
        """
        Fill the sizer containing hint
        """
        hint_msg = ""
        #hint_msg += "This tool is to approximately compute "
        #hint_msg += "the instrumental resolution (dQ)."

        self.hint_txt = wx.StaticText(self, -1, hint_msg)
        self.hint_sizer.AddMany([(self.hint_txt, 0, wx.LEFT, 15)])

    def _layout_button(self):
        """
        Do the layout for the button widgets
        """

        wx_id = wx.NewId()
        self.reset_button = wx.Button(self, wx_id, "Reset")
        hint_on_reset = "..."
        self.reset_button.SetToolTipString(hint_on_reset)
        self.Bind(wx.EVT_BUTTON, self.on_reset, id=wx_id)
        #compute button
        wx_id = wx.NewId()
        self.compute_button = wx.Button(self, wx_id, "Compute")
        hint_on_compute = "Compute... Please wait until finished."
        self.compute_button.SetToolTipString(hint_on_compute)
        self.Bind(wx.EVT_BUTTON, self.on_compute, id=wx_id)
        #help button
        wx_id = wx.NewId()
        self.help_button = wx.Button(self, wx_id, "HELP")
        hint_on_help = "Help on using the Resolution Calculator"
        self.help_button.SetToolTipString(hint_on_help)
        self.Bind(wx.EVT_BUTTON, self.on_help, id=wx_id)
        # close button
        self.bt_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this window.")

        self.button_sizer.Add((110, -1))
        self.button_sizer.AddMany([(self.reset_button, 0, wx.LEFT, 50),
                                   (self.compute_button, 0, wx.LEFT, 15),
                                   (self.help_button, 0, wx.LEFT, 15),
                                   (self.bt_close, 0, wx.LEFT, 15)])
        self.compute_button.SetFocus()

    def _layout_image(self):
        """
        Layout for image plot
        """
        # Contribution by James C.
        # Instantiate a figure object that will contain our plots.
        # Make the fig a little smaller than the default
        self.figure = Figure(figsize=(6.5, 6), facecolor='white')

        # Initialize the figure canvas, mapping the figure object to the plot
        # engine backend.
        self.canvas = FigureCanvas(self, wx.ID_ANY, self.figure)

        # Wx-Pylab magic ...
        # Make our canvas the active figure manager for pylab so that when
        # pylab plotting statements are executed they will operate on our
        # canvas and not create a new frame and canvas for display purposes.
        # This technique allows this application to execute code that uses
        # pylab stataments to generate plots and embed these plots in our
        # application window(s).
        self.fm = FigureManagerBase(self.canvas, 1)
        _pylab_helpers.Gcf.set_active(self.fm)

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(self.canvas)
        # Diable pan
        mpl_toolbar.DeleteToolByPos(3)

        # Add a toolbar into the frame
        mpl_toolbar.Realize()

        # Compute before adding the canvas to the sizer
        self.on_compute()

        # Fill up the sizer
        if IS_WIN:
            gap = 27
        else:
            gap = 13
        self.vertical_r_sizer.Add(self.canvas, 0, wx.ALL | wx.EXPAND, 2)
        self.vertical_r_spacer.Add((0, gap))
        self.vertical_r_spacer.Add(self.vertical_r_sizer, 0, wx.ALL | wx.EXPAND, 2)
        self.vertical_r_spacer.Add((0, gap))
        self.vertical_r_spacer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 2)
        self.vertical_r_spacer.Add(mpl_toolbar, 0, wx.ALL | wx.EXPAND, 2)

    def _do_layout(self):
        """
            Draw window layout
        """
        #  Title of parameters
        instrument_txt = wx.StaticText(self, -1, '[Instrumental Parameters]:')
        # Build individual layouts
        self._define_structure()
        self._layout_mass()
        self._layout_wavelength()
        self._layout_wavelength_spread()
        self._layout_source_aperture()
        self._layout_sample_aperture()
        self._layout_source2sample_distance()
        self._layout_sample2detector_distance()
        self._layout_sample2sample_distance()
        self._layout_detector_size()
        self._layout_detector_pix_size()
        self._layout_input()
        self._layout_output()
        self._layout_hint()
        self._layout_button()
        # Fill the sizers
        self.boxsizer_source.AddMany([(instrument_txt, 0,
                                       wx.EXPAND | wx.LEFT, 15),
                                      (self.mass_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.wavelength_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.wavelength_spread_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.source_aperture_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.sample_aperture_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.source2sample_distance_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.sample2detector_distance_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.sample2sample_distance_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.detector_size_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.detector_pix_size_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (wx.StaticLine(self), 0,
                                       wx.ALL | wx.EXPAND, 5),
                                      (self.input_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (wx.StaticLine(self), 0,
                                       wx.ALL | wx.EXPAND, 5),
                                      (self.output_sizer, 0,
                                       wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.vertical_l_sizer.AddMany([(self.boxsizer_source, 0, wx.ALL, 10),
                                       (wx.StaticLine(self), 0,
                                        wx.ALL | wx.EXPAND, 5),
                                       (self.button_sizer, 0,
                                        wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.main_sizer.Add(self.vertical_l_sizer, 0, wx.ALL, 10)

        # Build image plot layout
        self._layout_image()
        # Add a vertical static line
        self.main_sizer.Add(wx.StaticLine(self, -1, (2, 2),
                                          (2, PANEL_HEIGHT * 0.94), style=wx.LI_VERTICAL))
        # Add the plot to main sizer
        self.main_sizer.Add(self.vertical_r_spacer, 0, wx.ALL, 10)
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def on_help(self, event):
        """
        Bring up the Resolution calculator Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/calculator/"
        _TreeLocation += "resolution_calculator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Resolution Calculator Help")

    def on_close(self, event):
        """
        close the window containing this panel
        """
        # get ready for other events
        if event is not None:
            event.Skip()
        # Clear the plot
        if self.image is not None:
            self.image.clf()
            # reset image
            self.image = None
        # Close panel
        self.parent.OnClose(None)

    def on_compute(self, event=None):
        """
        Execute the computation of resolution
        """
        wx.CallAfter(self.on_compute_call, event)

    def on_compute_call(self, event=None):
        """
        Execute the computation of resolution
        """
        # Skip event for next event
        if event is not None:
            event.Skip()
            msg = "Please Check your input values "
            msg += "before starting the computation..."

        # message
        status_type = 'progress'
        msg = 'Calculating...'
        self._status_info(msg, status_type)

        status_type = 'stop'
        # Q min max list default
        qx_min = []
        qx_max = []
        qy_min = []
        qy_max = []
        # possible max qrange
        self.resolution.qxmin_limit = 0
        self.resolution.qxmax_limit = 0
        self.resolution.qymin_limit = 0
        self.resolution.qymax_limit = 0
        # q min and max of the detector
        try:
            # Get all the values at set to compute
            # default num bin of wave list
            self.num_wave = 10
            wavelength = self._str2longlist(self.wavelength_tcl.GetValue())
            source = self.source_cb.GetValue()
            mass = self.source_mass[str(source)]
            self.resolution.set_neutron_mass(float(mass))
            wavelength_spread = self._str2longlist(\
                        self.wavelength_spread_tcl.GetValue().split(';')[0])
            # Validate the wave inputs
            wave_input = self._validate_q_input(wavelength, wavelength_spread)
            if wave_input is not None:
                wavelength, wavelength_spread = wave_input

            self.resolution.set_wave(wavelength)
            self.resolution.set_wave_spread(wavelength_spread)
            source_aperture_size = self.source_aperture_tcl.GetValue()
            source_aperture_size = self._string2list(source_aperture_size)
            self.resolution.set_source_aperture_size(source_aperture_size)
            sample_aperture_size = self.sample_aperture_tcl.GetValue()
            sample_aperture_size = self._string2list(sample_aperture_size)
            self.resolution.set_sample_aperture_size(sample_aperture_size)
            source2sample_distance = self.source2sample_distance_tcl.GetValue()
            source2sample_distance = self._string2list(source2sample_distance)
            self.resolution.set_source2sample_distance(source2sample_distance)
            sample2sample_distance = self.sample2sample_distance_tcl.GetValue()
            sample2sample_distance = self._string2list(sample2sample_distance)
            self.resolution.set_sample2sample_distance(sample2sample_distance)
            sample2detector_distance = \
                                self.sample2detector_distance_tcl.GetValue()
            sample2detector_distance = \
                                self._string2list(sample2detector_distance)
            self.resolution.set_sample2detector_distance(\
                                                    sample2detector_distance)
            detector_size = self.detector_size_tcl.GetValue()
            detector_size = self._string2list(detector_size)
            self.resolution.set_detector_size(detector_size)
            detector_pix_size = self.detector_pix_size_tcl.GetValue()
            detector_pix_size = self._string2list(detector_pix_size)
            self.resolution.set_detector_pix_size(detector_pix_size)
            self.qx = self._string2inputlist(self.qx_tcl.GetValue())
            self.qy = self._string2inputlist(self.qy_tcl.GetValue())

            # Find min max of qs
            xmin = min(self.qx)
            xmax = max(self.qx)
            ymin = min(self.qy)
            ymax = max(self.qy)
            if not self._validate_q_input(self.qx, self.qy):
                raise
        except:
            msg = "An error occured during the resolution computation."
            msg += "Please check your inputs..."
            self._status_info(msg, status_type)
            wx.MessageBox(msg, 'Warning')
            return
            #raise ValueError, "Invalid Q Input..."

        # Validate the q inputs
        q_input = self._validate_q_input(self.qx, self.qy)
        if q_input is not None:
            self.qx, self.qy = q_input

        # Make list of q min max for mapping
        for i in range(len(self.qx)):
            qx_min.append(xmin)
            qx_max.append(xmax)
        for i in range(len(self.qy)):
            qy_min.append(ymin)
            qy_max.append(ymax)

        # Compute the resolution
        if self.image is not None:
            #_pylab_helpers.Gcf.set_active(self.fm)
            _pylab_helpers.Gcf.figs = {}
            # Clear the image before redraw
            self.image.clf()
            # reset the image
            self.resolution.reset_image()

        # Compute and get the image plot
        try:
            from sas.sasgui.perspectives.calculator.resolcal_thread import CalcRes as thread
            self.sigma_strings = '\nResolution: Computation is finished. \n'
            cal_res = thread(func=self._map_func,
                             qx=self.qx,
                             qy=self.qy,
                             qx_min=qx_min,
                             qx_max=qx_max,
                             qy_min=qy_min,
                             qy_max=qy_max,
                             image=self.image,
                             completefn=self.complete)
            cal_res.queue()
            msg = "Computation is in progress..."
            status_type = 'progress'
            self._status_info(msg, status_type)
        except:
            raise

    def complete(self, image, elapsed=None):
        """
        Callafter complete: wx call after needed for stable output
        """
        wx.CallAfter(self.complete_cal, image, elapsed)

    def complete_cal(self, image, elapsed=None):
        """
        Complete computation
        """
        self.image = image
        # Draw lines in image before drawing
        wave_list, _ = self.resolution.get_wave_list()
        if len(wave_list) > 1 and wave_list[-1] == max(wave_list):
            # draw a green rectangle(limit for the longest wavelength
            # to be involved) for tof inputs
            self._draw_lines(self.image, color='g')
        self._draw_lines(self.image, color='r')
        # Draw image
        self.image.draw()

        # Get and format the sigmas
        sigma_r = self.format_number(self.resolution.sigma_1)
        sigma_phi = self.format_number(self.resolution.sigma_2)
        sigma_lamd = self.format_number(self.resolution.sigma_lamd)
        sigma_1d = self.format_number(self.resolution.sigma_1d)

        # Set output values
        self.sigma_r_tcl.SetValue(str(sigma_r))
        self.sigma_phi_tcl.SetValue(str(sigma_phi))
        self.sigma_lamd_tcl.SetValue(str(sigma_lamd))
        self.sigma_1d_tcl.SetValue(str(sigma_1d))
        msg = self.sigma_strings
        msg += "\n"
        status_type = 'stop'
        self._status_info(msg, status_type)

    def _draw_lines(self, image=None, color='r'):
        """
        Draw lines in image if applicable
        : Param image: pylab object
        """
        if image is None:
            return
        if color == 'g':
            # Get the params from resolution
            # ploting range for largest wavelength
            qx_min = self.resolution.qx_min
            qx_max = self.resolution.qx_max
            qy_min = self.resolution.qy_min
            qy_max = self.resolution.qy_max
            # detector range
            detector_qx_min = self.resolution.detector_qx_min
            detector_qx_max = self.resolution.detector_qx_max
            detector_qy_min = self.resolution.detector_qy_min
            detector_qy_max = self.resolution.detector_qy_max
        else:
            qx_min, qx_max, qy_min, qy_max = \
                                self.resolution.get_detector_qrange()
            # detector range
            detector_qx_min = self.resolution.qxmin_limit
            detector_qx_max = self.resolution.qxmax_limit
            detector_qy_min = self.resolution.qymin_limit
            detector_qy_max = self.resolution.qymax_limit

        # Draw zero axis lines
        if qy_min < 0 and qy_max >= 0:
            image.axhline(linewidth=1)
        if qx_min < 0 and qx_max >= 0:
            image.axvline(linewidth=1)

        # Find x and y ratio values to draw the detector outline
        x_min = fabs(detector_qx_min - qx_min) / (qx_max - qx_min)
        x_max = fabs(detector_qx_max - qx_min) / (qx_max - qx_min)
        y_min = fabs(detector_qy_min - qy_min) / (qy_max - qy_min)
        y_max = fabs(detector_qy_max - qy_min) / (qy_max - qy_min)

        # Draw Detector outline
        if detector_qy_min >= qy_min:
            image.axhline(y=detector_qy_min + 0.0002,
                          xmin=x_min, xmax=x_max,
                          linewidth=2, color=color)
        if detector_qy_max <= qy_max:
            image.axhline(y=detector_qy_max - 0.0002,
                          xmin=x_min, xmax=x_max,
                          linewidth=2, color=color)
        if detector_qx_min >= qx_min:
            image.axvline(x=detector_qx_min + 0.0002,
                          ymin=y_min, ymax=y_max,
                          linewidth=2, color=color)
        if detector_qx_max <= qx_max:
            image.axvline(x=detector_qx_max - 0.0002,
                          ymin=y_min, ymax=y_max,
                          linewidth=2, color=color)
        xmin = min(self.qx)
        xmax = max(self.qx)
        ymin = min(self.qy)
        ymax = max(self.qy)
        if color != 'g':
            if xmin < detector_qx_min or xmax > detector_qx_max or \
                        ymin < detector_qy_min or ymax > detector_qy_max:
                # message
                status_type = 'stop'
                msg = 'At least one q value located out side of\n'
                msg += " the detector range (%s < qx < %s, %s < qy < %s),\n" % \
                        (self.format_number(detector_qx_min),
                         self.format_number(detector_qx_max),
                         self.format_number(detector_qy_min),
                         self.format_number(detector_qy_max))
                msg += " is ignored in computation.\n"

                self._status_info(msg, status_type)
                wx.MessageBox(msg, 'Warning')

    def _map_func(self, qx, qy, qx_min, qx_max, qy_min, qy_max):
        """
        Prepare the Mapping for the computation
        : params qx, qy, qx_min, qx_max, qy_min, qy_max:

        : return: image (pylab)
        """
        try:
            qx_value = float(qx)
            qy_value = float(qy)
        except:
            raise
        # calculate 2D resolution distribution image
        image = self.resolution.compute_and_plot(qx_value, qy_value,
                                                 qx_min, qx_max, qy_min, qy_max,
                                                 self.det_coordinate)
        # record sigmas
        self.sigma_strings += " At Qx = %s, Qy = %s; \n" % (qx_value, qy_value)
        self._sigma_strings()
        return image

    def _sigma_strings(self):
        """
        Recode sigmas as strings
        """
        sigma_r = self.format_number(self.resolution.sigma_1)
        sigma_phi = self.format_number(self.resolution.sigma_2)
        sigma_lamd = self.format_number(self.resolution.sigma_lamd)
        sigma_1d = self.format_number(self.resolution.sigma_1d)
        # Set output values
        self.sigma_strings += "   sigma_x = %s\n" % sigma_r
        self.sigma_strings += "   sigma_y = %s\n" % sigma_phi
        self.sigma_strings += "   sigma_lamd = %s\n" % sigma_lamd
        self.sigma_strings += "   sigma_1D = %s\n" % sigma_1d

    def _validate_q_input(self, qx, qy):
        """
        Check if q inputs are valid
        : params qx:  qx as a list
        : params qy:  qy as a list

        : return: True/False
        """
        # check qualifications
        if qx.__class__.__name__ != 'list':
            return None
        if qy.__class__.__name__ != 'list':
            return None
        if len(qx) < 1:
            return None
        if len(qy) < 1:
            return None
        # allow one input
        if len(qx) == 1 and len(qy) > 1:
            qx = [qx[0] for ind in range(len(qy))]
            #self.qx = qx
        if len(qy) == 1 and len(qx) > 1:
            qy = [qy[0] for ind in range(len(qx))]
            #self.qy = qy
        # check length
        if len(qx) != len(qy):
            return None
        if qx is None or qy is None:
            return None
        return qx, qy

    def on_reset(self, event):
        """
        Execute the reset
        """
        # skip for another event
        if event is not None:
            event.Skip()
        # init resolution_calculator
        self.resolution = ResolutionCalculator()
        self.resolution.get_all_instrument_params()
        # reset all param values
        self.source_cb.SetValue('Neutron')
        self._on_source_selection(None)
        self.wave_color_cb.SetValue('Monochromatic')
        self._on_source_color(None)
        #self.intensity_tcl.SetValue(str(self.resolution.intensity))
        self.wavelength_tcl.SetValue(str(6.0))
        self.wavelength_spread_tcl.SetValue(str(0.125))
        self.resolution.set_spectrum(self.spectrum_dic['Flat'])
        self.spectrum_txt.Show(False)
        self.spectrum_cb.Show(False)
        source_aperture_value = str(self.resolution.source_aperture_size[0])
        if len(self.resolution.source_aperture_size) > 1:
            source_aperture_value += ", "
            source_aperture_value += \
                str(self.resolution.source_aperture_size[1])
        self.source_aperture_tcl.SetValue(str(source_aperture_value))
        sample_aperture_value = str(self.resolution.sample_aperture_size[0])
        if len(self.resolution.sample_aperture_size) > 1:
            sample_aperture_value += ", "
            sample_aperture_value += \
                str(self.resolution.sample_aperture_size[1])
        self.sample_aperture_tcl.SetValue(sample_aperture_value)
        source2sample_distance_value = \
            str(self.resolution.source2sample_distance[0])
        self.source2sample_distance_tcl.SetValue(source2sample_distance_value)
        sample2sample_distance_value = \
            str(self.resolution.sample2sample_distance[0])
        self.sample2sample_distance_tcl.SetValue(sample2sample_distance_value)
        sample2detector_distance_value = \
            str(self.resolution.sample2detector_distance[0])
        self.sample2detector_distance_tcl.SetValue(\
                                            sample2detector_distance_value)
        detector_size_value = str(self.resolution.detector_size[0])
        if len(self.resolution.detector_size) > 1:
            detector_size_value += ", "
            detector_size_value += str(self.resolution.detector_size[1])
        self.detector_size_tcl.SetValue(detector_size_value)
        detector_pix_size_value = str(self.resolution.detector_pix_size[0])
        if len(self.resolution.detector_pix_size) > 1:
            detector_pix_size_value += ", "
            detector_pix_size_value += str(self.resolution.detector_pix_size[1])
        self.detector_pix_size_tcl.SetValue(detector_pix_size_value)
        #layout attribute
        self.hint_sizer = None
        # reset q inputs
        self.qx_tcl.SetValue(str(_Q_DEFAULT))
        self.qy_tcl.SetValue(str(_Q_DEFAULT))
        # reset sigma outputs
        self.sigma_r_tcl.SetValue('')
        self.sigma_phi_tcl.SetValue('')
        self.sigma_1d_tcl.SetValue('')
        # reset radio button
        #self.r_phi_rb.SetValue(True)
        # Finally re-compute
        self.on_compute()
        # msg on info
        msg = " Finished the resetting..."
        self._status_info(msg, 'stop')

    def format_number(self, value=None):
        """
        Return a float in a standardized, human-readable formatted string
        """
        try:
            value = float(value)
        except:
            output = None
            return output

        output = "%-7.4g" % value
        return output.lstrip().rstrip()

    def _string2list(self, string):
        """
        Change NNN, NNN to list,ie. [NNN, NNN] where NNN is a number
        """
        new_string = []
        # check the number of floats
        try:
            strg = float(string)
            new_string.append(strg)
        except:
            string_split = string.split(',')
            if len(string_split) == 2:
                str_1 = string_split[0]
                str_2 = string_split[1]
                new_string.append(float(str_1))
                new_string.append(float(str_2))
            elif len(string_split) == 1:
                str_1 = string_split[0]
                new_string.append(float(str_1))
            else:
                msg = "The numbers must be one or two (separated by ',')..."
                self._status_info(msg, 'stop')
                raise RuntimeError(msg)

        return new_string

    def _string2inputlist(self, string):
        """
        Change NNN, NNN,... to list,ie. [NNN, NNN,...] where NNN is a number

        : return new_string: string like list
        """
        new_string = []
        string_split = string.split(',')
        length = len(string_split)
        for ind in range(length):
            try:
                value = float(string_split[ind])
                new_string.append(value)
            except:
                logger.error(sys.exc_info()[1])

        return new_string

    def _str2longlist(self, string):
        """
        Change NNN, NNN,... to list, NNN - NNN ; NNN to list, or float to list

        : return new_string: string like list
        """
        msg = "Wrong format of intputs."
        try:
            # is float
            out = [float(string)]
            return out
        except:
            if self.wave_color.lower().count('mono') > 0:
                wx.MessageBox(msg, 'Warning')
            else:
                try:
                    # has a '-'
                    if string.count('-') > 0:
                        value = string.split('-')
                        if value[1].count(';') > 0:
                            # has a ';'
                            last_list = value[1].split(';')
                            num = math.ceil(float(last_list[1]))
                            max_value = float(last_list[0])
                            self.num_wave = num
                        else:
                            # default num
                            num = self.num_wave
                            max_value = float(value[1])
                        min_value = float(value[0])
                        # make a list
                        bin_size = math.fabs(max_value - min_value) / (num - 1)
                        out = [min_value + bin_size * bnum for bnum in range(num)]
                        return out
                    if string.count(',') > 0:
                        out = self._string2inputlist(string)
                        return out
                except:
                    logger.error(sys.exc_info()[1])

    def _on_xy_coordinate(self, event=None):
        """
        Set the detector coordinate for sigmas to x-y coordinate
        """
        if event is not None:
            event.Skip()
        # Set the coordinate in Cartesian
        self.det_coordinate = 'cartesian'
        self.sigma_r_txt.SetLabel('Sigma_x:')
        self.sigma_phi_txt.SetLabel('Sigma_y:')
        self._onparamEnter()

    def _on_rp_coordinate(self, event=None):
        """
        Set the detector coordinate for sigmas to polar coordinate
        """
        if event is not None:
            event.Skip()
        # Set the coordinate in polar
        self.det_coordinate = 'polar'
        self.sigma_r_txt.SetLabel('Sigma_r:   ')
        self.sigma_phi_txt.SetLabel('Sigma_phi:')
        self._onparamEnter()

    def _status_info(self, msg='', type="update"):
        """
        Status msg
        """
        if type == "stop":
            label = "Compute"
            able = True
        else:
            label = "Wait..."
            able = False
        self.compute_button.Enable(able)
        self.compute_button.SetLabel(label)
        self.compute_button.SetToolTipString(label)
        if self.parent.parent is not None:
            wx.PostEvent(self.parent.parent,
                         StatusEvent(status=msg, type=type))


    def _onparamEnter(self, event=None):
        """
        On Text_enter_callback, perform compute
        """
        self.on_compute()

    def _on_source_selection(self, event=None):
        """
        On source combobox selection
        """
        if event is not None:
            combo = event.GetEventObject()
            event.Skip()
        else:
            combo = self.source_cb
        selection = combo.GetValue()
        mass = self.source_mass[selection]
        self.resolution.set_neutron_mass(mass)
        source_hint = "Source Selection: Affect on"
        source_hint += " the gravitational contribution.\n"
        source_hint += "Mass of %s: m = %s [g]" % \
                            (selection, str(self.resolution.get_neutron_mass()))
        # source_tip.SetTip(source_hint)
        self.mass_txt.ToolTip.SetTip(source_hint)

    def _on_source_color(self, event=None):
        """
        On source color combobox selection
        """
        if event is not None:
            #combo = event.GetEventObject()
            event.Skip()
        #else:
        combo = self.wave_color_cb
        selection = combo.GetValue()
        self.wave_color = selection
        if self.wave_color.lower() == 'tof':
            list = self.resolution.get_wave_list()
            minw = min(list[0])
            if len(list[0]) < 2:
                maxw = 2 * minw
            else:
                maxw = max(list[0])
            self.wavelength_tcl.SetValue('%s - %s' % (minw, maxw))
            minw = min(list[1])
            maxw = max(list[1])
            self.wavelength_spread_tcl.SetValue('%s - %s' % (minw, maxw))
            spectrum_val = self.spectrum_cb.GetValue()
            self.resolution.set_spectrum(self.spectrum_dic[spectrum_val])
            self.spectrum_txt.Show(True)
            self.spectrum_cb.Show(True)

        else:
            wavelength = self.resolution.get_wavelength()
            wavelength_spread = self.resolution.get_wavelength_spread()
            self.wavelength_tcl.SetValue(str(wavelength))
            self.wavelength_spread_tcl.SetValue(str(wavelength_spread))
            self.resolution.set_spectrum(self.spectrum_dic['Flat'])
            self.spectrum_txt.Show(False)
            self.spectrum_cb.Show(False)
        self.wavelength_sizer.Layout()
        self.Layout()

    def _on_spectrum_cb(self, event=None):
        """
        On spectrum ComboBox event
        """
        if event is not None:
            #combo = event.GetEventObject()
            event.Skip()
        else:
            raise
        selection = self.spectrum_cb.GetValue()
        if selection == 'Add new':
            path = self._selectDlg()
            if path is None:
                self.spectrum_cb.SetValue('Flat')
                self.resolution.set_spectrum(self.spectrum_dic['Flat'])
                msg = "No file has been chosen."
                wx.MessageBox(msg, 'Info')
                return
            try:
                basename = os.path.basename(path)
                if basename not in list(self.spectrum_dic.keys()):
                    self.spectrum_cb.Append(basename)
                self.spectrum_dic[basename] = self._read_file(path)
                self.spectrum_cb.SetValue(basename)
                self.resolution.set_spectrum(self.spectrum_dic[basename])
                return
            except:
                raise

        self.resolution.set_spectrum(self.spectrum_dic[selection])

    def _selectDlg(self):
        """
        open a dialog file to select a customized spectrum
        """
        dlg = wx.FileDialog(self,
                            "Choose a wavelength spectrum file: Intensity vs. wavelength",
                            self.parent.parent.get_save_location() , "", "*.*", wx.OPEN)
        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path

    def _read_file(self, path):
        """
        Read two columns file as tuples of numpy array

        :param path: the path to the file to read

        """
        try:
            if path is None:
                wx.PostEvent(self.parent.parent, StatusEvent(status=\
                            " Selected Distribution was not loaded: %s" % path))
                return None, None
            input_f = open(path, 'r')
            buff = input_f.read()
            lines = buff.split('\n')

            wavelength = []
            intensity = []
            for line in lines:
                toks = line.split()
                try:
                    wave = float(toks[0])
                    intens = float(toks[1])
                    wavelength.append(wave)
                    intensity.append(intens)
                except:
                    # Skip non-data lines
                    logger.error(sys.exc_info()[1])

            return [wavelength, intensity]
        except:
            raise

class ResolutionWindow(widget.CHILD_FRAME):
    """
    Resolution Window
    """
    def __init__(self, parent=None, manager=None,
                 title="Q Resolution Estimator",
                 size=(PANEL_WIDTH * 2, PANEL_HEIGHT), *args, **kwds):
        kwds['title'] = title
        kwds['size'] = size
        widget.CHILD_FRAME.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self.panel = ResolutionCalculatorPanel(parent=self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def OnClose(self, event):
        """
        On close event
        """
        _pylab_helpers.Gcf.figs = {}
        if self.manager is not None:
            self.manager.cal_res_frame = None
        self.Destroy()


if __name__ == "__main__":
    app = wx.PySimpleApp()
    widget.CHILD_FRAME = wx.Frame
    frame = ResolutionWindow()
    frame.Show(True)
    app.MainLoop()

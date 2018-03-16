import wx
from .plottables import Theory1D
import math
import numpy as np
from . import fittings
from . import transform
import sys

# Linear fit panel size
if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
    PNL_WIDTH = 450
    PNL_HEIGHT = 500
else:
    FONT_VARIANT = 1
    PNL_WIDTH = 500
    PNL_HEIGHT = 500
RG_ON = True

def format_number(value, high=False):
    """
    Return a float in a standardized, human-readable formatted string.
    This is used to output readable (e.g. x.xxxe-y) values to the panel.
    """
    try:
        value = float(value)
    except:
        output = "NaN"
        return output.lstrip().rstrip()

    if high:
        output = "%-6.4g" % value

    else:
        output = "%-5.3g" % value
    return output.lstrip().rstrip()


class LinearFit(wx.Dialog):
    def __init__(self, parent, plottable, push_data, transform, title):
        """
        Dialog window pops- up when select Linear fit on Context menu
        Displays fitting parameters. This class handles the linearized
        fitting and derives and displays specialized output parameters based
        on the scale choice of the plot calling it.
        
        :note1: The fitting is currently a bit convoluted as besides using
        plottools.transform.py to handle all the conversions, it uses
        LineModel to define a linear model and calculate a number of
        things like residuals etc as well as the function itself given an x
        value. It also uses fittings.py to set up the defined LineModel for
        fitting and then send it to the SciPy NLLSQ method.  As these are by
        definition "linear nodels" it would make more sense to just call
        a linear solver such as scipy.stats.linregress or bumps.wsolve directly.
        This would considerably simplify the code and remove the need I think
        for LineModel.py and possibly fittins.py altogether.   -PDB 7/10/16
        
        :note2: The linearized fits do not take resolution into account. This
        means that for poor resolution such as slit smearing the answers will
        be completely wrong --- Rg would be OK but I0 would be orders of
        magnitude off.  Eventually we should fix this to account properly for
        resolution.   -PDB  7/10/16
        """
        wx.Dialog.__init__(self, parent, title=title,
                           size=(PNL_WIDTH, 350))
        self.parent = parent
        self.transform = transform
        # Font
        self.SetWindowVariant(variant=FONT_VARIANT)
        # Registered owner for close event
        self._registered_close = None
        # dialog panel self call function to plot the fitting function
        # calls the calling PlotPanel method onFitDisplay
        self.push_data = push_data
        # dialog self plottable - basically the plot we are working with
        # passed in by the caller
        self.plottable = plottable
        # is this a Guinier fit
        self.rg_on = False
        # Receive transformations of x and y - basically transform is passed
        # as caller method that returns its current value for these
        self.xLabel, self.yLabel, self.Avalue, self.Bvalue, \
               self.ErrAvalue, self.ErrBvalue, self.Chivalue = self.transform()

        # Now set up the dialog interface
        self.layout()
        # Receives the type of model for the fitting
        from .LineModel import LineModel
        self.model = LineModel()
        # Display the fittings values
        self.default_A = self.model.getParam('A')
        self.default_B = self.model.getParam('B')
        self.cstA = fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB = fittings.Parameter(self.model, 'B', self.default_B)

        # Set default value of parameter in the dialog panel
        if self.Avalue is None:
            self.tcA.SetValue(format_number(self.default_A))
        else:
            self.tcA.SetLabel(format_number(self.Avalue))
        if self.Bvalue is None:
            self.tcB.SetValue(format_number(self.default_B))
        else:
            self.tcB.SetLabel(format_number(self.Bvalue))
        if self.ErrAvalue is None:
            self.tcErrA.SetLabel(format_number(0.0))
        else:
            self.tcErrA.SetLabel(format_number(self.ErrAvalue))
        if self.ErrBvalue is None:
            self.tcErrB.SetLabel(format_number(0.0))
        else:
            self.tcErrB.SetLabel(format_number(self.ErrBvalue))
        if self.Chivalue is None:
            self.tcChi.SetLabel(format_number(0.0))
        else:
            self.tcChi.SetLabel(format_number(self.Chivalue))
        if self.plottable.x != []:
            # store the values of View in self.x,self.y,self.dx,self.dy
            self.x, self.y, self.dx, \
                     self.dy = self.plottable.returnValuesOfView()
            try:
                self.mini = self.floatForwardTransform(min(self.x))
            except:
                self.mini = "Invalid"
            try:
                self.maxi = self.floatForwardTransform(max(self.x))
            except:
                self.maxi = "Invalid"

            self.initXmin.SetValue(format_number(min(self.plottable.x)))
            self.initXmax.SetValue(format_number(max(self.plottable.x)))
            self.mini = min(self.x)
            self.maxi = max(self.x)
            self.xminFit.SetValue(format_number(self.mini))
            self.xmaxFit.SetValue(format_number(self.maxi))

    def layout(self):
        """
        Sets up the panel layout for the linear fit including all the
        labels, text entry boxes, and buttons.

        """

        # set up sizers first. 
        # vbox is the panel sizer and is a vertical sizer
        # The first element of the panel is sizer which is a gridbagsizer
        # and contains most of the text fields
        # this is followed by a line separator added to vbox
        # and finally the sizer_button (a horizontal sizer) adds the buttons
        vbox = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5, 5)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        
        #size of string boxes in pixels
        _BOX_WIDTH = 100
        _BOX_HEIGHT = 20
        #now set up all the text fields
        self.tcA = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        self.tcA.SetToolTipString("Fit value for the slope parameter.")
        self.tcErrA = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        self.tcErrA.SetToolTipString("Error on the slope parameter.")
        self.tcB = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        self.tcA.SetToolTipString("Fit value for the constant parameter.")
        self.tcErrB = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        self.tcErrB.SetToolTipString("Error on the constant parameter.")
        self.tcChi = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        self.tcChi.SetToolTipString("Chi^2 over degrees of freedom.")
        self.xminFit = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        msg = "Enter the minimum value on "
        msg += "the x-axis to be included in the fit."
        self.xminFit.SetToolTipString(msg)
        self.xmaxFit = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        msg = "Enter the maximum value on "
        msg += " the x-axis to be included in the fit."
        self.xmaxFit.SetToolTipString(msg)
        self.initXmin = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        msg = "Minimum value on the x-axis for the plotted data."
        self.initXmin.SetToolTipString(msg)
        self.initXmax = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, _BOX_HEIGHT))
        msg = "Maximum value on the x-axis for the plotted data."
        self.initXmax.SetToolTipString(msg)

        # Make the info box not editable
        # _BACKGROUND_COLOR = '#ffdf85'
        _BACKGROUND_COLOR = self.GetBackgroundColour()
        self.initXmin.SetEditable(False)
        self.initXmin.SetBackgroundColour(_BACKGROUND_COLOR)
        self.initXmax.SetEditable(False)
        self.initXmax.SetBackgroundColour(_BACKGROUND_COLOR)

        #set some flags for specific types of fits like Guinier (Rg) and
        #Porod (bg) -- this will determine WHAT boxes show up in the
        #sizer layout and depends on the active axis transform
        self.bg_on = False
        if RG_ON:
            if (self.yLabel == "ln(y)" or self.yLabel == "ln(y*x)") and \
                    (self.xLabel == "x^(2)"):
                self.rg_on = True
            if (self.xLabel == "x^(4)") and (self.yLabel == "y*x^(4)"):
                self.bg_on = True

        # Finally set up static text strings
        warning = "WARNING! Resolution is NOT accounted for. \n"
        warning += "Thus slit smeared data will give very wrong answers!"
        self.textwarn = wx.StaticText(self, -1, warning)
        self.textwarn.SetForegroundColour(wx.RED)
        explanation = "Perform fit for y(x) = ax + b \n"
        if self.bg_on:
            param_a = 'Background (= Parameter a)'
        else:
            param_a = 'Parameter a'


        #Now set this all up in the GridBagSizer sizer
        ix = 0
        iy = 0
        sizer.Add(self.textwarn, (iy, ix),
                  (2, 3), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        iy += 2
        sizer.Add(wx.StaticText(self, -1, explanation), (iy, ix),
                  (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        iy += 1
        sizer.Add(wx.StaticText(self, -1, param_a), (iy, ix),
                  (1, 1), wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcA, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(self, -1, '+/-'),
                  (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrA, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Parameter b'), (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcB, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(self, -1, '+/-'), (iy, ix),
                  (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrB, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Chi2/dof'), (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcChi, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 2
        ix = 1
        sizer.Add(wx.StaticText(self, -1, 'Min'), (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(wx.StaticText(self, -1, 'Max'), (iy, ix),
                  (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Maximum range (linear scale)'),
                  (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.initXmin, (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.initXmax, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Fit range of ' + self.xLabel),
                  (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.xminFit, (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.xmaxFit, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        if self.rg_on:
            self.SetSize((PNL_WIDTH, PNL_HEIGHT))
            I0_stxt = wx.StaticText(self, -1, 'I(q=0)')
            self.I0_tctr = wx.TextCtrl(self, -1, '')
            self.I0_tctr.SetEditable(False)
            self.I0_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            self.I0err_tctr = wx.TextCtrl(self, -1, '')
            self.I0err_tctr.SetEditable(False)
            self.I0err_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            Rg_stxt = wx.StaticText(self, -1, 'Rg [A]')
            Rg_stxt.Show(self.yLabel == "ln(y)")
            self.Rg_tctr = wx.TextCtrl(self, -1, '')
            self.Rg_tctr.SetEditable(False)
            self.Rg_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            self.Rg_tctr.Show(self.yLabel == "ln(y)")
            self.Rgerr_tctr = wx.TextCtrl(self, -1, '')
            self.Rgerr_tctr.SetEditable(False)
            self.Rgerr_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            self.Rgerr_tctr.Show(self.yLabel == "ln(y)")
            self.Rgerr_pm = wx.StaticText(self, -1, '+/-')
            self.Rgerr_pm.Show(self.yLabel == "ln(y)")
            Diameter_stxt = wx.StaticText(self, -1, 'Rod Diameter [A]')
            Diameter_stxt.Show(self.yLabel == "ln(y*x)")
            self.Diameter_tctr = wx.TextCtrl(self, -1, '')
            self.Diameter_tctr.SetEditable(False)
            self.Diameter_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            self.Diameter_tctr.Show(self.yLabel == "ln(y*x)")
            self.Diameter_pm = wx.StaticText(self, -1, '+/-')
            self.Diameter_pm.Show(self.yLabel == "ln(y*x)")
            self.Diametererr_tctr = wx.TextCtrl(self, -1, '')
            self.Diametererr_tctr.SetEditable(False)
            self.Diametererr_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            self.Diametererr_tctr.Show(self.yLabel == "ln(y*x)")
            RgQmin_stxt = wx.StaticText(self, -1, 'Rg*Qmin')
            self.RgQmin_tctr = wx.TextCtrl(self, -1, '')
            self.RgQmin_tctr.SetEditable(False)
            self.RgQmin_tctr.SetBackgroundColour(_BACKGROUND_COLOR)
            RgQmax_stxt = wx.StaticText(self, -1, 'Rg*Qmax')
            self.RgQmax_tctr = wx.TextCtrl(self, -1, '')
            self.RgQmax_tctr.SetEditable(False)
            self.RgQmax_tctr.SetBackgroundColour(_BACKGROUND_COLOR)

            iy += 2
            ix = 0
            sizer.Add(I0_stxt, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            ix += 1
            sizer.Add(self.I0_tctr, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix += 1
            sizer.Add(wx.StaticText(self, -1, '+/-'), (iy, ix),
                      (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix += 1
            sizer.Add(self.I0err_tctr, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)

            iy += 1
            ix = 0
            sizer.Add(Rg_stxt, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            ix += 1
            sizer.Add(self.Rg_tctr, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)

            ix += 1
            sizer.Add(self.Rgerr_pm, (iy, ix),
                      (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix += 1
            sizer.Add(self.Rgerr_tctr, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            iy += 1
            ix = 0
            sizer.Add(Diameter_stxt, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            ix += 1
            sizer.Add(self.Diameter_tctr, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)

            ix += 1
            sizer.Add(self.Diameter_pm, (iy, ix),
                      (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix += 1
            sizer.Add(self.Diametererr_tctr, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            iy += 1
            ix = 0
            sizer.Add(RgQmin_stxt, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            ix += 1
            sizer.Add(self.RgQmin_tctr, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            iy += 1
            ix = 0
            sizer.Add(RgQmax_stxt, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            ix += 1
            sizer.Add(self.RgQmax_tctr, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        #Now add some space before the separation line
        iy += 1
        ix = 0
        sizer.Add((20,20), (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        # Buttons on the bottom
        self.btFit = wx.Button(self, -1, 'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit)
        self.btFit.SetToolTipString("Perform fit.")
        self.btClose = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self._on_close)
        sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.btFit, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btClose, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        
        vbox.Add(sizer)
        self.static_line_1 = wx.StaticLine(self, -1)        
        vbox.Add(self.static_line_1, 0, wx.EXPAND, 0)
        vbox.Add(sizer_button, 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 10)

        # panel.SetSizer(sizer)
        self.SetSizer(vbox)
        self.Centre()

    def register_close(self, owner):
        """
        Method to register the close event to a parent
        window that needs notification when the dialog
        is closed

        :param owner: parent window

        """
        self._registered_close = owner

    def _on_close(self, event):
        """
        Close event.
        Notify registered owner if available.
        """
        event.Skip()
        if self._registered_close is not None:
            self._registered_close()

    def _onFit(self, event):
        """
        Performs the fit. Receive an event when clicking on
        the button Fit.Computes chisqr ,
        A and B parameters of the best linear fit y=Ax +B
        Push a plottable to the caller
        """
        tempx = []
        tempy = []
        tempdy = []

        # Check if View contains a x array .we online fit when x exits
        # makes transformation for y as a line to fit
        if self.x != []:
            if self.checkFitValues(self.xminFit) == True:
                # Check if the field of Fit Dialog contain values
                # and use the x max and min of the user
                if not self._checkVal(self.xminFit, self.xmaxFit):
                    return
                xminView = float(self.xminFit.GetValue())
                xmaxView = float(self.xmaxFit.GetValue())
                xmin = xminView
                xmax = xmaxView
                # Set the qmin and qmax in the panel that matches the
                # transformed min and max
                self.initXmin.SetValue(format_number(self.floatInvTransform(xmin)))
                self.initXmax.SetValue(format_number(self.floatInvTransform(xmax)))
                # Store the transformed values of view x, y,dy
                # in variables  before the fit
                if self.yLabel.lower() == "log10(y)":
                    if self.xLabel.lower() == "log10(x)":
                        for i in range(len(self.x)):
                            if self.x[i] >= math.log10(xmin):
                                tempy.append(math.log10(self.y[i]))
                                tempdy.append(transform.errToLogX(self.y[i], 0, self.dy[i], 0))
                    else:
                        for i in range(len(self.y)):
                            tempy.append(math.log10(self.y[i]))
                            tempdy.append(transform.errToLogX(self.y[i], 0, self.dy[i], 0))
                else:
                    tempy = self.y
                    tempdy = self.dy

                if self.xLabel.lower() == "log10(x)":
                    for x_i in self.x:
                        if x_i >= math.log10(xmin):
                            tempx.append(math.log10(x_i))
                else:
                    tempx = self.x

                # Find the fitting parameters
                # Always use the same defaults, so that fit history
                # doesn't play a role!
                self.cstA = fittings.Parameter(self.model, 'A', self.default_A)
                self.cstB = fittings.Parameter(self.model, 'B', self.default_B)

                if self.xLabel.lower() == "log10(x)":
                    tempdy = np.asarray(tempdy)
                    tempdy[tempdy == 0] = 1
                    chisqr, out, cov = fittings.sasfit(self.model,
                                                       [self.cstA, self.cstB],
                                                       tempx, tempy,
                                                       tempdy,
                                                       math.log10(xmin),
                                                       math.log10(xmax))
                else:
                    tempdy = np.asarray(tempdy)
                    tempdy[tempdy == 0] = 1
                    chisqr, out, cov = fittings.sasfit(self.model,
                                                       [self.cstA, self.cstB],
                                                       tempx, tempy, tempdy,
                                                       xminView, xmaxView)
                # Use chi2/dof
                if len(tempx) > 0:
                    chisqr = chisqr / len(tempx)

                # Check that cov and out are iterable before displaying them
                if cov is None:
                    errA = 0.0
                    errB = 0.0
                else:
                    errA = math.sqrt(cov[0][0])
                    errB = math.sqrt(cov[1][1])
                if out is None:
                    cstA = 0.0
                    cstB = 0.0
                else:
                    cstA = out[0]
                    cstB = out[1]
                # Reset model with the right values of A and B
                self.model.setParam('A', float(cstA))
                self.model.setParam('B', float(cstB))

                tempx = []
                tempy = []
                y_model = 0.0
                # load tempy with the minimum transformation

                if self.xLabel == "log10(x)":
                    y_model = self.model.run(math.log10(xmin))
                    tempx.append(xmin)
                else:
                    y_model = self.model.run(xminView)
                    tempx.append(xminView)

                if self.yLabel == "log10(y)":
                    tempy.append(math.pow(10, y_model))
                else:
                    tempy.append(y_model)

                # load tempy with the maximum transformation
                if self.xLabel == "log10(x)":
                    y_model = self.model.run(math.log10(xmax))
                    tempx.append(xmax)
                else:
                    y_model = self.model.run(xmaxView)
                    tempx.append(xmaxView)

                if self.yLabel == "log10(y)":
                    tempy.append(math.pow(10, y_model))
                else:
                    tempy.append(y_model)
                # Set the fit parameter display when  FitDialog is opened again
                self.Avalue = cstA
                self.Bvalue = cstB
                self.ErrAvalue = errA
                self.ErrBvalue = errB
                self.Chivalue = chisqr
                self.push_data(tempx, tempy, xminView, xmaxView,
                               xmin, xmax, self._ongetValues())

                # Display the fitting value on the Fit Dialog
                self._onsetValues(cstA, cstB, errA, errB, chisqr)

    def _onsetValues(self, cstA, cstB, errA, errB, Chi):
        """
        Display  the value on fit Dialog
        """
        rg = None
        _diam = None
        self.tcA.SetValue(format_number(cstA))
        self.tcB.SetValue(format_number(cstB))
        self.tcErrA.SetValue(format_number(errA))
        self.tcErrB.SetValue(format_number(errB))
        self.tcChi.SetValue(format_number(Chi))
        if self.rg_on:
            if self.Rg_tctr.IsShown():
                rg = np.sqrt(-3 * float(cstA))
                value = format_number(rg)
                self.Rg_tctr.SetValue(value)
                if self.I0_tctr.IsShown():
                    val = np.exp(cstB)
                    self.I0_tctr.SetValue(format_number(val))
            if self.Rgerr_tctr.IsShown():
                if rg is not None and rg != 0:
                    value = format_number(3 * float(errA) / (2 * rg))
                else:
                    value = ''
                self.Rgerr_tctr.SetValue(value)
                if self.I0err_tctr.IsShown():
                    val = np.abs(np.exp(cstB) * errB)
                    self.I0err_tctr.SetValue(format_number(val))
            if self.Diameter_tctr.IsShown():
                rg = np.sqrt(-2 * float(cstA))
                _diam = 4 * np.sqrt(-float(cstA))
                value = format_number(_diam)
                self.Diameter_tctr.SetValue(value)
            if self.Diametererr_tctr.IsShown():
                if rg is not None and rg != 0:
                    value = format_number(8 * float(errA) / _diam)
                else:
                    value = ''
                self.Diametererr_tctr.SetValue(value)
            if self.RgQmin_tctr.IsShown():
                value = format_number(rg * self.floatInvTransform(self.mini))
                self.RgQmin_tctr.SetValue(value)
            if self.RgQmax_tctr.IsShown():
                value = format_number(rg * self.floatInvTransform(self.maxi))
                self.RgQmax_tctr.SetValue(value)

    def _ongetValues(self):
        """
        Display  the value on fit Dialog
        """
        return self.Avalue, self.Bvalue, self.ErrAvalue, \
                            self.ErrBvalue, self.Chivalue

    def _checkVal(self, usermin, usermax):
        """
        Ensure that fields parameter contains a min and a max value
        within x min and x max range
        """
        self.mini = float(self.xminFit.GetValue())
        self.maxi = float(self.xmaxFit.GetValue())
        flag = True
        try:
            mini = float(usermin.GetValue())
            maxi = float(usermax.GetValue())
            if mini < maxi:
                usermin.SetBackgroundColour(wx.WHITE)
                usermin.Refresh()
            else:
                flag = False
                usermin.SetBackgroundColour("pink")
                usermin.Refresh()
        except:
            # Check for possible values entered
            flag = False
            usermin.SetBackgroundColour("pink")
            usermin.Refresh()

        return flag

    def floatForwardTransform(self, x):
        """
        transform a float.
        """
        # TODO: refactor this with proper object-oriented design
        # This code stinks.
        if self.xLabel == "x":
            return transform.toX(x)
        if self.xLabel == "x^(2)":
            return transform.toX2(x)
        if self.xLabel == "ln(x)":
            return transform.toLogX(x)
        if self.xLabel == "log10(x)":
            return math.log10(x)

    def floatTransform(self, x):
        """
        transform a float.It is use to determine the x.
        View min and x.View max for values
        not in x
        """
        # TODO: refactor this with proper object-oriented design
        # This code stinks.
        if self.xLabel == "x":
            return transform.toX(x)
        if self.xLabel == "x^(2)":
            return transform.toX2(x)
        if self.xLabel == "ln(x)":
            return transform.toLogX(x)
        if self.xLabel == "log10(x)":
            if x > 0:
                return x
            else:
                raise ValueError("cannot compute log of a negative number")

    def floatInvTransform(self, x):
        """
        transform a float.It is used to determine the x.View min and x.View
        max for values not in x.  Also used to properly calculate RgQmin,
        RgQmax and to update qmin and qmax in the linear range boxes on the
        panel.

        """
        # TODO: refactor this. This is just a hack to make the
        # functionality work without rewritting the whole code
        # with good design (which really should be done...).
        if self.xLabel == "x":
            return x
        elif self.xLabel == "x^(2)":
            return math.sqrt(x)
        elif self.xLabel == "x^(4)":
            return math.sqrt(math.sqrt(x))
        elif self.xLabel == "log10(x)":
            return math.pow(10, x)
        elif self.xLabel == "ln(x)":
            return math.exp(x)
        elif self.xLabel == "log10(x^(4))":
            return math.sqrt(math.sqrt(math.pow(10, x)))
        return x

    def checkFitValues(self, item):
        """
            Check the validity of input values
        """
        flag = True
        value = item.GetValue()
        # Check for possible values entered
        if self.xLabel == "log10(x)":
            if float(value) > 0:
                item.SetBackgroundColour(wx.WHITE)
                item.Refresh()
            else:
                flag = False
                item.SetBackgroundColour("pink")
                item.Refresh()
        return flag

    def setFitRange(self, xmin, xmax, xminTrans, xmaxTrans):
        """
        Set fit parameters
        """
        self.xminFit.SetValue(format_number(xmin))
        self.xmaxFit.SetValue(format_number(xmax))

    def set_fit_region(self, xmin, xmax):
        """
        Set the fit region
        :param xmin: minimum x-value to be included in fit
        :param xmax: maximum x-value to be included in fit
        """
        # Check values
        try:
            float(xmin)
            float(xmax)
        except:
            msg = "LinearFit.set_fit_region: fit range must be floats"
            raise ValueError(msg)
        self.xminFit.SetValue(format_number(xmin))
        self.xmaxFit.SetValue(format_number(xmax))


class MyApp(wx.App):
    """
        Test application
    """
    def OnInit(self):
        """
            Test application initialization
        """
        wx.InitAllImageHandlers()
        plot = Theory1D([], [])
        dialog = LinearFit(parent=None, plottable=plot,
                           push_data=self.onFitDisplay,
                           transform=self.returnTrans,
                           title='Linear Fit')
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        return 1

    def onFitDisplay(self, tempx, tempy, xminView, xmaxView, xmin, xmax, func):
        """
            Test application dummy method
        """
        pass

    def returnTrans(self):
        """
            Test application dummy method
        """
        return '', '', 0, 0, 0, 0, 0

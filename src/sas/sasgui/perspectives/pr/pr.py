"""
    P(r) perspective for SasView
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################


# Make sure the option of saving each curve is available
# Use the I(q) curve as input and compare the output to P(r)


import sys
import wx
import logging
import time
import math
import numpy as np
import pylab
from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sascalc.pr.invertor import Invertor
from sas.sascalc.dataloader.loader import Loader
import sas.sascalc.dataloader

from .pr_widgets import load_error
from sas.sasgui.guiframe.plugin_base import PluginBase

logger = logging.getLogger(__name__)


PR_FIT_LABEL = r"$P_{fit}(r)$"
PR_LOADED_LABEL = r"$P_{loaded}(r)$"
IQ_DATA_LABEL = r"$I_{obs}(q)$"
IQ_FIT_LABEL = r"$I_{fit}(q)$"
IQ_SMEARED_LABEL = r"$I_{smeared}(q)$"
GROUP_ID_IQ_DATA = r"$I_{obs}(q)$"
GROUP_ID_PR_FIT = r"$P_{fit}(r)$"



class Plugin(PluginBase):
    """
        P(r) inversion perspective
    """
    DEFAULT_ALPHA = 0.0001
    DEFAULT_NFUNC = 10
    DEFAULT_DMAX = 140.0

    def __init__(self):
        PluginBase.__init__(self, name="Pr Inversion")
        ## Simulation window manager
        self.simview = None

        ## State data
        self.alpha = self.DEFAULT_ALPHA
        self.nfunc = self.DEFAULT_NFUNC
        self.max_length = self.DEFAULT_DMAX
        self.q_min = None
        self.q_max = None
        self.est_bck = False
        self.bck_val = 0
        self.slit_height = 0
        self.slit_width = 0
        ## Remember last plottable processed
        self.last_data = ""
        self._current_file_data = None
        ## Time elapsed for last computation [sec]
        # Start with a good default
        self.elapsed = 0.022
        self.iq_data_shown = False

        ## Current invertor
        self.invertor = None
        self.pr = None
        self.data_id = IQ_DATA_LABEL
        # Copy of the last result in case we need to display it.
        self._last_pr = None
        self._last_out = None
        self._last_cov = None
        ## Calculation thread
        self.calc_thread = None
        ## Estimation thread
        self.estimation_thread = None
        ## Result panel
        self.control_panel = None
        ## Currently views plottable
        self.current_plottable = None
        ## Number of P(r) points to display on the output plot
        self._pr_npts = 51
        self._normalize_output = False
        self._scale_output_unity = False

        ## List of added P(r) plots
        self._added_plots = {}
        self._default_Iq = {}
        self.list_plot_id = []

        # Associate the inversion state reader with .prv files
        from .inversion_state import Reader

        # Create a CanSAS/Pr reader
        self.state_reader = Reader(self.set_state)
        self._extensions = '.prv'
        l = Loader()
        l.associate_file_reader('.prv', self.state_reader)
        #l.associate_file_reader(".svs", self.state_reader)

        # Log startup
        logger.info("Pr(r) plug-in started")

    def delete_data(self, data_id):
        """
        delete the data association with prview
        """
        self.control_panel.clear_panel()

    def get_data(self):
        """
            Returns the current data
        """
        return self.current_plottable

    def set_state(self, state=None, datainfo=None):
        """
        Call-back method for the inversion state reader.
        This method is called when a .prv file is loaded.

        :param state: InversionState object
        :param datainfo: Data1D object [optional]

        """
        try:
            if datainfo.__class__.__name__ == 'list':
                if len(datainfo) >= 1:
                    data = datainfo[0]
                else:
                    data = None
            else:
                data = datainfo
            if data is None:
                msg = "Pr.set_state: datainfo parameter cannot "
                msg += "be None in standalone mode"
                raise RuntimeError(msg)

            # Ensuring that plots are coordinated correctly
            t = time.localtime(data.meta_data['prstate'].timestamp)
            time_str = time.strftime("%b %d %H:%M", t)

            # Check that no time stamp is already appended
            max_char = data.meta_data['prstate'].file.find("[")
            if max_char < 0:
                max_char = len(data.meta_data['prstate'].file)

            datainfo.meta_data['prstate'].file = \
                data.meta_data['prstate'].file[0:max_char]\
                + ' [' + time_str + ']'

            data.filename = data.meta_data['prstate'].file
            # TODO:
            #remove this call when state save all information about the gui data
            # such as ID , Group_ID, etc...
            #make self.current_plottable = datainfo directly
            self.current_plottable = self.parent.create_gui_data(data, None)
            self.current_plottable.group_id = data.meta_data['prstate'].file

            # Make sure the user sees the P(r) panel after loading
            #self.parent.set_perspective(self.perspective)
            self.on_perspective(event=None)
            # Load the P(r) results
            #state = self.state_reader.get_state()
            data_dict = {self.current_plottable.id:self.current_plottable}
            self.parent.add_data(data_list=data_dict)
            wx.PostEvent(self.parent, NewPlotEvent(plot=self.current_plottable,
                                                   title=self.current_plottable.title))
            self.control_panel.set_state(state)
        except:
            logger.error("prview.set_state: %s" % sys.exc_info()[1])


    def help(self, evt):
        """
        Show a general help dialog.

        :TODO: replace the text with a nice image

        """
        from .inversion_panel import HelpDialog
        dialog = HelpDialog(None, -1)
        if dialog.ShowModal() == wx.ID_OK:
            dialog.Destroy()
        else:
            dialog.Destroy()

    def _fit_pr(self, evt):
        """
        """
        # Generate P(r) for sphere
        radius = 60.0
        d_max = 2 * radius

        r = pylab.arange(0.01, d_max, d_max / 51.0)
        M = len(r)
        y = np.zeros(M)
        pr_err = np.zeros(M)

        total = 0.0
        for j in range(M):
            value = self.pr_theory(r[j], radius)
            total += value
            y[j] = value
            pr_err[j] = math.sqrt(y[j])

        y = y / total * d_max / len(r)

        # Perform fit
        pr = Invertor()
        pr.d_max = d_max
        pr.alpha = 0
        pr.x = r
        pr.y = y
        pr.err = pr_err
        out, cov = pr.pr_fit()
        for i in range(len(out)):
            print("%g +- %g" % (out[i], math.sqrt(cov[i][i])))

        # Show input P(r)
        title = "Pr"
        new_plot = Data1D(pr.x, pr.y, dy=pr.err)
        new_plot.name = "P_{obs}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.group_id = "P_{obs}(r)"
        new_plot.id = "P_{obs}(r)"
        new_plot.title = title
        self.parent.update_theory(data_id=self.data_id, theory=new_plot)
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))

        # Show P(r) fit
        self.show_pr(out, pr)

        # Show I(q) fit
        q = pylab.arange(0.001, 0.1, 0.01 / 51.0)
        self.show_iq(out, pr, q)

    def show_shpere(self, x, radius=70.0, x_range=70.0):
        """
        """
        # Show P(r)
        y_true = np.zeros(len(x))

        sum_true = 0.0
        for i in range(len(x)):
            y_true[i] = self.pr_theory(x[i], radius)
            sum_true += y_true[i]

        y_true = y_true / sum_true * x_range / len(x)

        # Show the theory P(r)
        new_plot = Data1D(x, y_true)
        new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        new_plot.name = "P_{true}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.id = "P_{true}(r)"
        new_plot.group_id = "P_{true}(r)"
        self.parent.update_theory(data_id=self.data_id, theory=new_plot)
        #Put this call in plottables/guitools
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title="Sphere P(r)"))

    def get_npts(self):
        """
        Returns the number of points in the I(q) data
        """
        try:
            return len(self.pr.x)
        except:
            return 0

    def show_iq(self, out, pr, q=None):
        """
            Display computed I(q)
        """
        qtemp = pr.x
        if q is not None:
            qtemp = q

        # Make a plot
        maxq = -1
        for q_i in qtemp:
            if q_i > maxq:
                maxq = q_i

        minq = 0.001

        # Check for user min/max
        if pr.q_min is not None:
            minq = pr.q_min
        if pr.q_max is not None:
            maxq = pr.q_max

        x = pylab.arange(minq, maxq, maxq / 301.0)
        y = np.zeros(len(x))
        err = np.zeros(len(x))
        for i in range(len(x)):
            value = pr.iq(out, x[i])
            y[i] = value
            try:
                err[i] = math.sqrt(math.fabs(value))
            except:
                err[i] = 1.0
                print("Error getting error", value, x[i])

        new_plot = Data1D(x, y)
        new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        new_plot.name = IQ_FIT_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        title = "I(q)"
        new_plot.title = title

        # If we have a group ID, use it
        if 'plot_group_id' in pr.info:
            new_plot.group_id = pr.info["plot_group_id"]
        new_plot.id = IQ_FIT_LABEL
        self.parent.update_theory(data_id=self.data_id, theory=new_plot)

        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))

        # If we have used slit smearing, plot the smeared I(q) too
        if pr.slit_width > 0 or pr.slit_height > 0:
            x = pylab.arange(minq, maxq, maxq / 301.0)
            y = np.zeros(len(x))
            err = np.zeros(len(x))
            for i in range(len(x)):
                value = pr.iq_smeared(out, x[i])
                y[i] = value
                try:
                    err[i] = math.sqrt(math.fabs(value))
                except:
                    err[i] = 1.0
                    print("Error getting error", value, x[i])

            new_plot = Data1D(x, y)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            new_plot.name = IQ_SMEARED_LABEL
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
            # If we have a group ID, use it
            if 'plot_group_id' in pr.info:
                new_plot.group_id = pr.info["plot_group_id"]
            new_plot.id = IQ_SMEARED_LABEL
            new_plot.title = title
            self.parent.update_theory(data_id=self.data_id, theory=new_plot)
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))

    def _on_pr_npts(self, evt):
        """
        Redisplay P(r) with a different number of points
        """
        from .inversion_panel import PrDistDialog
        dialog = PrDistDialog(None, -1)
        dialog.set_content(self._pr_npts)
        if dialog.ShowModal() == wx.ID_OK:
            self._pr_npts = dialog.get_content()
            dialog.Destroy()
            self.show_pr(self._last_out, self._last_pr, self._last_cov)
        else:
            dialog.Destroy()


    def show_pr(self, out, pr, cov=None):
        """
        """
        # Show P(r)
        x = pylab.arange(0.0, pr.d_max, pr.d_max / self._pr_npts)

        y = np.zeros(len(x))
        dy = np.zeros(len(x))
        y_true = np.zeros(len(x))

        total = 0.0
        pmax = 0.0
        cov2 = np.ascontiguousarray(cov)

        for i in range(len(x)):
            if cov2 is None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov2, x[i])
            total += value * pr.d_max / len(x)

            # keep track of the maximum P(r) value
            if value > pmax:
                pmax = value

            y[i] = value

        if self._normalize_output == True:
            y = y / total
            dy = dy / total
        elif self._scale_output_unity == True:
            y = y / pmax
            dy = dy / pmax

        if cov2 is None:
            new_plot = Data1D(x, y)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        else:
            new_plot = Data1D(x, y, dy=dy)
        new_plot.name = PR_FIT_LABEL
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
        new_plot.title = "P(r) fit"
        new_plot.id = PR_FIT_LABEL
        # Make sure that the plot is linear
        new_plot.xtransform = "x"
        new_plot.ytransform = "y"
        new_plot.group_id = GROUP_ID_PR_FIT
        self.parent.update_theory(data_id=self.data_id, theory=new_plot)
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="P(r) fit"))
        return x, pr.d_max

    def load(self, data):
        """
        Load data. This will eventually be replaced
        by our standard DataLoader class.
        """
        class FileData(object):
            x = None
            y = None
            err = None
            path = None

            def __init__(self, path):
                self.path = path

        self._current_file_data = FileData(data.path)

        # Use data loader to load file
        dataread = data
        # Notify the user if we could not read the file
        if dataread is None:
            raise RuntimeError("Invalid data")

        x = None
        y = None
        err = None
        if dataread.__class__.__name__ == 'Data1D':
            x = dataread.x
            y = dataread.y
            err = dataread.dy
        else:
            if isinstance(dataread, list) and len(dataread) > 0:
                x = dataread[0].x
                y = dataread[0].y
                err = dataread[0].dy
                msg = "PrView only allows a single data set at a time. "
                msg += "Only the first data set was loaded."
                wx.PostEvent(self.parent, StatusEvent(status=msg))
            else:
                if dataread is None:
                    return x, y, err
                raise RuntimeError("This tool can only read 1D data")

        self._current_file_data.x = x
        self._current_file_data.y = y
        self._current_file_data.err = err
        return x, y, err

    def load_columns(self, path="sphere_60_q0_2.txt"):
        """
        Load 2- or 3- column ascii
        """
        # Read the data from the data file
        data_x = np.zeros(0)
        data_y = np.zeros(0)
        data_err = np.zeros(0)
        scale = None
        min_err = 0.0
        if path is not None:
            input_f = open(path, 'r')
            buff = input_f.read()
            lines = buff.split('\n')
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    if len(toks) > 2:
                        err = float(toks[2])
                    else:
                        if scale is None:
                            scale = 0.05 * math.sqrt(y)
                            #scale = 0.05/math.sqrt(y)
                            min_err = 0.01 * y
                        err = scale * math.sqrt(y) + min_err
                        #err = 0

                    data_x = np.append(data_x, x)
                    data_y = np.append(data_y, y)
                    data_err = np.append(data_err, err)
                except:
                    logger.error(sys.exc_info()[1])

        if scale is not None:
            message = "The loaded file had no error bars, statistical errors are assumed."
            wx.PostEvent(self.parent, StatusEvent(status=message))
        else:
            wx.PostEvent(self.parent, StatusEvent(status=''))

        return data_x, data_y, data_err

    def load_abs(self, path):
        """
        Load an IGOR .ABS reduced file

        :param path: file path

        :return: x, y, err vectors

        """
        # Read the data from the data file
        data_x = np.zeros(0)
        data_y = np.zeros(0)
        data_err = np.zeros(0)
        scale = None
        min_err = 0.0

        data_started = False
        if path is not None:
            input_f = open(path, 'r')
            buff = input_f.read()
            lines = buff.split('\n')
            for line in lines:
                if data_started == True:
                    try:
                        toks = line.split()
                        x = float(toks[0])
                        y = float(toks[1])
                        if len(toks) > 2:
                            err = float(toks[2])
                        else:
                            if scale is None:
                                scale = 0.05 * math.sqrt(y)
                                #scale = 0.05/math.sqrt(y)
                                min_err = 0.01 * y
                            err = scale * math.sqrt(y) + min_err
                            #err = 0

                        data_x = np.append(data_x, x)
                        data_y = np.append(data_y, y)
                        data_err = np.append(data_err, err)
                    except:
                        logger.error(sys.exc_info()[1])
                elif line.find("The 6 columns") >= 0:
                    data_started = True

        if scale is not None:
            message = "The loaded file had no error bars, statistical errors are assumed."
            wx.PostEvent(self.parent, StatusEvent(status=message))
        else:
            wx.PostEvent(self.parent, StatusEvent(status=''))

        return data_x, data_y, data_err

    def pr_theory(self, r, R):
        """
            Return P(r) of a sphere for a given R
            For test purposes
        """
        if r <= 2 * R:
            return 12.0 * ((0.5 * r / R) ** 2) * ((1.0 - 0.5 * r / R) ** 2) * (2.0 + 0.5 * r / R)
        else:
            return 0.0

    def get_context_menu(self, plotpanel=None):
        """
        Get the context menu items available for P(r)

        :param graph: the Graph object to which we attach the context menu

        :return: a list of menu items with call-back function

        """
        graph = plotpanel.graph
        # Look whether this Graph contains P(r) data
        if graph.selected_plottable not in plotpanel.plots:
            return []
        item = plotpanel.plots[graph.selected_plottable]
        if item.id == PR_FIT_LABEL:
            #add_data_hint = "Load a data file and display it on this plot"
            #["Add P(r) data",add_data_hint , self._on_add_data],
            change_n_hint = "Change the number of"
            change_n_hint += " points on the P(r) output"
            change_n_label = "Change number of P(r) points"
            m_list = [[change_n_label, change_n_hint, self._on_pr_npts]]

            if self._scale_output_unity or self._normalize_output:
                hint = "Let the output P(r) keep the scale of the data"
                m_list.append(["Disable P(r) scaling", hint,
                               self._on_disable_scaling])
            if not self._scale_output_unity:
                m_list.append(["Scale P_max(r) to unity",
                               "Scale P(r) so that its maximum is 1",
                               self._on_scale_unity])
            if not self._normalize_output:
                m_list.append(["Normalize P(r) to unity",
                               "Normalize the integral of P(r) to 1",
                               self._on_normalize])

            return m_list

        elif item.id in [PR_LOADED_LABEL, IQ_DATA_LABEL, IQ_FIT_LABEL, IQ_SMEARED_LABEL]:
            return []
        elif item.id == graph.selected_plottable:
            if issubclass(item.__class__, Data1D):
                return [["Compute P(r)",
                         "Compute P(r) from distribution",
                         self._on_context_inversion]]
        return []

    def _on_disable_scaling(self, evt):
        """
        Disable P(r) scaling

        :param evt: Menu event

        """
        self._normalize_output = False
        self._scale_output_unity = False
        self.show_pr(self._last_out, self._last_pr, self._last_cov)

        # Now replot the original added data
        for plot in self._added_plots:
            self._added_plots[plot].y = np.copy(self._default_Iq[plot])
            wx.PostEvent(self.parent,
                         NewPlotEvent(plot=self._added_plots[plot],
                                      title=self._added_plots[plot].name,
                                      update=True))

        # Need the update flag in the NewPlotEvent to protect against
        # the plot no longer being there...

    def _on_normalize(self, evt):
        """
        Normalize the area under the P(r) curve to 1.
        This operation is done for all displayed plots.

        :param evt: Menu event

        """
        self._normalize_output = True
        self._scale_output_unity = False

        self.show_pr(self._last_out, self._last_pr, self._last_cov)

        # Now scale the added plots too
        for plot in self._added_plots:
            total = np.sum(self._added_plots[plot].y)
            npts = len(self._added_plots[plot].x)
            total *= self._added_plots[plot].x[npts - 1] / npts
            y = self._added_plots[plot].y / total

            new_plot = Data1D(self._added_plots[plot].x, y)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            new_plot.group_id = self._added_plots[plot].group_id
            new_plot.id = self._added_plots[plot].id
            new_plot.title = self._added_plots[plot].title
            new_plot.name = self._added_plots[plot].name
            new_plot.xaxis("\\rm{r}", 'A')
            new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
            self.parent.update_theory(data_id=self.data_id, theory=new_plot)
            wx.PostEvent(self.parent,
                         NewPlotEvent(plot=new_plot, update=True,
                                      title=self._added_plots[plot].name))

    def _on_scale_unity(self, evt):
        """
        Scale the maximum P(r) value on each displayed plot to 1.

        :param evt: Menu event

        """
        self._scale_output_unity = True
        self._normalize_output = False

        self.show_pr(self._last_out, self._last_pr, self._last_cov)

        # Now scale the added plots too
        for plot in self._added_plots:
            _max = 0
            for y in self._added_plots[plot].y:
                if y > _max:
                    _max = y
            y = self._added_plots[plot].y / _max

            new_plot = Data1D(self._added_plots[plot].x, y)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            new_plot.name = self._added_plots[plot].name
            new_plot.xaxis("\\rm{r}", 'A')
            new_plot.yaxis("\\rm{P(r)} ", "cm^{-3}")
            self.parent.update_theory(data_id=self.data_id, theory=new_plot)
            wx.PostEvent(self.parent,
                         NewPlotEvent(plot=new_plot, update=True,
                                      title=self._added_plots[plot].name))

    def start_thread(self):
        """
            Start a calculation thread
        """
        from .pr_thread import CalcPr

        # If a thread is already started, stop it
        if self.calc_thread is not None and self.calc_thread.isrunning():
            self.calc_thread.stop()
            ## stop just raises the flag -- the thread is supposed to
            ## then kill itself. In August 2014 it was shown that this is
            ## incorrectly handled by fitting.py and a fix implemented.
            ## It is not clear whether it is properly used here, but the
            ## "fix" of waiting for the previous thread to end breaks the
            ## pr perspective completely as it causes an infinite loop.
            ## Thus it is likely the threading is bing properly handled.
            ## While the "fix" is no longer implemented the comment is
            ## left here till somebody ascertains that in fact the threads
            ## are being properly handled.
            ##
            ##    -PDB January 25, 2015

        pr = self.pr.clone()
        self.calc_thread = CalcPr(pr, self.nfunc,
                                  error_func=self._thread_error,
                                  completefn=self._completed, updatefn=None)
        self.calc_thread.queue()
        self.calc_thread.ready(2.5)

    def _thread_error(self, error):
        """
            Call-back method for calculation errors
        """
        wx.PostEvent(self.parent, StatusEvent(status=error))

    def _estimate_completed(self, alpha, message, elapsed):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param elapsed: computation time

        """
        # Save useful info
        self.elapsed = elapsed
        self.control_panel.alpha_estimate = alpha
        if message is not None:
            wx.PostEvent(self.parent, StatusEvent(status=str(message)))
        self.perform_estimateNT()

    def _estimateNT_completed(self, nterms, alpha, message, elapsed):
        """
        Parameter estimation completed,
        display the results to the user

        :param alpha: estimated best alpha
        :param nterms: estimated number of terms
        :param elapsed: computation time

        """
        # Save useful info
        self.elapsed = elapsed
        self.control_panel.nterms_estimate = nterms
        self.control_panel.alpha_estimate = alpha
        if message is not None:
            wx.PostEvent(self.parent, StatusEvent(status=str(message)))

    def _completed(self, out, cov, pr, elapsed):
        """
        wxCallAfter Method called with the results when the inversion
        is done

        :param out: output coefficient for the base functions
        :param cov: covariance matrix
        :param pr: Invertor instance
        :param elapsed: time spent computing
        """
        # Ensure hat you have all inputs are ready at the time call happens:
        # Without CallAfter, it will freeze with wx >= 2.9.
        wx.CallAfter(self._completed_call, out, cov, pr, elapsed)

    def _completed_call(self, out, cov, pr, elapsed):
        """
        Method called with the results when the inversion
        is done

        :param out: output coefficient for the base functions
        :param cov: covariance matrix
        :param pr: Invertor instance
        :param elapsed: time spent computing

        """
        # Save useful info
        self.elapsed = elapsed
        # Keep a copy of the last result
        self._last_pr = pr.clone()
        self._last_out = out
        self._last_cov = cov

        # Save Pr invertor
        self.pr = pr
        cov = np.ascontiguousarray(cov)

        # Show result on control panel
        self.control_panel.chi2 = pr.chi2
        self.control_panel.elapsed = elapsed
        self.control_panel.oscillation = pr.oscillations(out)
        self.control_panel.positive = pr.get_positive(out)
        self.control_panel.pos_err = pr.get_pos_err(out, cov)
        self.control_panel.rg = pr.rg(out)
        self.control_panel.iq0 = pr.iq0(out)
        self.control_panel.bck = pr.background
        self.control_panel.bck_input.SetValue("{:.2g}".format(pr.background))

        # Show I(q) fit
        self.show_iq(out, self.pr)

        # Show P(r) fit
        self.show_pr(out, self.pr, cov)

    def show_data(self, path=None, data=None, reset=False):
        """
        Show data read from a file

        :param path: file path
        :param reset: if True all other plottables will be cleared

        """
        #if path is not None:
        if data is not None:
            try:
                pr = self._create_file_pr(data)
            except:
                status = "Problem reading data: %s" % sys.exc_info()[1]
                wx.PostEvent(self.parent, StatusEvent(status=status))
                raise RuntimeError(status)

            # If the file contains nothing, just return
            if pr is None:
                raise RuntimeError("Loaded data is invalid")

            self.pr = pr

        # Make a plot of I(q) data
        if self.pr.err is None:
            new_plot = Data1D(self.pr.x, self.pr.y)
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        else:
            new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
        new_plot.name = IQ_DATA_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        new_plot.interactive = True
        new_plot.group_id = GROUP_ID_IQ_DATA
        new_plot.id = self.data_id
        new_plot.title = "I(q)"
        wx.PostEvent(self.parent,
                     NewPlotEvent(plot=new_plot, title="I(q)", reset=reset))

        self.current_plottable = new_plot
        # Get Q range
        self.control_panel.q_min = min(self.pr.x)
        self.control_panel.q_max = max(self.pr.x)

    def save_data(self, filepath, prstate=None):
        """
        Save data in provided state object.

        :TODO: move the state code away from inversion_panel and move it here.
                Then remove the "prstate" input and make this method private.

        :param filepath: path of file to write to
        :param prstate: P(r) inversion state

        """
        #TODO: do we need this or can we use DataLoader.loader.save directly?

        # Add output data and coefficients to state
        prstate.coefficients = self._last_out
        prstate.covariance = self._last_cov

        # Write the output to file
        # First, check that the data is of the right type
        if issubclass(self.current_plottable.__class__,
                      sas.sascalc.dataloader.data_info.Data1D):
            self.state_reader.write(filepath, self.current_plottable, prstate)
        else:
            msg = "pr.save_data: the data being saved is not a"
            msg += " sas.data_info.Data1D object"
            raise RuntimeError(msg)

    def setup_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None,
                             est_bck=False, bck_val=0, height=0, width=0):
        """
            Set up inversion from plotted data
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.est_bck = est_bck
        self.bck_val = bck_val
        self.slit_height = height
        self.slit_width = width

        try:
            pr = self._create_plot_pr()
            if pr is not None:
                self.pr = pr
                self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_info()[1]))

    def estimate_plot_inversion(self, alpha, nfunc, d_max,
                                q_min=None, q_max=None,
                                est_bck=False, bck_val=0, height=0, width=0):
        """
            Estimate parameters from plotted data
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.est_bck = est_bck
        self.bck_val = bck_val
        self.slit_height = height
        self.slit_width = width

        try:
            pr = self._create_plot_pr()
            if pr is not None:
                self.pr = pr
                self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_info()[1]))

    def _create_plot_pr(self, estimate=False):
        """
        Create and prepare invertor instance from
        a plottable data set.

        :param path: path of the file to read in

        """
        # Sanity check
        if self.current_plottable is None:
            msg = "Please load a valid data set before proceeding."
            wx.PostEvent(self.parent, StatusEvent(status=msg))
            return None

        # Get the data from the chosen data set and perform inversion
        pr = Invertor()
        pr.d_max = self.max_length
        pr.alpha = self.alpha
        pr.q_min = self.q_min
        pr.q_max = self.q_max
        pr.x = self.current_plottable.x
        pr.y = self.current_plottable.y
        pr.est_bck = self.est_bck
        pr.slit_height = self.slit_height
        pr.slit_width = self.slit_width
        pr.background = self.bck_val

        # Keep track of the plot window title to ensure that
        # we can overlay the plots
        pr.info["plot_group_id"] = self.current_plottable.group_id

        # Fill in errors if none were provided
        err = self.current_plottable.dy
        all_zeros = True
        if err is None:
            err = np.zeros(len(pr.y))
        else:
            for i in range(len(err)):
                if err[i] > 0:
                    all_zeros = False

        if all_zeros:
            scale = None
            min_err = 0.0
            for i in range(len(pr.y)):
                # Scale the error so that we can fit over several decades of Q
                if scale is None:
                    scale = 0.05 * math.sqrt(pr.y[i])
                    min_err = 0.01 * pr.y[i]
                err[i] = scale * math.sqrt(math.fabs(pr.y[i])) + min_err
            message = "The loaded file had no error bars, "
            message += "statistical errors are assumed."
            wx.PostEvent(self.parent, StatusEvent(status=message))

        pr.err = err

        return pr

    def setup_file_inversion(self, alpha, nfunc, d_max, data,
                             path=None, q_min=None, q_max=None,
                             bck=False, height=0, width=0):
        """
            Set up inversion
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.est_bck = bck
        self.slit_height = height
        self.slit_width = width

        try:
            pr = self._create_file_pr(data)
            if pr is not None:
                self.pr = pr
                self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_info()[1]))

    def estimate_file_inversion(self, alpha, nfunc, d_max, data,
                                path=None, q_min=None, q_max=None,
                                bck=False, height=0, width=0):
        """
            Estimate parameters for inversion
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.est_bck = bck
        self.slit_height = height
        self.slit_width = width

        try:
            pr = self._create_file_pr(data)
            if pr is not None:
                self.pr = pr
                self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_info()[1]))

    def _create_file_pr(self, data):
        """
        Create and prepare invertor instance from
        a file data set.

        :param path: path of the file to read in

        """
        # Reset the status bar so that we don't get mixed up
        # with old messages.
        #TODO: refactor this into a proper status handling
        wx.PostEvent(self.parent, StatusEvent(status=''))
        try:
            class FileData(object):
                x = None
                y = None
                err = None
                path = None
                def __init__(self, path):
                    self.path = path

            self._current_file_data = FileData(data.path)
            self._current_file_data.x = data.x
            self._current_file_data.y = data.y
            self._current_file_data.err = data.dy
            x, y, err = data.x, data.y, data.dy
        except:
            load_error(sys.exc_info()[1])
            return None

        # If the file contains no data, just return
        if x is None or len(x) == 0:
            load_error("The loaded file contains no data")
            return None

        # If we have not errors, add statistical errors
        if y is not None:
            if err is None or np.all(err) == 0:
                err = np.zeros(len(y))
                scale = None
                min_err = 0.0
                for i in range(len(y)):
                    # Scale the error so that we can fit over several decades of Q
                    if scale is None:
                        scale = 0.05 * math.sqrt(y[i])
                        min_err = 0.01 * y[i]
                    err[i] = scale * math.sqrt(math.fabs(y[i])) + min_err
                message = "The loaded file had no error bars, "
                message += "statistical errors are assumed."
                wx.PostEvent(self.parent, StatusEvent(status=message))

        try:
            # Get the data from the chosen data set and perform inversion
            pr = Invertor()
            pr.d_max = self.max_length
            pr.alpha = self.alpha
            pr.q_min = self.q_min
            pr.q_max = self.q_max
            pr.x = x
            pr.y = y
            pr.err = err
            pr.est_bck = self.est_bck
            pr.slit_height = self.slit_height
            pr.slit_width = self.slit_width
            return pr
        except:
            load_error(sys.exc_info()[1])
        return None

    def perform_estimate(self):
        """
            Perform parameter estimation
        """
        from .pr_thread import EstimatePr

        # If a thread is already started, stop it
        if self.estimation_thread is not None and \
            self.estimation_thread.isrunning():
            self.estimation_thread.stop()
            ## stop just raises the flag -- the thread is supposed to
            ## then kill itself. In August 2014 it was shown that this is
            ## incorrectly handled by fitting.py and a fix implemented.
            ## It is not clear whether it is properly used here, but the
            ## "fix" of waiting for the previous thread to end breaks the
            ## pr perspective completely as it causes an infinite loop.
            ## Thus it is likely the threading is bing properly handled.
            ## While the "fix" is no longer implemented the comment is
            ## left here till somebody ascertains that in fact the threads
            ## are being properly handled.
            ##
            ##    -PDB January 25, 2015
        pr = self.pr.clone()
        self.estimation_thread = EstimatePr(pr, self.nfunc,
                                            error_func=self._thread_error,
                                            completefn=self._estimate_completed,
                                            updatefn=None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)

    def perform_estimateNT(self):
        """
            Perform parameter estimation
        """
        from .pr_thread import EstimateNT

        # If a thread is already started, stop it
        if self.estimation_thread is not None and self.estimation_thread.isrunning():
            self.estimation_thread.stop()
            ## stop just raises the flag -- the thread is supposed to
            ## then kill itself. In August 2014 it was shown that this is
            ## incorrectly handled by fitting.py and a fix implemented.
            ## It is not clear whether it is properly used here, but the
            ## "fix" of waiting for the previous thread to end breaks the
            ## pr perspective completely as it causes an infinite loop.
            ## Thus it is likely the threading is bing properly handled.
            ## While the "fix" is no longer implemented the comment is
            ## left here till somebody ascertains that in fact the threads
            ## are being properly handled.
            ##
            ##    -PDB January 25, 2015
        pr = self.pr.clone()
        # Skip the slit settings for the estimation
        # It slows down the application and it doesn't change the estimates
        pr.slit_height = 0.0
        pr.slit_width = 0.0
        self.estimation_thread = EstimateNT(pr, self.nfunc,
                                            error_func=self._thread_error,
                                            completefn=self._estimateNT_completed,
                                            updatefn=None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)

    def perform_inversion(self):
        """
            Perform inversion
        """
        self.start_thread()

    def _on_context_inversion(self, event):
        """
            Call-back method for plot context menu
        """
        panel = event.GetEventObject()
        Plugin.on_perspective(self, event=event)

        # If we have more than one displayed plot, make the user choose
        if len(panel.plots) >= 1 and \
            panel.graph.selected_plottable in panel.plots:
            dataset = panel.plots[panel.graph.selected_plottable].name
        else:
            logger.info("Prview Error: No data is available")
            return

        # Store a reference to the current plottable
        # If we have a suggested value, use it.
        try:
            estimate = float(self.control_panel.alpha_estimate)
            self.control_panel.alpha = estimate
        except:
            self.control_panel.alpha = self.alpha
            logger.info("Prview :Alpha Not estimate yet")
        try:
            estimate = int(self.control_panel.nterms_estimate)
            self.control_panel.nfunc = estimate
        except:
            self.control_panel.nfunc = self.nfunc
            logger.info("Prview : ntemrs Not estimate yet")

        self.current_plottable = panel.plots[panel.graph.selected_plottable]
        self.set_data([self.current_plottable])
        self.control_panel.plotname = dataset
        #self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        #self.parent.set_perspective(self.perspective)
        self.control_panel._on_invert(None)

    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        from .inversion_panel import InversionControl

        self.parent = parent
        self.frame = MDIFrame(self.parent, None, 'None', (100, 200))
        self.control_panel = InversionControl(self.frame, -1,
                                              style=wx.RAISED_BORDER)
        self.frame.set_panel(self.control_panel)
        self._frame_set_helper()
        self.control_panel.set_manager(self)
        self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        self.control_panel.alpha = self.alpha
        self.perspective = []
        self.perspective.append(self.control_panel.window_name)

        return [self.control_panel]

    def set_data(self, data_list=None):
        """
        receive a list of data to compute pr
        """
        if data_list is None:
            data_list = []
        if len(data_list) >= 1:
            if len(data_list) == 1:
                data = data_list[0]
            else:
                data_1d_list = []
                data_2d_list = []
                error_msg = ""
                # separate data into data1d and data2d list
                for data in data_list:
                    if data is not None:
                        if issubclass(data.__class__, Data1D):
                            data_1d_list.append(data)
                        else:
                            error_msg += " %s type %s \n" % (str(data.name),
                                                             str(data.__class__.__name__))
                            data_2d_list.append(data)
                if len(data_2d_list) > 0:
                    msg = "PrView does not support the following data types:\n"
                    msg += error_msg
                if len(data_1d_list) == 0:
                    wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                    return
                msg = "Prview does not allow multiple data!\n"
                msg += "Please select one.\n"
                if len(data_list) > 1:
                    from .pr_widgets import DataDialog
                    dlg = DataDialog(data_list=data_1d_list, text=msg)
                    if dlg.ShowModal() == wx.ID_OK:
                        data = dlg.get_data()
                    else:
                        data = None
                    dlg.Destroy()
            if data is None:
                msg += "PrView receives no data. \n"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
                return
            if issubclass(data.__class__, Data1D):
                try:
                    wx.PostEvent(self.parent,
                                 NewPlotEvent(action='remove',
                                              group_id=GROUP_ID_IQ_DATA,
                                              id=self.data_id))
                    self.data_id = data.id
                    self.control_panel._change_file(evt=None, data=data)
                except:
                    msg = "Prview Set_data: " + str(sys.exc_info()[1])
                    wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
            else:
                msg = "Pr cannot be computed for data of "
                msg += "type %s" % (data_list[0].__class__.__name__)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info='error'))
        else:
            msg = "Pr contain no data"
            wx.PostEvent(self.parent, StatusEvent(status=msg, info='warning'))

    def post_init(self):
        """
            Post initialization call back to close the loose ends
            [Somehow openGL needs this call]
        """
        pass

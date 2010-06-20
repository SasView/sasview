
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

import os
import sys
import wx
import logging
import time
from sans.guiframe.dataFitting import Data1D, Theory1D
from sans.guicomm.events import NewPlotEvent, StatusEvent    
import math, numpy
from sans.pr.invertor import Invertor
from DataLoader.loader import Loader
import DataLoader
from sans.guiframe.data_loader import load_error 

import copy

PR_FIT_LABEL       = r"$P_{fit}(r)$"
PR_LOADED_LABEL    = r"$P_{loaded}(r)$"
IQ_DATA_LABEL      = r"$I_{obs}(q)$"
IQ_FIT_LABEL       = r"$I_{fit}(q)$"
IQ_SMEARED_LABEL   = r"$I_{smeared}(q)$"

import wx.lib
(NewPrFileEvent, EVT_PR_FILE) = wx.lib.newevent.NewEvent()


class Plugin:
    """
    """
    DEFAULT_ALPHA = 0.0001
    DEFAULT_NFUNC = 10
    DEFAULT_DMAX  = 140.0
    
    def __init__(self, standalone=True):
        """
        """
        ## Plug-in name
        self.sub_menu = "Pr inversion"
        
        ## Reference to the parent window
        self.parent = None
        
        ## Simulation window manager
        self.simview = None
        
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        
        ## State data
        self.alpha      = self.DEFAULT_ALPHA
        self.nfunc      = self.DEFAULT_NFUNC
        self.max_length = self.DEFAULT_DMAX
        self.q_min      = None
        self.q_max      = None
        self.has_bck    = False
        self.slit_height = 0
        self.slit_width  = 0
        ## Remember last plottable processed
        self.last_data  = "sphere_60_q0_2.txt"
        self._current_file_data = None
        ## Time elapsed for last computation [sec]
        # Start with a good default
        self.elapsed = 0.022
        self.iq_data_shown = False
        
        ## Current invertor
        self.invertor    = None
        self.pr          = None
        # Copy of the last result in case we need to display it.
        self._last_pr    = None
        self._last_out   = None
        self._last_cov   = None
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
        ## Flag to let the plug-in know that it is running standalone
        self.standalone = standalone
        self._normalize_output = False
        self._scale_output_unity = False
        
        ## List of added P(r) plots
        self._added_plots = {}
        self._default_Iq  = {}
        
        # Associate the inversion state reader with .prv files
        from DataLoader.loader import Loader
        from inversion_state import Reader
         
        # Create a CanSAS/Pr reader
        self.state_reader = Reader(self.set_state)
        l = Loader()
        l.associate_file_reader('.prv', self.state_reader)
                
        # Log startup
        logging.info("Pr(r) plug-in started")
        
    def set_state(self, state, datainfo=None):
        """
        Call-back method for the inversion state reader.
        This method is called when a .prv file is loaded.
        
        :param state: InversionState object
        :param datainfo: Data1D object [optional]
        
        """
        try:
            if datainfo is None:
                raise RuntimeError, "Pr.set_state: datainfo parameter cannot be None in standalone mode"

            # Ensuring that plots are coordinated correctly
            t = time.localtime(datainfo.meta_data['prstate'].timestamp)
            time_str = time.strftime("%b %d %H:%M", t)
            
            # Check that no time stamp is already appended
            max_char = datainfo.meta_data['prstate'].file.find("[")
            if max_char < 0:
                max_char = len(datainfo.meta_data['prstate'].file)
            
            datainfo.meta_data['prstate'].file = datainfo.meta_data['prstate'].file[0:max_char] +' [' + time_str + ']'
            datainfo.filename = datainfo.meta_data['prstate'].file
                
            self.current_plottable = datainfo
            self.current_plottable.group_id = datainfo.meta_data['prstate'].file
            
            # Load the P(r) results
            self.control_panel.set_state(state)
                        
            # Make sure the user sees the P(r) panel after loading
            self.parent.set_perspective(self.perspective)            

        except:
            logging.error("prview.set_state: %s" % sys.exc_value)

    def populate_menu(self, id, owner):
        """
        Create a menu for the plug-in
        """
        return []
    
    def help(self, evt):
        """
        Show a general help dialog. 
        
        :TODO: replace the text with a nice image
        
        """
        from inversion_panel import HelpDialog
        dialog = HelpDialog(None, -1)
        if dialog.ShowModal() == wx.ID_OK:
            dialog.Destroy()
        else:
            dialog.Destroy()
    
    def _fit_pr(self, evt):
        """
        """
        from sans.pr.invertor import Invertor
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from danse.common.plottools import Data1D, Theory1D
        
        # Generate P(r) for sphere
        radius = 60.0
        d_max  = 2*radius
        
        r = pylab.arange(0.01, d_max, d_max/51.0)
        M = len(r)
        y = numpy.zeros(M)
        pr_err = numpy.zeros(M)
        
        sum = 0.0
        for j in range(M):
            value = self.pr_theory(r[j], radius)
            sum += value
            y[j] = value
            pr_err[j] = math.sqrt(y[j])

        y = y/sum*d_max/len(r)

        # Perform fit
        pr = Invertor()
        pr.d_max = d_max
        pr.alpha = 0
        pr.x = r
        pr.y = y
        pr.err = pr_err
        out, cov = pr.pr_fit()
        for i in range(len(out)):
            print "%g +- %g" % (out[i], math.sqrt(cov[i][i]))

        # Show input P(r)
        new_plot = Data1D(pr.x, pr.y, dy=pr.err)
        new_plot.name = "P_{obs}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Pr"))

        # Show P(r) fit
        self.show_pr(out, pr)
        
        # Show I(q) fit
        q = pylab.arange(0.001, 0.1, 0.01/51.0)
        self.show_iq(out, pr, q)
        
    def show_shpere(self, x, radius=70.0, x_range=70.0):
        """
        """
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from danse.common.plottools import Data1D, Theory1D
        # Show P(r)
        y_true = numpy.zeros(len(x))

        sum_true = 0.0
        for i in range(len(x)):
            y_true[i] = self.pr_theory(x[i], radius)            
            sum_true += y_true[i]
            
        y_true = y_true/sum_true*x_range/len(x)
        
        # Show the theory P(r)
        new_plot = Theory1D(x, y_true)
        new_plot.name = "P_{true}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
        
        
        #Put this call in plottables/guitools    
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Sphere P(r)"))
        
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
        """
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from danse.common.plottools import Data1D, Theory1D

        qtemp = pr.x
        if not q==None:
            qtemp = q

        # Make a plot
        maxq = -1
        for q_i in qtemp:
            if q_i>maxq:
                maxq=q_i
                
        minq = 0.001
        
        # Check for user min/max
        if not pr.q_min==None:
            minq = pr.q_min
        if not pr.q_max==None:
            maxq = pr.q_max
                
        x = pylab.arange(minq, maxq, maxq/301.0)
        y = numpy.zeros(len(x))
        err = numpy.zeros(len(x))
        for i in range(len(x)):
            value = pr.iq(out, x[i])
            y[i] = value
            try:
                err[i] = math.sqrt(math.fabs(value))
            except:
                err[i] = 1.0
                print "Error getting error", value, x[i]
                
        new_plot = Theory1D(x, y)
        new_plot.name = IQ_FIT_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        
        title = "I(q)"
        # If we have a group ID, use it
        if pr.info.has_key("plot_group_id"):
            new_plot.group_id = pr.info["plot_group_id"]
            title = pr.info["plot_group_id"]
            
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))
        
        # If we have used slit smearing, plot the smeared I(q) too
        if pr.slit_width>0 or pr.slit_height>0:
            x = pylab.arange(minq, maxq, maxq/301.0)
            y = numpy.zeros(len(x))
            err = numpy.zeros(len(x))
            for i in range(len(x)):
                value = pr.iq_smeared(out, x[i])
                y[i] = value
                try:
                    err[i] = math.sqrt(math.fabs(value))
                except:
                    err[i] = 1.0
                    print "Error getting error", value, x[i]
                    
            new_plot = Theory1D(x, y)
            new_plot.name = IQ_SMEARED_LABEL
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
            # If we have a group ID, use it
            if pr.info.has_key("plot_group_id"):
                new_plot.group_id = pr.info["plot_group_id"]
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))
        
        
    def _on_pr_npts(self, evt):
        """
        Redisplay P(r) with a different number of points
        """   
        from inversion_panel import PrDistDialog
        dialog = PrDistDialog(None, -1)
        dialog.set_content(self._pr_npts)
        if dialog.ShowModal() == wx.ID_OK:
            self._pr_npts= dialog.get_content()
            dialog.Destroy()
            self.show_pr(self._last_out, self._last_pr, self._last_cov)
        else:
            dialog.Destroy()
        
        
    def show_pr(self, out, pr, cov=None):
        """
        """
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from danse.common.plottools import Data1D, Theory1D
        
        # Show P(r)
        x = pylab.arange(0.0, pr.d_max, pr.d_max/self._pr_npts)
    
        y = numpy.zeros(len(x))
        dy = numpy.zeros(len(x))
        y_true = numpy.zeros(len(x))

        sum = 0.0
        pmax = 0.0
        cov2 = numpy.ascontiguousarray(cov)
        
        for i in range(len(x)):
            if cov2==None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov2, x[i])
            sum += value*pr.d_max/len(x)
            
            # keep track of the maximum P(r) value
            if value>pmax:
                pmax = value
                
            y[i] = value
                
        if self._normalize_output==True:
            y = y/sum
            dy = dy/sum
        elif self._scale_output_unity==True:
            y = y/pmax
            dy = dy/pmax
        
        if cov2==None:
            new_plot = Theory1D(x, y)
        else:
            new_plot = Data1D(x, y, dy=dy)
        new_plot.name = PR_FIT_LABEL
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
        # Make sure that the plot is linear
        new_plot.xtransform="x"
        new_plot.ytransform="y"                 
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="P(r) fit"))
        
        return x, pr.d_max
        
        
    def choose_file(self, path=None):
        """
        """
        #TODO: this should be in a common module
        return self.parent.choose_file(path=path)
                
                
    def load(self, path):
        """
        Load data. This will eventually be replaced
        by our standard DataLoader class.
        """
        class FileData:
            x = None
            y = None
            err = None
            path = None
            
            def __init__(self, path):
                self.path = path
                
        self._current_file_data = FileData(path)
        
        # Use data loader to load file
        dataread = Loader().load(path)
        
        # Notify the user if we could not read the file
        if dataread is None:
            raise RuntimeError, "Invalid data"
            
        x = None
        y = None
        err = None
        if dataread.__class__.__name__ == 'Data1D':
            x = dataread.x
            y = dataread.y
            err = dataread.dy
        else:
            if isinstance(dataread, list) and len(dataread)>0:
                x = dataread[0].x
                y = dataread[0].y
                err = dataread[0].dy
                msg = "PrView only allows a single data set at a time. "
                msg += "Only the first data set was loaded." 
                wx.PostEvent(self.parent, StatusEvent(status=msg))
            else:
                if dataread is None:
                    return x, y, err
                raise RuntimeError, "This tool can only read 1D data"
        
        self._current_file_data.x = x
        self._current_file_data.y = y
        self._current_file_data.err = err
        return x, y, err
                
    def load_columns(self, path = "sphere_60_q0_2.txt"):
        """
        Load 2- or 3- column ascii
        """
        import numpy, math, sys
        # Read the data from the data file
        data_x   = numpy.zeros(0)
        data_y   = numpy.zeros(0)
        data_err = numpy.zeros(0)
        scale    = None
        min_err  = 0.0
        if not path == None:
            input_f = open(path,'r')
            buff    = input_f.read()
            lines   = buff.split('\n')
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    if len(toks)>2:
                        err = float(toks[2])
                    else:
                        if scale==None:
                            scale = 0.05*math.sqrt(y)
                            #scale = 0.05/math.sqrt(y)
                            min_err = 0.01*y
                        err = scale*math.sqrt(y)+min_err
                        #err = 0
                        
                    data_x = numpy.append(data_x, x)
                    data_y = numpy.append(data_y, y)
                    data_err = numpy.append(data_err, err)
                except:
                    pass
                   
        if not scale==None:
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
        import numpy, math, sys
        # Read the data from the data file
        data_x   = numpy.zeros(0)
        data_y   = numpy.zeros(0)
        data_err = numpy.zeros(0)
        scale    = None
        min_err  = 0.0
        
        data_started = False
        if not path == None:
            input_f = open(path,'r')
            buff    = input_f.read()
            lines   = buff.split('\n')
            for line in lines:
                if data_started==True:
                    try:
                        toks = line.split()
                        x = float(toks[0])
                        y = float(toks[1])
                        if len(toks)>2:
                            err = float(toks[2])
                        else:
                            if scale==None:
                                scale = 0.05*math.sqrt(y)
                                #scale = 0.05/math.sqrt(y)
                                min_err = 0.01*y
                            err = scale*math.sqrt(y)+min_err
                            #err = 0
                            
                        data_x = numpy.append(data_x, x)
                        data_y = numpy.append(data_y, y)
                        data_err = numpy.append(data_err, err)
                    except:
                        pass
                elif line.find("The 6 columns")>=0:
                    data_started = True      
                   
        if not scale==None:
            message = "The loaded file had no error bars, statistical errors are assumed."
            wx.PostEvent(self.parent, StatusEvent(status=message))
        else:
            wx.PostEvent(self.parent, StatusEvent(status=''))
                        
        return data_x, data_y, data_err     
        
    def pr_theory(self, r, R):
        """  
        """
        if r<=2*R:
            return 12.0* ((0.5*r/R)**2) * ((1.0-0.5*r/R)**2) * ( 2.0 + 0.5*r/R )
        else:
            return 0.0

    def get_context_menu(self, graph=None):
        """
        Get the context menu items available for P(r)
        
        :param graph: the Graph object to which we attach the context menu
        
        :return: a list of menu items with call-back function
        
        """
        # Look whether this Graph contains P(r) data
        #if graph.selected_plottable==IQ_DATA_LABEL:
        for item in graph.plottables:
            if item.name==PR_FIT_LABEL:
                m_list = [["Add P(r) data", "Load a data file and display it on this plot", self._on_add_data],
                       ["Change number of P(r) points", "Change the number of points on the P(r) output", self._on_pr_npts]]

                if self._scale_output_unity==True or self._normalize_output==True:
                    m_list.append(["Disable P(r) scaling", 
                                   "Let the output P(r) keep the scale of the data", 
                                   self._on_disable_scaling])
                
                if self._scale_output_unity==False:
                    m_list.append(["Scale P_max(r) to unity", 
                                   "Scale P(r) so that its maximum is 1", 
                                   self._on_scale_unity])
                    
                if self._normalize_output==False:
                    m_list.append(["Normalize P(r) to unity", 
                                   "Normalize the integral of P(r) to 1", 
                                   self._on_normalize])
                    
                return m_list
                #return [["Add P(r) data", "Load a data file and display it on this plot", self._on_add_data],
                #       ["Change number of P(r) points", "Change the number of points on the P(r) output", self._on_pr_npts]]

            elif item.name==graph.selected_plottable:
	            #TODO: we might want to check that the units are consistent with I(q)
	            #      before allowing this menu item
                if not self.standalone and issubclass(item.__class__, DataLoader.data_info.Data1D):
                    return [["Compute P(r)", "Compute P(r) from distribution", self._on_context_inversion]]      
                
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
            self._added_plots[plot].y = numpy.copy(self._default_Iq[plot])
            wx.PostEvent(self.parent, NewPlotEvent(plot=self._added_plots[plot], 
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
            sum = numpy.sum(self._added_plots[plot].y)
            npts = len(self._added_plots[plot].x)
            sum *= self._added_plots[plot].x[npts-1]/npts
            y = self._added_plots[plot].y/sum
            
            new_plot = Theory1D(self._added_plots[plot].x, y)
            new_plot.name = self._added_plots[plot].name
            new_plot.xaxis("\\rm{r}", 'A')
            new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
            
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, update=True,
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
                if y>_max: 
                    _max = y
            y = self._added_plots[plot].y/_max
            
            new_plot = Theory1D(self._added_plots[plot].x, y)
            new_plot.name = self._added_plots[plot].name
            new_plot.xaxis("\\rm{r}", 'A')
            new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
            
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, update=True,
                                                   title=self._added_plots[plot].name))        
        
        
    def _on_add_data(self, evt):
        """
        Add a data curve to the plot
        
        :WARNING: this will be removed once guiframe.plotting has
             its full functionality
        """
        path = self.choose_file()
        if path==None:
            return
        
        #x, y, err = self.parent.load_ascii_1D(path)
        # Use data loader to load file
        try:
            dataread = Loader().load(path)
            x = None
            y = None
            err = None
            if dataread.__class__.__name__ == 'Data1D':
                x = dataread.x
                y = dataread.y
                err = dataread.dy
            else:
                if isinstance(dataread, list) and len(dataread)>0:
                    x = dataread[0].x
                    y = dataread[0].y
                    err = dataread[0].dy
                    msg = "PrView only allows a single data set at a time. "
                    msg += "Only the first data set was loaded." 
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                else:
                    wx.PostEvent(self.parent, StatusEvent(status="This tool can only read 1D data"))
                    return
            
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))
            return
        
        filename = os.path.basename(path)
        
        #new_plot = Data1D(x, y, dy=err)
        new_plot = Theory1D(x, y)
        new_plot.name = filename
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
            
        # Store a ref to the plottable for later use
        self._added_plots[filename] = new_plot
        self._default_Iq[filename]  = numpy.copy(y)
        
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=filename))
        
        

    def start_thread(self):
        """
        """
        from pr_thread import CalcPr
        from copy import deepcopy
        
        # If a thread is already started, stop it
        if self.calc_thread != None and self.calc_thread.isrunning():
            self.calc_thread.stop()
                
        pr = self.pr.clone()
        self.calc_thread = CalcPr(pr, self.nfunc, error_func=self._thread_error, completefn=self._completed, updatefn=None)
        self.calc_thread.queue()
        self.calc_thread.ready(2.5)
    
    def _thread_error(self, error):
        """
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
        if not message==None:
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
        if not message==None:
            wx.PostEvent(self.parent, StatusEvent(status=str(message)))
    
    def _completed(self, out, cov, pr, elapsed):
        """
        Method called with the results when the inversion
        is done
        
        :param out: output coefficient for the base functions
        :param cov: covariance matrix
        :param pr: Invertor instance
        :param elapsed: time spent computing
        
        """
        from copy import deepcopy
        # Save useful info
        self.elapsed = elapsed
        # Keep a copy of the last result
        self._last_pr  = pr.clone()
        self._last_out = out
        self._last_cov = cov
        
        # Save Pr invertor
        self.pr = pr
        
        #message = "Computation completed in %g seconds [chi2=%g]" % (elapsed, pr.chi2)
        #wx.PostEvent(self.parent, StatusEvent(status=message))

        cov = numpy.ascontiguousarray(cov)

        # Show result on control panel
        self.control_panel.chi2 = pr.chi2
        self.control_panel.elapsed = elapsed
        self.control_panel.oscillation = pr.oscillations(out)
        #print "OSCILL", pr.oscillations(out)
        #print "PEAKS:", pr.get_peaks(out) 
        self.control_panel.positive = pr.get_positive(out)
        self.control_panel.pos_err  = pr.get_pos_err(out, cov)
        self.control_panel.rg = pr.rg(out)
        self.control_panel.iq0 = pr.iq0(out)
        self.control_panel.bck = pr.background
        
        if False:
            for i in range(len(out)):
                try:
                    print "%d: %g +- %g" % (i, out[i], math.sqrt(math.fabs(cov[i][i])))
                except: 
                    print sys.exc_value
                    print "%d: %g +- ?" % (i, out[i])        
        
            # Make a plot of I(q) data
            new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
            new_plot.name = IQ_DATA_LABEL
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
            #new_plot.group_id = "test group"
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Iq"))
                
        # Show I(q) fit
        self.show_iq(out, self.pr)
        
        # Show P(r) fit
        x_values, x_range = self.show_pr(out, self.pr, cov)  
        
        # Popup result panel
        #result_panel = InversionResults(self.parent, -1, style=wx.RAISED_BORDER)
        
    def show_data(self, path=None, reset=False):
        """
        Show data read from a file
        
        :param path: file path
        :param reset: if True all other plottables will be cleared
        
        """
        if path is not None:
            try:
                pr = self._create_file_pr(path)
            except:
                status="Problem reading data: %s" % sys.exc_value
                wx.PostEvent(self.parent, StatusEvent(status=status))
                raise RuntimeError, status
                
            # If the file contains nothing, just return
            if pr is None:
                raise RuntimeError, "Loaded data is invalid"
            
            self.pr = pr
              
        # Make a plot of I(q) data
        if self.pr.err==None:
            new_plot = Theory1D(self.pr.x, self.pr.y)
        else:
            new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
        new_plot.name = IQ_DATA_LABEL
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.interactive = True
        #new_plot.group_id = "test group"
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="I(q)", reset=reset))
        
        self.current_plottable = new_plot
        self.current_plottable.group_id = IQ_DATA_LABEL
        
        
        # Get Q range
        self.control_panel.q_min = self.pr.x.min()
        self.control_panel.q_max = self.pr.x.max()
            
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
        if issubclass(self.current_plottable.__class__, DataLoader.data_info.Data1D):
            self.state_reader.write(filepath, self.current_plottable, prstate)
        else:
            raise RuntimeError, "pr.save_data: the data being saved is not a DataLoader.data_info.Data1D object" 
        
        
    def setup_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None, 
                             bck=False, height=0, width=0):
        """
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.has_bck = bck
        self.slit_height = height
        self.slit_width  = width
        
        try:
            pr = self._create_plot_pr()
            if not pr==None:
                self.pr = pr
                self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))

    def estimate_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None, 
                                bck=False, height=0, width=0):
        """
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.has_bck = bck
        self.slit_height = height
        self.slit_width  = width
        
        try:
            pr = self._create_plot_pr()
            if not pr==None:
                self.pr = pr
                self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))            

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
        pr.has_bck = self.has_bck
        pr.slit_height = self.slit_height
        pr.slit_width = self.slit_width
        
        # Keep track of the plot window title to ensure that
        # we can overlay the plots
        if hasattr(self.current_plottable, "group_id"):
            pr.info["plot_group_id"] = self.current_plottable.group_id
        
        # Fill in errors if none were provided
        err = self.current_plottable.dy
        all_zeros = True
        if err == None:
            err = numpy.zeros(len(pr.y)) 
        else:    
            for i in range(len(err)):
                if err[i]>0:
                    all_zeros = False
        
        if all_zeros:        
            scale = None
            min_err = 0.0
            for i in range(len(pr.y)):
                # Scale the error so that we can fit over several decades of Q
                if scale==None:
                    scale = 0.05*math.sqrt(pr.y[i])
                    min_err = 0.01*pr.y[i]
                err[i] = scale*math.sqrt( math.fabs(pr.y[i]) ) + min_err
            message = "The loaded file had no error bars, statistical errors are assumed."
            wx.PostEvent(self.parent, StatusEvent(status=message))

        pr.err = err
        
        return pr

          
    def setup_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None, 
                             bck=False, height=0, width=0):
        """
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.has_bck = bck
        self.slit_height = height
        self.slit_width  = width
        
        try:
            pr = self._create_file_pr(path)
            if not pr==None:
                self.pr = pr
                self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))
          
    def estimate_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None, 
                                bck=False, height=0, width=0):
        """
        """
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        self.has_bck = bck
        self.slit_height = height
        self.slit_width  = width
        
        try:
            pr = self._create_file_pr(path)
            if not pr==None:
                self.pr = pr
                self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))
                
          
    def _create_file_pr(self, path):
        """
        Create and prepare invertor instance from
        a file data set.
        
        :param path: path of the file to read in 
        
        """
        # Load data
        if os.path.isfile(path):
            
            if self._current_file_data is not None \
                and self._current_file_data.path==path:
                # Protect against corrupted data from 
                # previous failed load attempt
                if self._current_file_data.x is None:
                    return None
                x = self._current_file_data.x
                y = self._current_file_data.y
                err = self._current_file_data.err
                
                message = "The data from this file has already been loaded."
                wx.PostEvent(self.parent, StatusEvent(status=message))
            else:
                # Reset the status bar so that we don't get mixed up
                # with old messages. 
                #TODO: refactor this into a proper status handling
                wx.PostEvent(self.parent, StatusEvent(status=''))
                try:
                    x, y, err = self.load(path)
                except:
                    load_error(sys.exc_value)
                    return None
                
                # If the file contains no data, just return
                if x is None or len(x)==0:
                    load_error("The loaded file contains no data")
                    return None
            
            # If we have not errors, add statistical errors
            if err==None and y is not None:
                err = numpy.zeros(len(y))
                scale = None
                min_err = 0.0
                for i in range(len(y)):
                    # Scale the error so that we can fit over several decades of Q
                    if scale==None:
                        scale = 0.05*math.sqrt(y[i])
                        min_err = 0.01*y[i]
                    err[i] = scale*math.sqrt( math.fabs(y[i]) ) + min_err
                message = "The loaded file had no error bars, statistical errors are assumed."
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
                pr.has_bck = self.has_bck
                pr.slit_height = self.slit_height
                pr.slit_width = self.slit_width
                return pr
            except:
                load_error(sys.exc_value)
        return None
        
    def perform_estimate(self):
        """
        """
        from pr_thread import EstimatePr
        from copy import deepcopy
        
        # If a thread is already started, stop it
        if self.estimation_thread != None and self.estimation_thread.isrunning():
            self.estimation_thread.stop()
                
        pr = self.pr.clone()
        self.estimation_thread = EstimatePr(pr, self.nfunc, error_func=self._thread_error, 
                                            completefn = self._estimate_completed, 
                                            updatefn   = None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)
    
    def perform_estimateNT(self):
        """
        """
        from pr_thread import EstimateNT
        from copy import deepcopy
        
        # If a thread is already started, stop it
        if self.estimation_thread != None and self.estimation_thread.isrunning():
            self.estimation_thread.stop()
                
        pr = self.pr.clone()
        # Skip the slit settings for the estimation
        # It slows down the application and it doesn't change the estimates
        pr.slit_height = 0.0
        pr.slit_width  = 0.0
        self.estimation_thread = EstimateNT(pr, self.nfunc, error_func=self._thread_error, 
                                            completefn = self._estimateNT_completed, 
                                            updatefn   = None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)
        
    def perform_inversion(self):
        """
        """
        # Time estimate
        #estimated = self.elapsed*self.nfunc**2
        #message = "Computation time may take up to %g seconds" % self.elapsed
        #wx.PostEvent(self.parent, StatusEvent(status=message))
        
        # Start inversion thread
        self.start_thread()
        return
        
        out, cov = self.pr.lstsq(self.nfunc)
        
        # Save useful info
        self.elapsed = self.pr.elapsed
        
        for i in range(len(out)):
            try:
                print "%d: %g +- %g" % (i, out[i], math.sqrt(math.fabs(cov[i][i])))
            except: 
                print "%d: %g +- ?" % (i, out[i])        
        
        # Make a plot of I(q) data
        new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
        new_plot.name = "I_{obs}(q)"
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Iq"))
                
        # Show I(q) fit
        self.show_iq(out, self.pr)
        
        # Show P(r) fit
        x_values, x_range = self.show_pr(out, self.pr, cov=cov)
        
        
          
    def _on_context_inversion(self, event):
        panel = event.GetEventObject()

        # If we have more than one displayed plot, make the user choose
        if len(panel.plots)>1 and panel.graph.selected_plottable in panel.plots:
            dataset = panel.graph.selected_plottable
        elif len(panel.plots)==1:
            dataset = panel.plots.keys()[0]
        else:
            print "Error: No data is available"
            return
        
        # Store a reference to the current plottable
        # If we have a suggested value, use it.
        try:
            estimate = float(self.control_panel.alpha_estimate)
            self.control_panel.alpha = estimate
        except:
            self.control_panel.alpha = self.alpha
            print "No estimate yet"
            pass
        try:
            estimate = int(self.control_panel.nterms_estimate)
            self.control_panel.nfunc = estimate
        except:
            self.control_panel.nfunc = self.nfunc
            print "No estimate yet"
            pass
        
        self.current_plottable = panel.plots[dataset]
        self.control_panel.plotname = dataset
        #self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        self.parent.set_perspective(self.perspective)
        self.control_panel._on_invert(None)
            
    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        from inversion_panel import InversionControl
        
        self.parent = parent
        self.control_panel = InversionControl(self.parent, -1, 
                                              style=wx.RAISED_BORDER,
                                              standalone=self.standalone)
        self.control_panel.set_manager(self)
        self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        self.control_panel.alpha = self.alpha
        
        self.perspective = []
        self.perspective.append(self.control_panel.window_name)
        
        self.parent.Bind(EVT_PR_FILE, self._on_new_file)
        
        return [self.control_panel]
    
    def _on_new_file(self, evt):
        """
            Called when the application manager posted an
            EVT_PR_FILE event. Just prompt the control
            panel to load a new data file.
        """
        self.control_panel._change_file(None)
    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
            [Somehow openGL needs this call]
        """
        if self.standalone==True:
            self.parent.set_perspective(self.perspective)
  
if __name__ == "__main__":
    i = Plugin()
    print i.perform_estimateNT()
    
    
    
    
#TODO: Use simview to generate P(r) and I(q) pairs in sansview.
# Make sure the option of saving each curve is available 
# Use the I(q) curve as input and compare the output to P(r)

import os
import sys
import wx
import logging
from sans.guitools.plottables import Data1D, Theory1D
from sans.guicomm.events import NewPlotEvent, StatusEvent    
import math, numpy
from sans.pr.invertor import Invertor

PR_FIT_LABEL    = "P_{fit}(r)"
PR_LOADED_LABEL = "P_{loaded}(r)"
IQ_DATA_LABEL   = "I_{obs}(q)"

import wx.lib
(NewPrFileEvent, EVT_PR_FILE) = wx.lib.newevent.NewEvent()


class Plugin:
    
    DEFAULT_ALPHA = 0.0001
    DEFAULT_NFUNC = 10
    DEFAULT_DMAX  = 140.0
    
    def __init__(self):
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
        ## Remember last plottable processed
        self.last_data  = "sphere_60_q0_2.txt"
        ## Time elapsed for last computation [sec]
        # Start with a good default
        self.elapsed = 0.022
        self.iq_data_shown = False
        
        ## Current invertor
        self.invertor    = None
        self.pr          = None
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
        self.standalone = True
        
        # Log startup
        logging.info("Pr(r) plug-in started")
        
        

    def populate_menu(self, id, owner):
        """
            Create a menu for the plug-in
        """
        return []
        import wx
        shapes = wx.Menu()

        id = wx.NewId()
        shapes.Append(id, '&Sphere test')
        wx.EVT_MENU(owner, id, self._fit_pr)
        
        return [(id, shapes, "P(r)")]
    
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
        """
        from inversion_panel import HelpDialog
        dialog = HelpDialog(None, -1)
        if dialog.ShowModal() == wx.ID_OK:
            dialog.Destroy()
        else:
            dialog.Destroy()
    
    def _fit_pr(self, evt):
        from sans.pr.invertor import Invertor
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from sans.guitools.plottables import Data1D, Theory1D
        
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
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from sans.guitools.plottables import Data1D, Theory1D
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
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from sans.guitools.plottables import Data1D, Theory1D

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
        new_plot.name = "I_{fit}(q)"
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        #new_plot.group_id = "test group"
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="I(q)"))
        
        
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
            self.show_pr(self.pr.out, self.pr, self.pr.cov)
        else:
            dialog.Destroy()
        
        
    def show_pr(self, out, pr, cov=None):
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from sans.guitools.plottables import Data1D, Theory1D
        
        # Show P(r)
        x = pylab.arange(0.0, pr.d_max, pr.d_max/self._pr_npts)
    
        y = numpy.zeros(len(x))
        dy = numpy.zeros(len(x))
        y_true = numpy.zeros(len(x))

        sum = 0.0
        cov2 = numpy.ascontiguousarray(cov)
        
        for i in range(len(x)):
            if cov2==None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov2, x[i])
            sum += value*pr.d_max/len(x)
            y[i] = value
            
        y = y/sum
        dy = dy/sum
        
        if cov2==None:
            new_plot = Theory1D(x, y)
        else:
            new_plot = Data1D(x, y, dy=dy)
        new_plot.name = "P_{fit}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
            
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="P(r) fit"))
        
        return x, pr.d_max
        
        
    def choose_file(self):
        """
        
        """
        #TODO: this should be in a common module
        return self.parent.choose_file()
                
    def load(self, path = "sphere_60_q0_2.txt"):
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
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        # Look whether this Graph contains P(r) data
        #if graph.selected_plottable==IQ_DATA_LABEL:
        for item in graph.plottables:
            if item.name==PR_FIT_LABEL:
                return [["Add P(r) data", "Load a data file and display it on this plot", self._on_add_data],
                       ["Change number of P(r) points", "Change the number of points on the P(r) output", self._on_pr_npts]]

            elif item.name==graph.selected_plottable:
                return [["Compute P(r)", "Compute P(r) from distribution", self._on_context_inversion]]      
                
        return []

    def _on_add_data(self, evt):
        """
            Add a data curve to the plot
            WARNING: this will be removed once guiframe.plotting has its full functionality
        """
        path = self.choose_file()
        if path==None:
            return
        
        x, y, err = self.parent.load_ascii_1D(path)
        
        #new_plot = Data1D(x, y, dy=err)
        new_plot = Theory1D(x, y)
        new_plot.name = "P_{loaded}(r)"
        new_plot.xaxis("\\rm{r}", 'A')
        new_plot.yaxis("\\rm{P(r)} ","cm^{-3}")
            
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="P(r) fit"))
        
        

    def start_thread(self):
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
        wx.PostEvent(self.parent, StatusEvent(status=error))
    
    def _estimate_completed(self, alpha, message, elapsed):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        # Save useful info
        self.elapsed = elapsed
        self.control_panel.alpha_estimate = alpha
        if not message==None:
            wx.PostEvent(self.parent, StatusEvent(status=str(message)))
    
    def _completed(self, out, cov, pr, elapsed):
        """
            Method called with the results when the inversion
            is done
            
            @param out: output coefficient for the base functions
            @param cov: covariance matrix
            @param pr: Invertor instance
            @param elapsed: time spent computing
        """
        from copy import deepcopy
        # Save useful info
        self.elapsed = elapsed
        # Save Pr invertor
        self.pr = pr
        
        message = "Computation completed in %g seconds [chi2=%g]" % (elapsed, pr.chi2)
        wx.PostEvent(self.parent, StatusEvent(status=message))

        cov = numpy.ascontiguousarray(cov)

        # Show result on control panel
        self.control_panel.chi2 = pr.chi2
        self.control_panel.elapsed = elapsed
        self.control_panel.oscillation = pr.oscillations(out)
        #print "OSCILL", pr.oscillations(out)
        print "PEAKS:", pr.get_peaks(out) 
        self.control_panel.positive = pr.get_positive(out)
        self.control_panel.pos_err  = pr.get_pos_err(out, cov)
        
        for i in range(len(out)):
            try:
                print "%d: %g +- %g" % (i, out[i], math.sqrt(math.fabs(cov[i][i])))
            except: 
                print sys.exc_value
                print "%d: %g +- ?" % (i, out[i])        
        
        # Make a plot of I(q) data
        if False:
            new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
            new_plot.name = "I_{obs}(q)"
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
        
    def show_data(self, path=None):
        if not path==None:
            self._create_file_pr(path)  
              
        # Make a plot of I(q) data
        new_plot = Data1D(self.pr.x, self.pr.y, dy=self.pr.err)
        new_plot.name = "I_{obs}(q)"
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.interactive = True
        #new_plot.group_id = "test group"
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="I(q)"))
        
        # Get Q range
        self.control_panel.q_min = self.pr.x.min()
        self.control_panel.q_max = self.pr.x.max()
            

        
    def setup_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        try:
            self._create_plot_pr()
            self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))

    def estimate_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        try:
            self._create_plot_pr()
            self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))            

    def _create_plot_pr(self):
        """
            Create and prepare invertor instance from
            a plottable data set.
            @param path: path of the file to read in 
        """
        # Get the data from the chosen data set and perform inversion
        pr = Invertor()
        pr.d_max = self.max_length
        pr.alpha = self.alpha
        pr.q_min = self.q_min
        pr.q_max = self.q_max
        pr.x = self.current_plottable.x
        pr.y = self.current_plottable.y
        
        # Fill in errors if none were provided
        if self.current_plottable.dy == None:
            print "no error", self.current_plottable.name
            y = numpy.zeros(len(pr.y))
            for i in range(len(pr.y)):
                y[i] = math.sqrt(pr.y[i])
            pr.err = y
        else:
            pr.err = self.current_plottable.dy
            
        self.pr = pr
        self.iq_data_shown = True

          
    def setup_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        try:
            if self._create_file_pr(path):
                self.perform_inversion()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))
          
    def estimate_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        try:
            if self._create_file_pr(path):
                self.perform_estimate()
        except:
            wx.PostEvent(self.parent, StatusEvent(status=sys.exc_value))
                
          
    def _create_file_pr(self, path):
        """
            Create and prepare invertor instance from
            a file data set.
            @param path: path of the file to read in 
        """
        # Load data
        if os.path.isfile(path):
            x, y, err = self.load(path)
            
            # Get the data from the chosen data set and perform inversion
            pr = Invertor()
            pr.d_max = self.max_length
            pr.alpha = self.alpha
            pr.q_min = self.q_min
            pr.q_max = self.q_max
            pr.x = x
            pr.y = y
            pr.err = err
            
            self.pr = pr
            return True
        return False
        
    def perform_estimate(self):
        from pr_thread import EstimatePr
        from copy import deepcopy
        
        wx.PostEvent(self.parent, StatusEvent(status=''))
        # If a thread is already started, stop it
        if self.estimation_thread != None and self.estimation_thread.isrunning():
            self.estimation_thread.stop()
                
        pr = self.pr.clone()
        self.estimation_thread = EstimatePr(pr, self.nfunc, error_func=self._thread_error, 
                                            completefn = self._estimate_completed, 
                                            updatefn   = None)
        self.estimation_thread.queue()
        self.estimation_thread.ready(2.5)
        
    def perform_inversion(self):
        
        # Time estimate
        #estimated = self.elapsed*self.nfunc**2
        message = "Computation time may take up to %g seconds" % self.elapsed
        wx.PostEvent(self.parent, StatusEvent(status=message))
        
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

        from inversion_panel import InversionDlg
        
        # If we have more than one displayed plot, make the user choose
        if len(panel.plots)>1 and panel.graph.selected_plottable in panel.plots:
            dataset = panel.graph.selected_plottable
            if False:
                dialog = InversionDlg(None, -1, "P(r) Inversion", panel.plots, pars=False)
                dialog.set_content(self.last_data, self.nfunc, self.alpha, self.max_length)
                if dialog.ShowModal() == wx.ID_OK:
                    dataset = dialog.get_content()
                    dialog.Destroy()
                else:
                    dialog.Destroy()
                    return
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
        
        self.current_plottable = panel.plots[dataset]
        self.control_panel.plotname = dataset
        self.control_panel.nfunc = self.nfunc
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
        self.parent.set_perspective(self.perspective)
    
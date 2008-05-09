#TODO: Use simview to generate P(r) and I(q) pairs in sansview.
# Make sure the option of saving each curve is available 
# Use the I(q) curve as input and compare the output to P(r)

import os
import wx
from sans.guitools.plottables import Data1D, Theory1D
from sans.guicomm.events import NewPlotEvent, StatusEvent    
import math, numpy
from sans.pr.invertor import Invertor

class Plugin:
    
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
        self.alpha      = 0.0001
        self.nfunc      = 10
        self.max_length = 140.0
        self.q_min      = None
        self.q_max      = None
        ## Remember last plottable processed
        self.last_data  = "sphere_60_q0_2.txt"
        ## Time elapsed for last computation [sec]
        # Start with a good default
        self.elapsed = 0.022
        
        ## Current invertor
        self.invertor    = None
        ## Calculation thread
        self.calc_thread = None
        ## Estimation thread
        self.estimation_thread = None
        ## Result panel
        self.control_panel = None
        ## Currently views plottable
        self.current_plottable = None

    def populate_menu(self, id, owner):
        """
            Create a menu for the plug-in
        """
        import wx
        shapes = wx.Menu()

        id = wx.NewId()
        shapes.Append(id, '&Sphere test')
        wx.EVT_MENU(owner, id, self._fit_pr)
        return [(id, shapes, "P(r)")]
    
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
        new_plot = Data1D(pr.x, pr.y, pr.err)
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
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Iq"))
        
        
        
        
    def show_pr(self, out, pr, cov=None):
        import numpy
        import pylab
        import math
        from sans.guicomm.events import NewPlotEvent            
        from sans.guitools.plottables import Data1D, Theory1D
        
        # Show P(r)
        x = pylab.arange(0.0, pr.d_max, pr.d_max/51.0)
    
        y = numpy.zeros(len(x))
        dy = numpy.zeros(len(x))
        y_true = numpy.zeros(len(x))

        sum = 0.0
        for i in range(len(x)):
            if cov==None:
                value = pr.pr(out, x[i])
            else:
                (value, dy[i]) = pr.pr_err(out, cov, x[i])
            sum += value
            y[i] = value
            
        y = y/sum*pr.d_max/len(x)
        dy = dy/sum*pr.d_max/len(x)
        
        if cov==None:
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
                
    def load(self, path = "sphere_test_data.txt"):
        import numpy, math, sys
        # Read the data from the data file
        data_x   = numpy.zeros(0)
        data_y   = numpy.zeros(0)
        data_err = numpy.zeros(0)
        if not path == None:
            input_f = open(path,'r')
            buff    = input_f.read()
            lines   = buff.split('\n')
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    data_x = numpy.append(data_x, x)
                    data_y = numpy.append(data_y, y)
                    try:
                        scale = 0.05/math.sqrt(data_x[0])
                    except:
                        scale = 1.0
                    #data_err = numpy.append(data_err, 10.0*math.sqrt(y)+1000.0)
                    data_err = numpy.append(data_err, scale*math.sqrt(y))
                except:
                    print "Error reading line: ", line
                    print sys.exc_value
                   
        print "Lines read:", len(data_x)
        return data_x, data_y, data_err
        
    def pr_theory(self, r, R):
        """
           
        """
        if r<=2*R:
            return 12.0* ((0.5*r/R)**2) * ((1.0-0.5*r/R)**2) * ( 2.0 + 0.5*r/R )
        else:
            return 0.0

    def get_context_menu(self, plot_id=None):
        """
            Get the context menu items available for P(r)
            @param plot_id: Unique ID of a plot, so that we can recognize those
                            that we created
            @return: a list of menu items with call-back function
        """
        return [["Compute P(r)", "Compute P(r) from distribution", self._on_context_inversion]]
    

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
        # Save useful info
        self.elapsed = elapsed
        message = "Computation completed in %g seconds [chi2=%g]" % (elapsed, pr.chi2)
        wx.PostEvent(self.parent, StatusEvent(status=message))

        # Show result on control panel
        self.control_panel.chi2 = pr.chi2
        self.control_panel.elapsed = elapsed
        self.control_panel.oscillation = pr.oscillations(out)
        #print "OSCILL", pr.oscillations(out)
        print "PEAKS:", pr.get_peaks(out)
        
        for i in range(len(out)):
            try:
                print "%d: %g +- %g" % (i, out[i], math.sqrt(math.fabs(cov[i][i])))
            except: 
                print "%d: %g +- ?" % (i, out[i])        
        
        # Make a plot of I(q) data
        new_plot = Data1D(self.pr.x, self.pr.y, self.pr.err)
        new_plot.name = "I_{obs}(q)"
        new_plot.xaxis("\\rm{Q}", 'A^{-1}')
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        #new_plot.group_id = "test group"
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Iq"))
                
        # Show I(q) fit
        self.show_iq(out, self.pr)
        
        # Show P(r) fit
        x_values, x_range = self.show_pr(out, self.pr)  
        
        # Popup result panel
        #result_panel = InversionResults(self.parent, -1, style=wx.RAISED_BORDER)
        
    def setup_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        self._create_plot_pr()
        self.perform_inversion()

    def estimate_plot_inversion(self, alpha, nfunc, d_max, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        self._create_plot_pr()
        self.perform_estimate()

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

          
    def setup_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        self._create_file_pr(path)
        
        self.perform_inversion()
          
    def estimate_file_inversion(self, alpha, nfunc, d_max, path, q_min=None, q_max=None):
        self.alpha = alpha
        self.nfunc = nfunc
        self.max_length = d_max
        self.q_min = q_min
        self.q_max = q_max
        
        if self._create_file_pr(path):
            self.perform_estimate()
          
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
        if len(panel.plots)>1:
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
        self.current_plottable = panel.plots[dataset]
        self.control_panel.plotname = dataset
        self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        self.control_panel.alpha = self.alpha
        self.parent.set_perspective(self.perspective)
            
    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        from inversion_panel import InversionControl
        
        self.parent = parent
        self.control_panel = InversionControl(self.parent, -1, style=wx.RAISED_BORDER)
        self.control_panel.set_manager(self)
        self.control_panel.nfunc = self.nfunc
        self.control_panel.d_max = self.max_length
        self.control_panel.alpha = self.alpha
        
        self.perspective = []
        self.perspective.append(self.control_panel.window_name)
        return [self.control_panel]
    
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
    

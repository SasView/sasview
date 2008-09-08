import os,os.path, re
import sys, wx, logging
import string, numpy, pylab, math

from sans.guitools.plottables import Data1D, Theory1D
from sans.guitools.PlotPanel import PlotPanel
from sans.guicomm.events import NewPlotEvent, StatusEvent  
from copy import deepcopy 
from sans.fit.AbstractFitEngine import Model
from sans.fit.AbstractFitEngine import Data
from fitproblem import FitProblem
from fitpanel import FitPanel

import models
import fitpage
class PlottableData(Data,Data1D):
    """ class plottable data"""
    def __init__(self,data,data1d):
        self.x = data1d.x
        self.y = data1d.y
        self.dx= data1d.dx
        self.dy= data1d.dy
       
        self.group_id= data1d.group_id
        x_name, x_units = data1d.get_xaxis() 
        y_name, y_units = data1d.get_yaxis() 
        self.xaxis( x_name, x_units)
        self.yaxis( y_name, y_units )
        self.qmin=data.qmin
        self.qmax=data.qmax
class Plugin:
    """
    """
    
    def __init__(self):
        ## Plug-in name
        self.sub_menu = "Fitting"
        
        ## Reference to the parent window
        self.parent = None
        self.menu_mng = models.ModelManager()
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        # Start with a good default
        self.elapsed = 0.022
        self.fitter  = None
       
        #Flag to let the plug-in know that it is running standalone
        self.standalone=True
        ## Fit engine
        self._fit_engine = 'park'
        # Log startup
        logging.info("Fitting plug-in started")   

    def populate_menu(self, id, owner):
        """
            Create a menu for the Fitting plug-in
            @param id: id to create a menu
            @param owner: owner of menu
            @ return : list of information to populate the main menu
        """
        #Menu for fitting
        self.menu1 = wx.Menu()
        id1 = wx.NewId()
        self.menu1.Append(id1, '&Show fit panel')
        wx.EVT_MENU(owner, id1, self.on_perspective)
        
        #menu for model
        menu2 = wx.Menu()
        self.menu_mng.populate_menu(menu2, owner)
        id2 = wx.NewId()
        owner.Bind(models.EVT_MODEL,self._on_model_menu)
        self.fit_panel.set_owner(owner)
        self.fit_panel.set_model_list(self.menu_mng.get_model_list())
        owner.Bind(fitpage.EVT_MODEL_BOX,self._on_model_panel)
        #owner.Bind(modelpage.EVT_MODEL_DRAW,self.draw_model)
      
        return [(id, self.menu1, "Fitting"),(id2, menu2, "Model")]
    
    
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
        """
        pass
    
    def get_context_menu(self, graph=None):
        """
            Get the context menu items available for P(r)
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        
        self.graph=graph
        for item in graph.plottables:
            if item.name==graph.selected_plottable and item.__class__.__name__ is not "Theory1D":
                return [["Select Data", "Dialog with fitting parameters ", self._onSelect]] 
        return []   


    def get_panels(self, parent):
        """
            Create and return a list of panel objects
        """
        self.parent = parent
        # Creation of the fit panel
        self.fit_panel = FitPanel(self.parent, -1)
        #Set the manager forthe main panel
        self.fit_panel.set_manager(self)
        # List of windows used for the perspective
        self.perspective = []
        self.perspective.append(self.fit_panel.window_name)
        # take care of saving  data, model and page associated with each other
        self.page_finder={}
        self.index_model=0
        return [self.fit_panel]
   
      
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
        
        
    def _onSelect(self,event):
        """ 
            when Select data to fit a new page is created .Its reference is 
            added to self.page_finder
        """
        self.panel = event.GetEventObject()
        for item in self.panel.graph.plottables:
            if item.name == self.panel.graph.selected_plottable:
                try:
                    name = item.group_id # item in Data1D
                except:
                    name = 'Fit'
                try:
                    page = self.fit_panel.add_fit_page(name)
                    page.set_data_name(item)
                    self.page_finder[page]= FitProblem()
                    #creating Data type
                    data1= Data(sans_data=item)
                    datas=PlottableData(data=data1,data1d=item)
                    self.page_finder[page].add_data(datas)
                except:
                    raise 
                    wx.PostEvent(self.parent, StatusEvent(status="Fitting error: \
                    data already Selected "))
                    
                    
    def get_page_finder(self):
        """ @return self.page_finder used also by simfitpage.py"""  
        return self.page_finder 
    
    
    def set_page_finder(self,modelname,param,values):
        """
             Used by simfitpage.py to reset a parameter given the string constrainst.
             @param modelname: the name ot the model for with the parameter has to reset
             @param value: can be a string in this case.
             @note: expecting park used for fit.
        """  
        sim_page=self.fit_panel.get_page(0)
        for page, value in self.page_finder.iteritems():
            if page != sim_page:
                list=value.get_model()
                model=list[0]
                if model.name== modelname:
                    value.set_model_param(param,values)
                    break

   
                            
    def split_string(self,item): 
        """
            recieve a word containing ""
        """
        #print "fitting: split :went here" 
        
        if string.find(item,".")!=-1:
            param_names= re.split("\.",item)
            model_name=param_names[0]
            param_name=param_names[1]  
            return model_name,param_name
        
        
    def _single_fit_completed(self,result,pars,current_pg,qmin,qmax):
        """
          
        """
       
        try:
            for page, value in self.page_finder.iteritems():
                if page== current_pg:
                    data = value.get_data()
                    list = value.get_model()
                    model= list[0]
                    break
            #print "fitting : result",result,result.pvec,result.cov,result.fitness
            i = 0
            for name in pars:
                if result.pvec.__class__==numpy.float64:
                    model.setParam(name,result.pvec)
                else:
                    model.setParam(name,result.pvec[i])
                    #print "fitting: i name out[i]", i,name,float(result.pvec[i])
                    i += 1
            new_cov=[]
            if result.cov !=None:
                 for j in range(len(result.cov)):
                     new_cov.append(result.cov[j][j])  
            else:
                new_cov=None
            current_pg.onsetValues(result.fitness, result.pvec,new_cov)
            self.plot_helper(currpage=current_pg,qmin=qmin,qmax=qmax)
        except:
             wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
            
       
    def _simul_fit_completed(self,result,qmin,qmax):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        try:
            for page, value in self.page_finder.iteritems():
                data = value.get_data()
                list = value.get_model()
                model= list[0]
               
                small_out = []
                small_cov = []
                i = 0
                for p in result.parameters:
                    print "fitting: fit in park fitting", p.name, p.value,p.stderr
                    model_name,param_name = self.split_string(p.name)  
                    print "fitting: simultfit",model.name,model_name,param_name ,p.name,param_name,p.value
                    if model.name == model_name:
                        print "fitting: hello",p.name,param_name,p.value
                        small_out.append(p.value )
                        small_cov.append(p.stderr)
                        model.setParam(param_name,p.value)   
                #print "fitting: out of each page",page,small_out,small_cov,data.group_id
                page.onsetValues(result.fitness, small_out,small_cov)
                self.plot_helper(currpage= page,qmin= qmin,qmax= qmax) 
        except:
             wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
            
     
    def _completed(self,result,pars,current_pg, elapsed):
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
        # Keep a copy of the last result
        self._last_out = result.pvec
        self._last_cov = result.cov
        self._last_chisqr=result.fitness
        #print "fitting: initial parameter ",pars
        #result=self.fitter.fit(qmin,qmax)
        
        #print "fitting : result",result,result.pvec,result.cov,result.fitness
        i = 0
        for name in pars:
            if result.pvec.__class__==numpy.float64:
                model.model.setParam(name,result.pvec)
            else:
                model.model.setParam(name,result.pvec[i])
                #print "fitting: i name out[i]", i,name,float(result.pvec[i])
                i += 1
        new_cov=[]
        if result.cov !=None:
             for j in range(len(result.cov)):
                 new_cov.append(result.cov[j][j])  
        else:
            new_cov=None
        current_pg.onsetValues(result.fitness, result.pvec,new_cov)
        self.plot_helper(currpage=current_pg,qmin=qmin,qmax=qmax)
 
        
    def _on_single_fit(self,id=None,qmin=None,qmax=None):
        """ 
            perform fit for the  current page  and return chisqr,out and cov
            @param engineName: type of fit to be performed
            @param id: unique id corresponding to a fit problem(model, set of data)
            @param model: model to fit
            
        """
        #set an engine to perform fit
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        #Setting an id to store model and data
        if id==None:
            id=0
        self.id=id
        current_pg=self.fit_panel.get_current_page() 
        for page, value in self.page_finder.iteritems():
            if page ==current_pg :
                #print "fitting: self.page_finder",self.page_finder
                data = value.get_data()
                list=value.get_model()
                model=list[0]
                
                #Create dictionary of parameters for fitting used
                pars=[]
                templist=[]
                try:
                    templist=current_pg.get_param_list()
                except:
                    raise
                    wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                    return
                #for element in templist:
                #    print "fitting: templist",str(element[0].GetLabelText())
                #print "fitting: model list",model.getParamList()
                for element in templist:
                    try:
                       pars.append(str(element[0].GetLabelText()))
                    except:
                        raise
                        wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                        return
                #print "fitting: pars",pars
                pars.sort()
                
                self.fitter.set_model(model,model.name, self.id, pars) 
                self.fitter.set_data(data,self.id,qmin,qmax)
                #Do the fit SCIPY
                try:
                    result=self.fitter.fit()
                    self._single_fit_completed(result,pars,current_pg,qmin,qmax)
                   
                except:
                    wx.PostEvent(self.parent, StatusEvent(status="Single Fit error: %s" % sys.exc_value))
                    return
         
    def _on_simul_fit(self, id=None,qmin=None,qmax=None):
        """ 
            perform fit for all the pages selected on simpage and return chisqr,out and cov
            @param engineName: type of fit to be performed
            @param id: unique id corresponding to a fit problem(model, set of data)
             in park_integration
            @param model: model to fit
            
        """
        #print "fitting: probabily breaking on fit call"
        #set an engine to perform fit
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        #Setting an id to store model and data
        if id==None:
             id = 0
        self.id = id
        for page, value in self.page_finder.iteritems():
            try:
                #print "fitting: self.page_finder",value
                data = value.get_data()
                #print "fitting: data",data
                list = value.get_model()
                model= list[0]
                if data != None :
                    #Create dictionary of parameters for fitting used
                    pars = []
                    templist = []
                    try:
                        templist = page.get_param_list()
                    except:
                        wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                        return
                    
                    for element in templist:
                        try:
                            name = str(element[0].GetLabelText())
                            pars.append(name)
                        except:
                            wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                            return
                
                    print "fitting: pars",pars,model.name
                    #print "fitter",self.fitter
                    #print "fitting: model name",model.name
                    self.fitter.set_model(Model(model),model.name, self.id, pars) 
                    self.fitter.set_data(data,self.id,qmin,qmax)
                else:
                    raise ValueError," Fitting: cannot set model with empty parameter"
                self.id += 1 
            except:
                    raise
                    wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                    return 
        #Do the fit SCIPY
        try:
            result=self.fitter.fit()
            self._simul_fit_completed(result,qmin,qmax)
        except:
            raise
            wx.PostEvent(self.parent, StatusEvent(status="Simultaneous Fitting error: %s" % sys.exc_value))
            return
   
    def _on_change_engine(self, engine='park'):
        """
            Allow to select the type of engine to perform fit 
            @param engine: the key work of the engine
        """
        self._fit_engine = engine
   
   
    def _on_model_panel(self, evt):
        """
            react to model selection on any combo box or model menu.plot the model  
        """
        model = evt.model
        name = evt.name
        sim_page=self.fit_panel.get_page(0)
        current_pg = self.fit_panel.get_current_page() 
        if current_pg != sim_page:
            current_pg.set_model_name(name)
            current_pg.set_panel(model)
            try:
                data=self.page_finder[current_pg].get_data()
                M_name="M"+str(self.index_model)+"= "+name+"("+data.group_id+")"
            except:
                raise 
                M_name="M"+str(self.index_model)+"= "+name
            model.name="M"+str(self.index_model)
            self.index_model += 1  
            self.page_finder[current_pg].set_theory("Fitness")
            #print "on model",model.name
            self.page_finder[current_pg].set_model(model,M_name)
            self.plot_helper(currpage= current_pg,qmin= None,qmax= None)
            sim_page.add_model(self.page_finder)
        
            
    def redraw_model(self,qmin= None,qmax= None):
        """
            Draw a theory according to model changes or data range.
            @param qmin: the minimum value plotted for theory
            @param qmax: the maximum value plotted for theory
        """
        current_pg=self.fit_panel.get_current_page()
        for page, value in self.page_finder.iteritems():
            if page ==current_pg :
                break 
        self.plot_helper(currpage=page,qmin= qmin,qmax= qmax)
        
    def plot_helper(self,currpage,qmin=None,qmax=None):
        """
            Plot a theory given a model and data
            @param model: the model from where the theory is derived
            @param currpage: page in a dictionary referring to some data
        """
        #print "fitting: plot helper"
        if self.fit_panel.get_page_count() >1:
            for page in self.page_finder.iterkeys():
                if  page==currpage :  
                    break 
           
            data=self.page_finder[page].get_data()
            list=self.page_finder[page].get_model()
            model=list[0]
            if data!=None:
                theory = Theory1D(x=[], y=[])
                theory.name = self.page_finder[page].get_theory()
                theory.group_id = data.group_id
              
                x_name, x_units = data.get_xaxis() 
                y_name, y_units = data.get_yaxis() 
                theory.xaxis(x_name, x_units)
                theory.yaxis(y_name, y_units)
              
                if qmin == None :
                   qmin = min(data.x)
                if qmax == None :
                    qmax = max(data.x)
                try:
                    tempx = qmin
                    tempy = model.run(qmin)
                    theory.x.append(tempx)
                    theory.y.append(tempy)
                except :
                        wx.PostEvent(self.parent, StatusEvent(status="fitting \
                        skipping point x %g %s" %(qmin, sys.exc_value)))
                           
                for i in range(len(data.x)):
                    try:
                        if data.x[i]> qmin and data.x[i]< qmax:
                            tempx = data.x[i]
                            tempy = model.run(tempx)
                            
                            theory.x.append(tempx) 
                            theory.y.append(tempy)
                    except:
                        wx.PostEvent(self.parent, StatusEvent(status="fitting \
                        skipping point x %g %s" %(data.x[i], sys.exc_value)))   
                try:
                    tempx = qmax
                    tempy = model.run(qmax)
                    theory.x.append(tempx)
                    theory.y.append(tempy)
                except:
                        wx.PostEvent(self.parent, StatusEvent(status="fitting \
                        skipping point x %g %s" %(qmax, sys.exc_value)))
                try:
                    from sans.guicomm.events import NewPlotEvent
                    #print"fitting: theory",theory
                    wx.PostEvent(self.parent, NewPlotEvent(plot=theory, title="Analytical model"))
                except:
                    raise
                    print "SimView.complete1D: could not import sans.guicomm.events"
            
            
    def _on_model_menu(self, evt):
        """
            Plot a theory from a model selected from the menu
        """
        #name = evt.model.__class__.__name__
        name="Model View"
        self.fit_panel.add_model_page(evt.model,name)       
        self.draw_model(evt.model)
        
    def draw_model(self,model):
        x = pylab.arange(0.001, 0.1, 0.001)
        xlen = len(x)
        dy = numpy.zeros(xlen)
        y = numpy.zeros(xlen)
        
        for i in range(xlen):
            y[i] = model.run(x[i])
            dy[i] = math.sqrt(math.fabs(y[i]))
        try:
           
            new_plot = Theory1D(x, y)
            #new_plot.name = evt.model.__class__.__name__
            new_plot.name ="Fitness"
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
         
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Analytical model"))
        except:
            print "SimView.complete1D: could not import sans.guicomm.events"

if __name__ == "__main__":
    i = Plugin()
    
    
    
    
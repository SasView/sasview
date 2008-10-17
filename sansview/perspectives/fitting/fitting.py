import os,os.path, re
import sys, wx, logging
import string, numpy, pylab, math

from copy import deepcopy 
from danse.common.plottools.plottables import Data1D, Theory1D, Data2D

from sans.guiframe.data_loader import MetaData1D, MetaTheory1D, MetaData2D
from danse.common.plottools.PlotPanel import PlotPanel
from sans.guicomm.events import NewPlotEvent, StatusEvent  
from sans.fit.AbstractFitEngine import Model,Data,FitData1D,FitData2D
from fitproblem import FitProblem
from fitpanel import FitPanel

import models
import fitpage1D,fitpage2D
import park

class Plugin:
    """
        Fitting plugin is used to perform fit 
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
        self._fit_engine = 'scipy'
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
        id3 = wx.NewId()
        self.menu1.AppendCheckItem(id3, "park") 
        wx.EVT_MENU(owner, id3, self._onset_engine)
        
        #menu for model
        menu2 = wx.Menu()
        self.menu_mng.populate_menu(menu2, owner)
        id2 = wx.NewId()
        owner.Bind(models.EVT_MODEL,self._on_model_menu)
        self.fit_panel.set_owner(owner)
        self.fit_panel.set_model_list(self.menu_mng.get_model_list())
        owner.Bind(fitpage1D.EVT_MODEL_BOX,self._on_model_panel)
        owner.Bind(fitpage2D.EVT_MODEL_BOX,self._on_model_panel)
        #create  menubar items
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
            if item.__class__.__name__ is "MetaData2D":
                return [["Fit Data2D", "Dialog with fitting parameters ", self._onSelect]] 
            else:
                if item.name==graph.selected_plottable and (item.__class__.__name__ is  "MetaData1D"or \
                                        item.__class__.__name__ is  "Data1D" ):
                    return [["Fit Data1D", "Dialog with fitting parameters ", self._onSelect]] 
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
        self.page_finder = {}
        #index number to create random model name
        self.index_model = 0
        #create the fitting panel
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
            if item.name == self.panel.graph.selected_plottable or item.__class__.__name__ is "MetaData2D":
                #find a name for the page created for notebook
                try:
                    page = self.fit_panel.add_fit_page(item)
                    # add data associated to the page created
                    
                    if page !=None:    
                        
                        #create a fitproblem storing all link to data,model,page creation
                        self.page_finder[page]= FitProblem()
                        self.page_finder[page].add_data(item)
                except:
                    wx.PostEvent(self.parent, StatusEvent(status="Creating Fit page: %s"\
                    %sys.exc_value))
    def schedule_for_fit(self,value=0,fitproblem =None):  
        """
        
        """   
        if fitproblem !=None:
            fitproblem.schedule_tofit(value)
        else:
            current_pg=self.fit_panel.get_current_page() 
            for page, val in self.page_finder.iteritems():
                if page ==current_pg :
                    val.schedule_tofit(value)
                    break
                      
                    
    def get_page_finder(self):
        """ @return self.page_finder used also by simfitpage.py"""  
        return self.page_finder 
    
    
    def set_page_finder(self,modelname,names,values):
        """
             Used by simfitpage.py to reset a parameter given the string constrainst.
             @param modelname: the name ot the model for with the parameter has to reset
             @param value: can be a string in this case.
             @param names: the paramter name
             @note: expecting park used for fit.
        """  
        sim_page=self.fit_panel.get_page(0)
        for page, value in self.page_finder.iteritems():
            if page != sim_page:
                list=value.get_model()
                model=list[0]
                #print "fitting",model.name,modelname
                if model.name== modelname:
                    value.set_model_param(names,values)
                    break

   
                            
    def split_string(self,item): 
        """
            receive a word containing dot and split it. used to split parameterset
            name into model name and parameter name example:
            paramaterset (item) = M1.A
            @return model_name =M1 , parameter name =A
        """
        if string.find(item,".")!=-1:
            param_names= re.split("\.",item)
            model_name=param_names[0]
            param_name=param_names[1]  
            return model_name,param_name
        
        
    def _single_fit_completed(self,result,pars,cpage,qmin,qmax,ymin=None, ymax=None):
        """
            Display fit result on one page of the notebook.
            @param result: result of fit 
            @param pars: list of names of parameters fitted
            @param current_pg: the page where information will be displayed
            @param qmin: the minimum value of x to replot the model 
            @param qmax: the maximum value of x to replot model
          
        """
        try:
            for page, value in self.page_finder.iteritems():
                if page==cpage :
                    #fitdata = value.get_data()
                    list = value.get_model()
                    model= list[0]
                    break
            i = 0
#            print "fitting: single fit pars ", pars
            for name in pars:
                if result.pvec.__class__==numpy.float64:
                    model.setParam(name,result.pvec)
                else:
                    model.setParam(name,result.pvec[i])
#                    print "fitting: single fit", name, result.pvec[i]
                    i += 1
#            print "fitting result : chisqr",result.fitness
#            print "fitting result : pvec",result.pvec
#            print "fitting result : stderr",result.stderr
            
            cpage.onsetValues(result.fitness, result.pvec,result.stderr)
            self.plot_helper(currpage=cpage,qmin=qmin,qmax=qmax,ymin=ymin, ymax=ymax)
        except:
            raise
            wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
            
       
    def _simul_fit_completed(self,result,qmin,qmax,ymin=None, ymax=None):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        try:
            for page, value in self.page_finder.iteritems():
                if value.get_scheduled()==1:
                    #fitdata = value.get_data()
                    list = value.get_model()
                    model= list[0]
                   
                    small_out = []
                    small_cov = []
                    i = 0
                    #Separate result in to data corresponding to each page
                    for p in result.parameters:
                        model_name,param_name = self.split_string(p.name)  
                        if model.name == model_name:
                            small_out.append(p.value )
                            small_cov.append(p.stderr)
                            model.setParam(param_name,p.value)  
                    # Display result on each page 
                    page.onsetValues(result.fitness, small_out,small_cov)
                    #Replot model
                    self.plot_helper(currpage= page,qmin= qmin,qmax= qmax,ymin=ymin, ymax=ymax) 
        except:
             wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
            
    
    def _on_single_fit(self,id=None,qmin=None,qmax=None,ymin=None,ymax=None):
        """ 
            perform fit for the  current page  and return chisqr,out and cov
            @param engineName: type of fit to be performed
            @param id: unique id corresponding to a fit problem(model, set of data)
            @param model: model to fit
            
        """
        #print "in single fitting"
        #set an engine to perform fit
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        #Setting an id to store model and data in fit engine
        if id==None:
            id=0
        self.id = id
        page_fitted=None
        fit_problem=None
        #Get information (model , data) related to the page on 
        #with the fit will be perform
        #current_pg=self.fit_panel.get_current_page() 
        #simul_pg=self.fit_panel.get_page(0)
            
        for page, value in self.page_finder.iteritems():
            if  value.get_scheduled() ==1 :
                metadata = value.get_data()
                list=value.get_model()
                model=list[0]
                #Create list of parameters for fitting used
                pars=[]
                templist=[]
                try:
                    #templist=current_pg.get_param_list()
                    templist=page.get_param_list()
                    for element in templist:
                        pars.append(str(element[0].GetLabelText()))
                    pars.sort()
                    #Do the single fit
                    self.fitter.set_model(Model(model), self.id, pars) 
                    self.fitter.set_data(metadata,self.id,qmin,qmax)
                    self.fitter.select_problem_for_fit(Uid=self.id,value=value.get_scheduled())
                    page_fitted=page
                    self.id+=1
                    self.schedule_for_fit( 0,value) 
                except:
                    wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                    return
                # make sure to keep an alphabetic order 
                #of parameter names in the list      
        try:
            result=self.fitter.fit()
            #self._single_fit_completed(result,pars,current_pg,qmin,qmax)
            print "single_fit: result",result.fitness,result.pvec,result.stderr
            #self._single_fit_completed(result,pars,page,qmin,qmax)
            self._single_fit_completed(result,pars,page_fitted,qmin,qmax,ymin,ymax)
        except:
            raise
            wx.PostEvent(self.parent, StatusEvent(status="Single Fit error: %s" % sys.exc_value))
            return
         
    def _on_simul_fit(self, id=None,qmin=None,qmax=None, ymin=None, ymax=None):
        """ 
            perform fit for all the pages selected on simpage and return chisqr,out and cov
            @param engineName: type of fit to be performed
            @param id: unique id corresponding to a fit problem(model, set of data)
             in park_integration
            @param model: model to fit
            
        """
        #set an engine to perform fit
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        
        #Setting an id to store model and data
        if id==None:
             id = 0
        self.id = id
        
        for page, value in self.page_finder.iteritems():
            try:
                if value.get_scheduled()==1:
                    metadata = value.get_data()
                    list = value.get_model()
                    model= list[0]
                    #Create dictionary of parameters for fitting used
                    pars = []
                    templist = []
                    templist = page.get_param_list()
                    for element in templist:
                        try:
                            name = str(element[0].GetLabelText())
                            pars.append(name)
                        except:
                            wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                            return
                    new_model=Model(model)
                    param=value.get_model_param()
                    
                    if len(param)>0:
                        for item in param:
                            param_value = item[1]
                            param_name = item[0]
                            #print "fitting ", param,param_name, param_value
                           
                            #new_model.set( model.getParam(param_name[0])= param_value)
                            #new_model.set( exec"%s=%s"%(param_name[0], param_value))
                            #new_model.set( exec "%s"%(param_nam) = param_value)
                            new_model.parameterset[ param_name].set( param_value )
                            
                    self.fitter.set_model(new_model, self.id, pars) 
                    self.fitter.set_data(metadata,self.id,qmin,qmax,ymin,ymax)
                    self.fitter.select_problem_for_fit(Uid=self.id,value=value.get_scheduled())
                    self.id += 1 
            except:
                wx.PostEvent(self.parent, StatusEvent(status="Fitting error: %s" % sys.exc_value))
                return 
        #Do the simultaneous fit
        try:
            result=self.fitter.fit()
            self._simul_fit_completed(result,qmin,qmax,ymin,ymax)
        except:
            wx.PostEvent(self.parent, StatusEvent(status="Simultaneous Fitting error: %s" % sys.exc_value))
            return
        
        
    def _onset_engine(self,event):
        """ set engine to scipy"""
        if self._fit_engine== 'park':
            self._on_change_engine('scipy')
        else:
            self._on_change_engine('park')
        wx.PostEvent(self.parent, StatusEvent(status="Engine set to: %s" % self._fit_engine))
  
    
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
            current_pg.set_panel(model)
            
            try:
                metadata=self.page_finder[current_pg].get_data()
                M_name="M"+str(self.index_model)+"= "+name+"("+metadata.group_id+")"
            except:
                M_name="M"+str(self.index_model)+"= "+name
            model.name="M"+str(self.index_model)
            self.index_model += 1  
            
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
        
    def plot_helper(self,currpage,qmin=None,qmax=None,ymin=None,ymax=None):
        """
            Plot a theory given a model and data
            @param model: the model from where the theory is derived
            @param currpage: page in a dictionary referring to some data
        """
        if self.fit_panel.get_page_count() >1:
            for page in self.page_finder.iterkeys():
                if  page==currpage :  
                    data=self.page_finder[page].get_data()
                    list=self.page_finder[page].get_model()
                    model=list[0]
                    break 
            
            if data!=None and data.__class__.__name__ != 'MetaData2D':
                theory = Theory1D(x=[], y=[])
                theory.name = "Model"
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
            else:
                theory=Data2D(data.image, data.err_image)
                theory.x_bins= data.x_bins
                theory.y_bins= data.y_bins
                tempy=[]
                if qmin==None:
                    qmin=data.xmin
                if qmax==None:
                    qmin=data.xmax
                if ymin==None:
                    ymin=data.ymin
                if ymax==None:
                    qmin=data.ymax
              
                for i in range(len(data.y_bins)):
                    if data.y_bins[i]>= ymin and data.y_bins[i]<= ymax:
                        for j in range(len(data.x_bins)):
                            if data.x_bins[i]>= xmin and data.x_bins[i]<= xmax:
                                theory.image= model.runXY([data.x_bins[j],data.y_bins[i]])
               
                    
                    #print "fitting : plot_helper:", theory.image
                #print data.image
                #theory.image=model.runXY(data.image)
               
                #print "fitting : plot_helper:",theory.image
                theory.zmin= data.zmin
                theory.zmax= data.zmax
                theory.xmin= data.xmin
                theory.xmax= data.xmax
                theory.ymin= data.ymin
                theory.ymax= data.ymax
                
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory, title="Analytical model"))
        
        
    def _on_model_menu(self, evt):
        """
            Plot a theory from a model selected from the menu
        """
        name="Model View"
        model=evt.modelinfo.model()
        description=evt.modelinfo.description
        self.fit_panel.add_model_page(model,description,name)       
        self.draw_model(model)
        
    def draw_model(self,model):
        """
             draw model with default data value
        """
        x = pylab.arange(0.001, 0.1, 0.001)
        xlen = len(x)
        dy = numpy.zeros(xlen)
        y = numpy.zeros(xlen)
        
        for i in range(xlen):
            y[i] = model.run(x[i])
            dy[i] = math.sqrt(math.fabs(y[i]))
        try:
           
            new_plot = Theory1D(x, y)
            new_plot.name = "Model"
            new_plot.xaxis("\\rm{Q}", 'A^{-1}')
            new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
            new_plot.group_id ="Fitness"
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Analytical model"))
        except:
            wx.PostEvent(self.parent, StatusEvent(status="fitting \
                        skipping point x %g %s" %(qmax, sys.exc_value)))

if __name__ == "__main__":
    i = Plugin()
    
    
    
    
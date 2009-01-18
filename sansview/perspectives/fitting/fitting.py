import os,os.path, re
import sys, wx, logging
import string, numpy, math

from copy import deepcopy 
from danse.common.plottools.plottables import Data1D, Theory1D,Data2D
from danse.common.plottools.PlotPanel import PlotPanel
from sans.guicomm.events import NewPlotEvent, StatusEvent  
from sans.guicomm.events import EVT_SLICER_PARS

from sans.fit.AbstractFitEngine import Model,Data,FitData1D,FitData2D
from fitproblem import FitProblem
from fitpanel import FitPanel
from fit_thread import FitThread
import models,modelpage
import fitpage1D,fitpage2D
import park
DEFAULT_BEAM = 0.005
import time
import thread
print "main",thread.get_ident()

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
        self.mypanels=[]
        self.calc_thread = None
        self.done = False
        # Start with a good default
        self.elapsed = 0.022
        self.fitter  = None
       
        #Flag to let the plug-in know that it is running standalone
        self.standalone=True
        ## Fit engine
        self._fit_engine = 'scipy'
        self.enable_model2D=False
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
        #owner.Bind(modelpage.EVT_MODEL,self._on_model_menu)
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
        from helpDialog import  HelpWindow
        dialog = HelpWindow(None, -1, 'HelpWindow')
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
    
    def get_context_menu(self, graph=None):
        """
            Get the context menu items available for P(r)
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        self.graph=graph
        for item in graph.plottables:
            if item.__class__.__name__ is "Data2D":
                return [["Select data  for Fitting",\
                          "Dialog with fitting parameters ", self._onSelect]] 
            else:
                if item.name==graph.selected_plottable and\
                 item.__class__.__name__ is  "Data1D":
                    return [["Select data  for Fitting", \
                             "Dialog with fitting parameters ", self._onSelect]] 
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
        self.parent.Bind(EVT_SLICER_PARS, self._on_slicer_event)
        #create the fitting panel
        #return [self.fit_panel]
        self.mypanels.append(self.fit_panel)
        return self.mypanels
    def _on_slicer_event(self, event):
        print "slicer event ", event.panel
        new_panel = event.panel
        # Set group ID if available
        event_id = self.parent.popup_panel(new_panel)
        #self.menu.Append(event_id, new_panel.window_caption, 
        #                 "Show %s plot panel" % new_panel.window_caption)
        # Set UID to allow us to reference the panel later
        new_panel.uid = event_id
       
        self.mypanels.append(new_panel) 
        return        
    def _on_show_panel(self, event):
        print "_on_show_panel: fitting"
      
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
            if item.name == self.panel.graph.selected_plottable or\
                 item.__class__.__name__ is "Data2D":
                #find a name for the page created for notebook
                try:
                    page, model_name = self.fit_panel.add_fit_page(item)
                    # add data associated to the page created
                    
                    if page !=None:    
                        
                        #create a fitproblem storing all link to data,model,page creation
                        self.page_finder[page]= FitProblem()
                        self.page_finder[page].save_model_name(model_name)  
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
        
   
    def _single_fit_completed(self,result,pars,cpage,qmin,qmax,elapsed,ymin=None, ymax=None):
        """
            Display fit result on one page of the notebook.
            @param result: result of fit 
            @param pars: list of names of parameters fitted
            @param current_pg: the page where information will be displayed
            @param qmin: the minimum value of x to replot the model 
            @param qmax: the maximum value of x to replot model
          
        """
        #self.done = True
        #wx.PostEvent(self.parent, StatusEvent(status="Fitting Completed: %g" % elapsed))
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
            
       
    def _simul_fit_completed(self,result,qmin,qmax, elapsed,pars=None,cpage=None, ymin=None, ymax=None):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        wx.PostEvent(self.parent, StatusEvent(status="Fitting Completed: %g" % elapsed))
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
                smearer= value.get_smearer()
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
                   
                    self.fitter.set_data(metadata,self.id,smearer, qmin,qmax)
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
            # If a thread is already started, stop it
            if self.calc_thread != None and self.calc_thread.isrunning():
                self.calc_thread.stop()
                    
            self.calc_thread =FitThread(parent =self.parent,
                                        fn= self.fitter,
                                        pars= pars,
                                        cpage= page_fitted,
                                       qmin=qmin,
                                       qmax=qmax,
                                       ymin= ymin,
                                       ymax= ymax,
                                       completefn=self._single_fit_completed,
                                       updatefn=None)
            self.calc_thread.queue()
            self.calc_thread.ready(2.5)
            #while not self.done:
                #print "when here"
             #   time.sleep(1)
            
           
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
            # If a thread is already started, stop it
            if self.calc_thread != None and self.calc_thread.isrunning():
                self.calc_thread.stop()
                    
            self.calc_thread =FitThread(parent =self.parent,
                                        fn= self.fitter,
                                       qmin=qmin,
                                       qmax=qmax,
                                       ymin= ymin,
                                       ymax= ymax,
                                       completefn= self._simul_fit_completed,
                                       updatefn=None)
            self.calc_thread.queue()
            self.calc_thread.ready(2.5)
            
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
        selected_page = self.fit_panel.get_selected_page()
        if current_pg != sim_page:
            current_pg.set_panel(model)
            model.name = self.page_finder[current_pg].get_name()
            try:
                metadata=self.page_finder[current_pg].get_data()
                M_name=model.name+"= "+name+"("+metadata.group_id+")"
            except:
                M_name=model.name+"= "+name
            #model.name="M"+str(self.index_model)
            self.index_model += 1  
            # save model name
            
            # save the name containing the data name with the appropriate model
            self.page_finder[current_pg].set_model(model,M_name)
            self.plot_helper(currpage= current_pg,qmin= None,qmax= None)
            sim_page.add_model(self.page_finder)
        
    def  set_smearer(self,smearer):     
         current_pg=self.fit_panel.get_current_page()
         self.page_finder[current_pg].set_smearer(smearer)
         
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
        
    def plot_helper(self,currpage, fitModel=None, qmin=None,qmax=None,ymin=None,ymax=None):
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
            
            if data!=None and data.__class__.__name__ != 'Data2D':
                theory = Theory1D(x=[], y=[])
                theory.name = model.name
                theory.group_id = data.group_id
                theory.id = "Model"
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
                theory=Data2D(data.data, data.err_data)
                theory.name= model.name
                theory.id= "Model"
                theory.group_id= "Model"+data.name
                theory.x_bins= data.x_bins
                theory.y_bins= data.y_bins
                tempy=[]
                if qmin==None:
                    qmin=data.xmin
                if qmax==None:
                    qmax=data.xmax
                if ymin==None:
                    ymin=data.ymin
                if ymax==None:
                    ymax=data.ymax
                    
                theory.data = numpy.zeros((len(data.y_bins),len(data.x_bins)))
                for i in range(len(data.y_bins)):
                    if data.y_bins[i]>= ymin and data.y_bins[i]<= ymax:
                        for j in range(len(data.x_bins)):
                            if data.x_bins[i]>= qmin and data.x_bins[i]<= qmax:
                                theory.data[j][i]=model.runXY([data.x_bins[j],data.y_bins[i]])
               
                #print "fitting : plot_helper:", theory.image
                #print data.image
                #print "fitting : plot_helper:",theory.image
                theory.detector= data.detector
                theory.source= data.source
                theory.zmin= data.zmin
                theory.zmax= data.zmax
                theory.xmin= qmin
                theory.xmax= qmax
                theory.ymin= ymin
                theory.ymax= ymax
        
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory,
                                                title="Analytical model %s"%str(data.name)))
        
        
    def _on_model_menu(self, evt):
        """
            Plot a theory from a model selected from the menu
        """
        name = evt.model.__name__
        if hasattr(evt.model, "name"):
            name = evt.model.name
        model=evt.model()
        #name="Model View"
        #print "mon menu",model.name
        description=model.description
        #self.fit_panel.add_model_page(model,description,name)  
    
        self.draw_model(model=model,name=name)
        
    def draw_model(self,model,name ,description=None,enable1D=True, enable2D=False,qmin=None, qmax=None,qstep=None):
        """
             draw model with default data value
        """
        
        self.fit_panel.add_model_page(model=model,description=model.description,page_title=name) 
        self._draw_model2D(model=model,
                           description=model.description,
                           enable2D= enable2D,
                           qmin=qmin,
                           qmax=qmax,
                           qstep=qstep)
        self._draw_model1D(model,name,model.description, enable1D,qmin,qmax, qstep)
       
    def _draw_model1D(self,model,name,description=None, enable1D=True,qmin=None,qmax=None, qstep=None):
        
        if enable1D:
            if qmin==None:
                qmin= 0.001
            if qmax==None:
                qmax= 1.0
            if qstep ==None:
                qstep =100
           
            #print "x in data1D",qmin,qmax
            #x = numpy.arange(qmin, qmax, qstep)  
            x=  numpy.linspace(start= qmin,
                               stop= qmax,
                               num= qstep,
                               endpoint=True
                               )      
            xlen= len(x)
            y = numpy.zeros(xlen)
            if not enable1D:
                for i in range(xlen):
                    y[i] = model.run(x[i])
                
                try:
                    new_plot = Theory1D(x, y)
                    new_plot.name = name
                    new_plot.xaxis("\\rm{Q}", 'A^{-1}')
                    new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
                    new_plot.id = "Model"
                    new_plot.group_id ="Model"
                    wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title="Analytical model 1D"))
                    
                except:
                    raise
            else:
                for i in range(xlen):
                    y[i] = model.run(x[i])
                #print x, y   
                try:
                    new_plot = Theory1D(x, y)
                    new_plot.name = name
                    new_plot.xaxis("\\rm{Q}", 'A^{-1}')
                    new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
                    new_plot.id ="Model"
                    new_plot.group_id ="Model"
                    wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                     title="Analytical model 1D " ))
                    
                except:
                    raise
    def update(self, output,time):
        pass
    
    def complete(self, output, elapsed, model, qmin, qmax):
       
        wx.PostEvent(self.parent, StatusEvent(status="Calc \
        complete in %g sec" % elapsed))
        #print "complete",output, model,qmin, qmax
        data = output
        theory= Data2D(data)
        #print data.detector
        #theory.detector= data.detector
        from DataLoader.data_info import Detector, Source
        
        detector = Detector()
        theory.detector=[]
        theory.detector.append(detector)
            
        theory.detector[0].pixel_size.x= 5.0
        theory.detector[0].pixel_size.y= 5.0
        theory.source= Source()
        theory.source.wavelength= 8.4
        theory.detector[0].beam_center.x= 0
        theory.detector[0].beam_center.y= 0
        theory.detector[0].distance= 13705.0
        
        theory.name= model.name
        theory.group_id ="Model"
        theory.id ="Model"
        theory.xmin= -qmax
        theory.xmax= qmax
        theory.ymin= -qmax
        theory.ymax= qmax
        print "model draw comptele xmax",theory.xmax
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory,
                         title="Analytical model 2D %s" %str(model.name)))
         
        
         
    def _draw_model2D(self,model,description=None, enable2D=False,qmin=None,qmax=None, qstep=None):
        if qmin==None:
            qmin= 0.0
        if qmax==None:
            qmax= 0.05
        if qstep ==None:
            qstep =100
       
        x=  numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )  
        y = numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )
       
        lx = len(x)
        #print x
        data=numpy.zeros([len(x),len(y)])
        self.model= model
        if enable2D:
            from model_thread import Calc2D
            self.calc_thread = Calc2D(parent =self.parent,x=x,
                                       y=y,model= self.model, 
                                       qmin=qmin,
                                       qmax=qmax,
                            completefn=self.complete,
                            updatefn=None)
            self.calc_thread.queue()
            self.calc_thread.ready(2.5)
           
   
if __name__ == "__main__":
    i = Plugin()
    
    
    
    
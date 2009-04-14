import  re
import sys, wx, logging
import string, numpy, math

#import copy,deepcopy 
from danse.common.plottools.plottables import Data1D, Theory1D,Data2D
from danse.common.plottools.PlotPanel import PlotPanel
from sans.guicomm.events import NewPlotEvent, StatusEvent  
from sans.guicomm.events import EVT_SLICER_PANEL,ERR_DATA

from sans.fit.AbstractFitEngine import Model,FitData1D,FitData2D#,Data,
from fitproblem import FitProblem
from fitpanel import FitPanel
from fit_thread import FitThread
import models
import fitpage

DEFAULT_BEAM = 0.005
DEFAULT_QMIN = 0.0
DEFAULT_QMAX = 0.1
DEFAULT_NPTS = 50
import time
import thread


(PageInfoEvent, EVT_PAGE_INFO)   = wx.lib.newevent.NewEvent()
class PlotInfo:
    """
        store some plotting field
    """
    _xunit = 'A^{-1}'
    _xaxis= "\\rm{Q}"
    _yunit = "cm^{-1}"
    _yaxis= "\\rm{Intensity} "
    id = "Model"
    group_id = "Model"
    title= None
    info= None
    
    
class Plugin:
    """
        Fitting plugin is used to perform fit 
    """
    def __init__(self):
        ## Plug-in name
        self.sub_menu = "Fitting"
        
        ## Reference to the parent window
        self.parent = None
        #Provide list of models existing in the application
        self.menu_mng = models.ModelManager()
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        #list of panel to send to guiframe
        self.mypanels=[]
        # reference to the current running thread
        self.calc_2D= None
        self.calc_1D= None
        self.calc_fit= None
        
        # Start with a good default
        self.elapsed = 0.022
        # the type of optimizer selected, park or scipy
        self.fitter  = None
        #Flag to let the plug-in know that it is running stand alone
        self.standalone=True
        ## dictionary of page closed and id 
        self.closed_page_dict ={}
        ## Fit engine
        self._fit_engine = 'scipy'
        #List of selected data
        self.selected_data_list=[]
        # Log startup
        logging.info("Fitting plug-in started")   
        # model 2D view
        self.model2D_id=None
        #keep reference of the simultaneous fit page
        self.sim_page=None
        #dictionary containing data name and error on dy of that data 
        self.err_dy={}
        
   
        
    def populate_menu(self, id, owner):
        """
            Create a menu for the Fitting plug-in
            @param id: id to create a menu
            @param owner: owner of menu
            @ return : list of information to populate the main menu
        """
        #Menu for fitting
        self.menu1 = wx.Menu()
        
        #Set park engine
        id3 = wx.NewId()
        scipy_help= "Scipy Engine: Perform Simple fit. More in Help window...."
        self.menu1.AppendCheckItem(id3, "Simple Fit  [Scipy]",scipy_help) 
        wx.EVT_MENU(owner, id3,  self._onset_engine_scipy)
        
        id3 = wx.NewId()
        park_help = "Park Engine: Perform Complex fit. More in Help window...."
        self.menu1.AppendCheckItem(id3, "Complex Fit  [Park]",park_help) 
        wx.EVT_MENU(owner, id3,  self._onset_engine_park)
        
        self.menu1.FindItemByPosition(0).Check(True)
        self.menu1.FindItemByPosition(1).Check(False)
            
        self.menu1.AppendSeparator()
        
        id1 = wx.NewId()
        simul_help = "Allow to edit fit engine with multiple model and data"
        self.menu1.Append(id1, '&Simultaneous Page',simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_sim_page)
    
        #menu for model
        menu2 = wx.Menu()
    
        self.menu_mng.populate_menu(menu2, owner)
        id2 = wx.NewId()
        owner.Bind(models.EVT_MODEL,self._on_model_menu)
      
        self.fit_panel.set_owner(owner)
        self.fit_panel.set_model_list(self.menu_mng.get_model_list())
        owner.Bind(fitpage.EVT_MODEL_BOX,self._on_model_panel)
        
        self.menu3= wx.Menu()
        id4 = wx.NewId()
        
        #create  menubar items
        return [(id, self.menu1, "Fitting"),
                (id4,self.menu3,"Averagers"),
                (id2, menu2, "Model")]
    
    def on_add_sim_page(self, event):
        """
            Create a page to access simultaneous fit option
        """
        if self.sim_page !=None:
            msg= "Simultaneous Fit page already opened"
            wx.PostEvent(self.parent, StatusEvent(status= msg))
            return 
        
        self.sim_page= self.fit_panel.add_sim_page()
        
        
        
    def help(self, evt):
        """
            Show a general help dialog. 
            TODO: replace the text with a nice image
        """
        from helpPanel import  HelpWindow
        frame = HelpWindow(None, -1, 'HelpWindow')    
        frame.Show(True)
        
        
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
               
                if item.name==graph.selected_plottable :
                    if not hasattr(item, "group_id"):
                        return []
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
        #Set the manager for the main panel
        self.fit_panel.set_manager(self)
        # List of windows used for the perspective
        self.perspective = []
        self.perspective.append(self.fit_panel.window_name)
        # take care of saving  data, model and page associated with each other
        self.page_finder = {}
        #index number to create random model name
        self.index_model = 0
        self.index_theory= 0
        self.parent.Bind(EVT_SLICER_PANEL, self._on_slicer_event)
        self.parent.Bind( ERR_DATA, self._on_data_error)
        
        #Send the fitting panel to guiframe
        self.mypanels.append(self.fit_panel)
        return self.mypanels

        
      
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


    def copy_data(self, item, dy):
        """
            receive a data 1D and the list of errors on dy
            and create a new data1D data
            @param return 
        """
        detector=None
        source=None
        info = None
        id=None
        dxl=None
        dxw=None
        if hasattr(item, "dxl"):
            dxl = item.dxl
        if hasattr(item, "dxw"):
            dxw = item.dxw
        if hasattr(item, "detector"):
            detector =item.detector
        if hasattr(item, "source"):
            source =item.source
        if hasattr(item ,"info"):
            info= item.info
        if hasattr(item,"id"):
            id = item.id
        from sans.guiframe import dataFitting 
        if item.__class__.__name__=="Data1D":
            data= dataFitting.Data1D(x=item.x, y=item.y, dy=dy, dxl=dxl, dxw=dxw)
        else:
            data= dataFitting.Theory1D(x=item.x, y=item.y, dxl=dxl, dxw=dxw)
        data.name = item.name
        data.detector = detector
        data.source = source
        ## allow to highlight data when plotted
        data.interactive = item.interactive
        ## when 2 data have the same id override the 1 st plotted
        data.id = id
        ## info is a reference to output of dataloader that can be used
        ## to save  data 1D as cansas xml file
        data.info= info
        ## If the data file does not tell us what the axes are, just assume...
        data.xaxis(item._xaxis,item._xunit)
        data.yaxis(item._yaxis,item._yunit)
        ##group_id specify on which panel to plot this data
        data.group_id = item.group_id
        return data

    def set_fit_range(self, page, qmin, qmax):
        """
            Set the fitting range of a given page
        """
        if page in self.page_finder.iterkeys():
            fitproblem= self.page_finder[page]
            fitproblem.set_range(qmin= qmin, qmax= qmax)
                    
    def schedule_for_fit(self,value=0,page=None,fitproblem =None):  
        """
            Set the fit problem field to 0 or 1 to schedule that problem to fit.
            Schedule the specified fitproblem or get the fit problem related to 
            the current page and set value.
            @param value : integer 0 or 1 
            @param fitproblem: fitproblem to schedule or not to fit
        """   
        if fitproblem !=None:
            fitproblem.schedule_tofit(value)
        else:
            if page in self.page_finder.iterkeys():
                fitproblem= self.page_finder[page]
                fitproblem.schedule_tofit(value)
          
                      
                    
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
        sim_page= self.sim_page
        for page, value in self.page_finder.iteritems():
            if page != sim_page:
                list=value.get_model()
                model = list[0]
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
        
   
    def stop_fit(self):
        """
            Stop the fit engine
        """
        if self.calc_fit!= None and self.calc_thread.isrunning():
            self.calc_thread.stop()
            wx.PostEvent(self.parent, StatusEvent(status="Fitting  \
                is cancelled" , type="stop"))
            
    
      
    def set_smearer(self,smearer, qmin=None, qmax=None):
        """
            Get a smear object and store it to a fit problem
            @param smearer: smear object to allow smearing data
        """   
        current_pg=self.fit_panel.get_current_page()
        self.page_finder[current_pg].set_smearer(smearer)
        ## draw model 1D with smeared data
        data =  self.page_finder[current_pg].get_plotted_data()
        model = self.page_finder[current_pg].get_model()
        ## if user has already selected a model to plot
        ## redraw the model with data smeared
        
        smearer =self.page_finder[current_pg].get_smearer()
        self.draw_model( model=model, data= data, smearer= smearer,
                qmin= qmin, qmax= qmax)

    
    
    def draw_model(self, model, data= None,smearer= None,
                   enable1D= True, enable2D= False,
                   qmin= DEFAULT_QMIN, qmax= DEFAULT_QMAX, qstep= DEFAULT_NPTS):
        """
             Draw model.
             @param model: the model to draw
             @param name: the name of the model to draw
             @param data: the data on which the model is based to be drawn
             @param description: model's description
             @param enable1D: if true enable drawing model 1D
             @param enable2D: if true enable drawing model 2D
             @param qmin:  Range's minimum value to draw model
             @param qmax:  Range's maximum value to draw model
             @param qstep: number of step to divide the x and y-axis
             
        """
        ## draw model 1D with no loaded data
        self._draw_model1D( model= model, data= data,enable1D=enable1D, smearer= smearer,
                           qmin= qmin, qmax= qmax, qstep= qstep )
        ## draw model 2D with no initial data
        self._draw_model2D(model=model,
                           data = data,
                           enable2D= enable2D,
                           qmin=qmin,
                           qmax=qmax,
                           qstep=qstep)
        
  
                        
    def onFit(self):
        """
            perform fit 
        """
        ##  count the number of fitproblem schedule to fit 
        fitproblem_count= 0
        for value in self.page_finder.itervalues():
            if value.get_scheduled()==1:
                fitproblem_count += 1
                
        ## if simultaneous fit change automatically the engine to park
        if fitproblem_count >1:
            self._on_change_engine(engine='park')
            
        from sans.fit.Fitting import Fit
        self.fitter= Fit(self._fit_engine)
        
        if self._fit_engine=="park":
            engineType="Simultaneous Fit"
        else:
            engineType="Single Fit"
            
        fproblemId = 0
        current_pg=None
        for page, value in self.page_finder.iteritems():
            try:
                if value.get_scheduled()==1:
                    #Get list of parameters name to fit
                    pars = []
                    templist = []
                    templist = page.get_param_list()
                    for element in templist:
                        name = str(element[0].GetLabelText())
                        pars.append(name)
                    #Set Engine  (model , data) related to the page on 
                    self._fit_helper( current_pg=page, value=value,pars=pars,
                                      id=fproblemId, title= engineType ) 
                    fproblemId += 1 
                    current_pg= page
            except:
                msg= "%s error: %s" % (engineType,sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status= msg ))
                return 
        #Do the simultaneous fit
        try:
            ## If a thread is already started, stop it
            if self.calc_fit!= None and self.calc_fit.isrunning():
                self.calc_fit.stop()
            ## perform single fit
            if self._fit_engine=="scipy":
                qmin, qmax= current_pg.get_range()
                self.calc_fit=FitThread(parent =self.parent,
                                        fn= self.fitter,
                                       cpage=current_pg,
                                       pars= pars,
                                       completefn= self._single_fit_completed,
                                       updatefn=None)
                      
            else:
                ## Perform more than 1 fit at the time
                self.calc_fit=FitThread(parent =self.parent,
                                        fn= self.fitter,
                                       completefn= self._simul_fit_completed,
                                       updatefn=None)
            self.calc_fit.queue()
            self.calc_fit.ready(2.5)
            
        except:
            msg= "%s error: %s" % (engineType,sys.exc_value)
            wx.PostEvent(self.parent, StatusEvent(status= msg ))
            return 
              
              
    def _add_page_onmenu(self, name,fitproblem=None):
        """
            Add name of a closed page of fitpanel in a menu 
        """
        list = self.menu1.GetMenuItems()
        for item in list:
            if name == item.GetItemLabel():
                self.closed_page_dict[name][1] = fitproblem
                
        if not name in self.closed_page_dict.keys():    
            # Post paramters
            event_id = wx.NewId()
            self.menu1.Append(event_id, name, "Show %s fit panel" % name)
            self.closed_page_dict[name]= [event_id, fitproblem]
            wx.EVT_MENU(self.parent,event_id,  self._open_closed_page)
        
        
    def _open_closed_page(self, event):    
        """
            reopen a closed page
        """
        for name, value in self.closed_page_dict.iteritems():
            if event.GetId() in value:
                id,fitproblem = value
                if name !="Model":
                    data= fitproblem.get_fit_data()
                    page = self.fit_panel.add_fit_page(data= data,reset=True)
                    if fitproblem != None:
                        self.page_finder[page]=fitproblem
                        if self.sim_page != None:
                            self.sim_page.draw_page()
                            
                else:
                    model = fitproblem
                    self.fit_panel.add_model_page(model=model, topmenu=True,
                                                  reset= True)
                    break
        
        
    def _reset_schedule_problem(self, value=0):
        """
             unschedule or schedule all fitproblem to be fit
        """
        for page, fitproblem in self.page_finder.iteritems():
            fitproblem.schedule_tofit(value)
            
    def _fit_helper(self,current_pg,pars,value, id, title="Single Fit " ):
        """
            helper for fitting
        """
        metadata = value.get_fit_data()
        model = value.get_model()
        smearer = value.get_smearer()
        qmin , qmax = value.get_range()
        self.fit_id =id
        #Create list of parameters for fitting used
        templist=[]
        pars=pars
        try:
            ## create a park model and reset parameter value if constraint
            ## is given
            new_model = Model(model)
            param = value.get_model_param()
            if len(param)>0:
                for item in param:
                    param_value = item[1]
                    param_name = item[0]
                    ## check if constraint
                    if param_value !=None and param_name != None:
                        new_model.parameterset[ param_name].set( param_value )
            
            #Do the single fit
            self.fitter.set_model(new_model, self.fit_id, pars)
            
            self.fitter.set_data(data=metadata,Uid=self.fit_id,
                                 smearer=smearer,qmin= qmin,qmax=qmax )
           
            self.fitter.select_problem_for_fit(Uid= self.fit_id,
                                               value= value.get_scheduled())
            value.clear_model_param()
        except:
            msg= title +" error: %s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status= msg ))
            return
       
    def _onSelect(self,event):
        """ 
            when Select data to fit a new page is created .Its reference is 
            added to self.page_finder
        """
        self.panel = event.GetEventObject()
        for item in self.panel.graph.plottables:
            if item.name == self.panel.graph.selected_plottable:
                ## put the errors values back to the model if the errors were hiden
                ## before sending them to the fit engine
                if len(self.err_dy)>0:
                    if item.name in  self.err_dy.iterkeys():
                        dy= self.err_dy[item.name]
                        data= self.copy_data(item, dy)
                    else:
                        data= item
                else:
                    if item.dy==None:
                        dy= numpy.zeros(len(item.y))
                        dy[dy==0]=1
                        data= self.copy_data(item, dy)
                    else:
                        data= item
            else:
                data= item
            ## create anew page                   
            if item.name == self.panel.graph.selected_plottable or\
                 item.__class__.__name__ is "Data2D":
                try:
                    page = self.fit_panel.add_fit_page(data)
                    # add data associated to the page created
                    if page !=None:   
                        #create a fitproblem storing all link to data,model,page creation
                        self.page_finder[page]= FitProblem()
                        ## item is almost the same as data but contains
                        ## axis info for plotting 
                        self.page_finder[page].add_plotted_data(item)
                        self.page_finder[page].add_fit_data(data)
                        
                        wx.PostEvent(self.parent, StatusEvent(status="Page Created"))
                    else:
                        wx.PostEvent(self.parent, StatusEvent(status="Page was already Created"))
                except:
                    raise
                    #wx.PostEvent(self.parent, StatusEvent(status="Creating Fit page: %s"\
                    #%sys.exc_value))
                    #return
    
    def _single_fit_completed(self,result,pars,cpage, elapsed=None):
        """
            Display fit result on one page of the notebook.
            @param result: result of fit 
            @param pars: list of names of parameters fitted
            @param current_pg: the page where information will be displayed
            @param qmin: the minimum value of x to replot the model 
            @param qmax: the maximum value of x to replot model
          
        """
        wx.PostEvent(self.parent, StatusEvent(status="Single fit \
        complete! " , type="stop"))
        try:
            for page, value in self.page_finder.iteritems():
                if page==cpage :
                    model= value.get_model()
                    break
            i = 0
            for name in pars:
                if result.pvec.__class__==numpy.float64:
                    model.setParam(name,result.pvec)
                else:
                    model.setParam(name,result.pvec[i])
                    i += 1
            ## Reset values of the current page to fit result
            cpage.onsetValues(result.fitness, result.pvec,result.stderr)
            ## plot the current model with new param
            metadata =  self.page_finder[cpage].get_fit_data()
            model = self.page_finder[cpage].get_model()
            qmin, qmax= self.page_finder[cpage].get_range()
            smearer =self.page_finder[cpage].get_smearer()
            #Replot models
            msg= "Single Fit completed. plotting... %s:"%model.name
            wx.PostEvent(self.parent, StatusEvent(status="%s " % msg))
            self.draw_model( model=model, data= metadata, smearer= smearer,
                             qmin= qmin, qmax= qmax)
            
        except:
            msg= "Single Fit completed but Following error occurred:"
            wx.PostEvent(self.parent, StatusEvent(status="%s %s" % (msg, sys.exc_value)))
            return
       
       
    def _simul_fit_completed(self,result,pars=None,cpage=None, elapsed=None):
        """
            Parameter estimation completed, 
            display the results to the user
            @param alpha: estimated best alpha
            @param elapsed: computation time
        """
        wx.PostEvent(self.parent, StatusEvent(status="Simultaneous fit \
        complete ", type="stop"))
       
        ## fit more than 1 model at the same time 
        try:
            for page, value in self.page_finder.iteritems():
                if value.get_scheduled()==1:
                    model = value.get_model()
                    metadata =  value.get_plotted_data()
                    small_out = []
                    small_cov = []
                    i = 0
                    #Separate result in to data corresponding to each page
                    for p in result.parameters:
                        model_name,param_name = self.split_string(p.name)  
                        if model.name == model_name:
                            p_name= model.name+"."+param_name
                            if p.name == p_name:
                                small_out.append(p.value )
                                model.setParam(param_name,p.value) 
                                if p.stderr==None:
                                    p.stderr=numpy.nan
                                    small_cov.append(p.stderr)
                                   
                                else:
                                    small_cov.append(p.stderr)
                            else:
                                value= model.getParam(param_name)
                                small_out.append(value )
                                small_cov.append(numpy.nan)
                    # Display result on each page 
                    page.onsetValues(result.fitness, small_out,small_cov)
                    #Replot models
                    msg= "Simultaneous Fit completed. plotting... %s:"%model.name
                    wx.PostEvent(self.parent, StatusEvent(status="%s " % msg))
                    qmin, qmax= page.get_range()
                    smearer =self.page_finder[page].get_smearer()
                    self.draw_model( model=model, data= metadata, smearer=smearer,
                                     qmin= qmin, qmax= qmax)
                    
        except:
             msg= "Simultaneous Fit completed but Following error occurred: "
             wx.PostEvent(self.parent, StatusEvent(status="%s%s" %(msg,sys.exc_value)))
             return 
             
                           
        
    def _on_show_panel(self, event):
        print "_on_show_panel: fitting"
      
      
    def _onset_engine_park(self,event):
        """ 
            set engine to park
        """
        self._on_change_engine('park')
       
       
    def _onset_engine_scipy(self,event):
        """ 
            set engine to scipy
        """
        self._on_change_engine('scipy')
       
    def _on_slicer_event(self, event):
        """
            Receive a panel as event and send it to guiframe 
            @param event: event containing a panel
        """
        if event.panel!=None:
            new_panel = event.panel
            # Set group ID if available
            event_id = self.parent.popup_panel(new_panel)
            self.menu3.Append(event_id, new_panel.window_caption, 
                             "Show %s plot panel" % new_panel.window_caption)
            # Set UID to allow us to reference the panel later
            new_panel.uid = event_id
            new_panel
            self.mypanels.append(new_panel) 
        return  
    
      
    def _return_engine_type(self):
        """
            return the current type of engine
        """
        return self._fit_engine
     
     
    def _on_change_engine(self, engine='park'):
        """
            Allow to select the type of engine to perform fit 
            @param engine: the key work of the engine
        """
        ## saving fit engine name
        self._fit_engine = engine
        ## change menu item state
        if engine=="park":
            self.menu1.FindItemByPosition(0).Check(False)
            self.menu1.FindItemByPosition(1).Check(True)
        else:
            self.menu1.FindItemByPosition(0).Check(True)
            self.menu1.FindItemByPosition(1).Check(False)
            
        ## post a message to status bar
        wx.PostEvent(self.parent, StatusEvent(status="Engine set to: %s" % self._fit_engine))
   
        ## Bind every open fit page with a newevent to know the current fitting engine
        import fitpage
        event= fitpage.FitterTypeEvent()
        event.type = self._fit_engine
        for key in self.page_finder.keys():
            wx.PostEvent(key, event)
       
   
    def _on_model_panel(self, evt):
        """
            react to model selection on any combo box or model menu.plot the model  
            @param evt: wx.combobox event
        """
        model = evt.model
        
        if model ==None:
            return
       
        current_pg = self.fit_panel.get_current_page() 
        ## make sure nothing is done on self.sim_page
        ## example trying to call set_panel on self.sim_page
        if current_pg != self.sim_page :
           
            if self.page_finder[current_pg].get_model()== None :
                
                model.name="M"+str(self.index_model)
                self.index_model += 1  
            else:
                model.name= self.page_finder[current_pg].get_model().name
                
            metadata = self.page_finder[current_pg].get_plotted_data()
            
            # save the name containing the data name with the appropriate model
            self.page_finder[current_pg].set_model(model)
            qmin, qmax= current_pg.get_range()
            self.page_finder[current_pg].set_range(qmin=qmin, qmax=qmax)
           
            # save model name
            self.draw_model( model=model, data= metadata, qmin=qmin, qmax=qmax)
            
            if self.sim_page!=None:
                self.sim_page.draw_page()
        
        
  
    def _on_model_menu(self, evt):
        """
            Plot a theory from a model selected from the menu
            @param evt: wx.menu event
        """
        model = evt.model
     
        # Create a model page. If a new page is created, the model
        # will be plotted automatically. If a page already exists,
        # the content will be updated and the plot refreshed
        self.fit_panel.add_model_page(model,topmenu=True)
    
   
    
    
    def _update1D(self,x, output):
        """
            Update the output of plotting model 1D
        """
        self.calc_thread.ready(1)
    
    def _fill_default_model2D(self, theory, qmax,qstep, qmin=None):
        """
            fill Data2D with default value 
            @param theory: Data2D to fill
        """
        from DataLoader.data_info import Detector, Source
        
        detector = Detector()
        theory.detector.append(detector) 
            
        theory.detector[0].distance=1e+32
        theory.source= Source()
        theory.source.wavelength=2*math.pi/1e+32
      
        ## Create detector for Model 2D
        xmax=2*theory.detector[0].distance*math.atan(\
                            qmax/(4*math.pi/theory.source.wavelength))
        
        theory.detector[0].pixel_size.x= xmax/(qstep/2-0.5)
        theory.detector[0].pixel_size.y= xmax/(qstep/2-0.5)
        theory.detector[0].beam_center.x= qmax
        theory.detector[0].beam_center.y= qmax
        ## create x_bins and y_bins of the model 2D
        distance   = theory.detector[0].distance
        pixel      = qstep/2-1
        theta      = pixel / distance / qstep#100.0
        wavelength = theory.source.wavelength
        pixel_width_x = theory.detector[0].pixel_size.x
        pixel_width_y = theory.detector[0].pixel_size.y
        center_x      = theory.detector[0].beam_center.x/pixel_width_x
        center_y      = theory.detector[0].beam_center.y/pixel_width_y
        
        
        size_x, size_y= numpy.shape(theory.data)
        for i_x in range(size_x):
            theta = (i_x-center_x)*pixel_width_x / distance 
            qx = 4.0*math.pi/wavelength * math.tan(theta/2.0)
            theory.x_bins.append(qx)    
        for i_y in range(size_y):
            theta = (i_y-center_y)*pixel_width_y / distance 
            qy =4.0*math.pi/wavelength * math.tan(theta/2.0)
            theory.y_bins.append(qy)
           
        theory.group_id ="Model"
        theory.id ="Model"
        ## determine plot boundaries
        theory.xmin= -qmax
        theory.xmax= qmax
        theory.ymin= -qmax
        theory.ymax= qmax
        
        
    def _get_plotting_info(self, data=None):
        """
            get plotting info from data if data !=None
            else use some default
        """
        my_info = PlotInfo()
        if data !=None:
            if hasattr(data,"info"):
                x_name, x_units = data.get_xaxis() 
                y_name, y_units = data.get_yaxis() 
                
                my_info._xunit = x_units
                my_info._xaxis = x_name
                my_info._yunit = y_units
                my_info._yaxis = y_name
                
            my_info.title= data.name
            if hasattr(data, "info"):
                my_info.info= data.info
            if hasattr(data, "group_id"):
                my_info.group_id= data.group_id
        
        return my_info
                
    def _complete1D(self, x,y, elapsed,model,data=None):
        """
            Complete plotting 1D data
        """ 
        try:
            
            new_plot = Theory1D(x=x, y=y)
            my_info = self._get_plotting_info( data)
            new_plot.name = model.name
            new_plot.id = my_info.id
            new_plot.group_id = my_info.group_id
            
            new_plot.xaxis( my_info._xaxis,  my_info._xunit)
            new_plot.yaxis( my_info._yaxis, my_info._yunit)
            if data!=None:
                if new_plot.id == data.id:
                    new_plot.id += "Model"
         
            # Pass the reset flag to let the plotting event handler
            # know that we are replacing the whole plot
            title= my_info.title
            if title== None:
                title="Analytical model 1D "
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                             title= str(title), reset=True ))
            else:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                             title= str(title)))
            
        except:
            msg= " Error occurred when drawing %s Model 1D: "%new_plot.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg ))
            return  
        
                 
    
        
    def _update2D(self, output,time=None):
        """
            Update the output of plotting model
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ",type="update"))
        self.calc_thread.ready(0.01)
        
        
    def _complete2D(self, image,data, model,  elapsed,qmin, qmax,qstep=DEFAULT_NPTS):
        """
            Complete get the result of modelthread and create model 2D
            that can be plot.
        """
        msg = "Calc complete !"
        wx.PostEvent( self.parent, StatusEvent( status= msg , type="stop" ))
    
        err_image = numpy.zeros(numpy.shape(image))
        err_image[err_image==0]= 1
        theory= Data2D(image= image , err_image= err_image)
        theory.name= model.name
        
        if data ==None:
            self._fill_default_model2D(theory= theory, qmax=qmax,qstep=qstep, qmin= qmin)
        
        else:
            theory.id= "Model"
            theory.group_id= "Model"+data.name
            theory.x_bins= data.x_bins
            theory.y_bins= data.y_bins
            theory.detector= data.detector
            theory.source= data.source
            
            ## plot boundaries
            theory.ymin= data.ymin
            theory.ymax= data.ymax
            theory.xmin= data.xmin
            theory.xmax= data.xmax
        
        ## plot
        wx.PostEvent(self.parent, NewPlotEvent(plot=theory,
                         title="Analytical model 2D ", reset=True ))
         
    def _on_data_error(self, event):
        """
            receives and event from plotting plu-gins to store the data name and 
            their errors of y coordinates for 1Data hide and show error
        """
        self.err_dy= event.err_dy
         
    def _draw_model2D(self,model,data=None,description=None, enable2D=False,
                      qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep=DEFAULT_NPTS):
        """
            draw model in 2D
            @param model: instance of the model to draw
            @param description: the description of the model
            @param enable2D: when True allows to draw model 2D
            @param qmin: the minimum value to  draw model 2D
            @param qmax: the maximum value to draw model 2D
            @param qstep: the number of division of Qx and Qy of the model to draw
            
        """
        
        x=  numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )  
        y = numpy.linspace(start= -1*qmax,
                               stop= qmax,
                               num= qstep,
                               endpoint=True )
        ## use data info instead
        if data !=None:
            ## check if data2D to plot
            if hasattr(data, "x_bins"):
                enable2D = True
                x= data.x_bins
                y= data.y_bins
            
        if not enable2D:
            return
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if self.calc_2D != None and self.calc_2D.isrunning():
                self.calc_2D.stop()
            self.calc_2D = Calc2D(  x= x,
                                    y= y,
                                    model= model, 
                                    data = data,
                                    qmin= qmin,
                                    qmax= qmax,
                                    qstep= qstep,
                                    completefn= self._complete2D,
                                    updatefn= self._update2D )
            self.calc_2D.queue()
            
        except:
            msg= " Error occurred when drawing %s Model 2D: "%model.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg ))
            return  
   
    def _draw_model1D(self, model, data=None, smearer= None,
                qmin=DEFAULT_QMIN, qmax=DEFAULT_QMAX, qstep= DEFAULT_NPTS,enable1D= True):
        """
            Draw model 1D from loaded data1D
            @param data: loaded data
            @param model: the model to plot
        """
         
        x=  numpy.linspace(start= qmin,
                           stop= qmax,
                           num= qstep,
                           endpoint=True
                           )
        if data!=None:
            ## check for data2D
            if hasattr(data,"x_bins"):
                return
            x = data.x
            if qmin == DEFAULT_QMIN :
                qmin = min(data.x)
            if qmax == DEFAULT_QMAX:
                qmax = max(data.x)
        
        if not enable1D:
            return
    
        try:
            from model_thread import Calc1D
            ## If a thread is already started, stop it
            if self.calc_1D!= None and self.calc_1D.isrunning():
                self.calc_1D.stop()
            self.calc_1D= Calc1D( x= x,
                                  data = data,
                                  model= model, 
                                  qmin = qmin,
                                  qmax = qmax,
                                  smearer = smearer,
                                  completefn = self._complete1D,
                                  updatefn = self._update1D  )
            self.calc_1D.queue()
            
        except:
            msg= " Error occurred when drawing %s Model 1D: "%model.name
            msg+= " %s"%sys.exc_value
            wx.PostEvent( self.parent, StatusEvent(status= msg ))
            return  
            
   


   
if __name__ == "__main__":
    i = Plugin()
    
    
    
    
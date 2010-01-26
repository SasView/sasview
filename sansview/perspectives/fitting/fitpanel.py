import wx
import wx.aui
import wx.lib
import numpy
import string 


import basepage

_BOX_WIDTH = 80


class StateIterator(object):
    """
        Contains all saved state of a given page.
        Provide position of the current state of a page, the first save state
        and the last state for a given page. 
        Allow easy undo or redo for a given page  
    """
    def __init__(self):
        self._current=0
       
    
    def __iter__(self):
        return self
    
    
    def first(self):
        self._current =0
        return self._current
    
    def next(self, max ):
        if self._current < max:
            self._current += 1
        return self._current
    
    def previous(self):
        if self._current > 0:
            self._current = self._current -1
        return self._current
    
    def currentPosition(self):
        return self._current
    
    def setPosition(self, value):
        if value >=0:
            self._current = int(value)
        
        
    
  
class ListOfState(list):     
    def __init__(self, *args, **kw):
        list.__init__(self, *args, **kw)
        self.iterator = StateIterator()
        
    def appendItem(self, x):
        self.append(x)
        self.iterator.setPosition(value= len(self)-1)
        
    def removeItem(self, x):
        self.iterator.previous()
        self.remove(x)
        
    def getPreviousItem(self):
        position = self.iterator.previous()
        
        if position < 0:
            return None
        else:
            return self[position]
        
    def getNextItem(self):
        position = self.iterator.next(max= len(self)-1)
        if position >= len(self):
            return None
        else:
            return self[position]
        
    def getCurrentItem(self):
        postion = self.iterator.currentPosition()
        if postion >= 0 and position < len(self):
            return self[postion]
        else:
            return None
        
    def getCurrentPosition(self):
        return self.iterator.currentPosition()
        

        
        
        
class PageInfo(object):
    """
        this class contains the minimum numbers of data members
        a fitpage or model page need to be initialized.
    """
    data = None
    model =  None
    manager = None
    event_owner= None
    model_list_box = None
    name = None
    ## Internal name for the AUI manager
    window_name = "Page"
    ## Title to appear on top of the window
    window_caption = "Page"
    
    def __init__(self, model=None,data=None, manager=None,
                  event_owner=None,model_list_box=None , name=None):
        """
            Initialize data members
        """
        self.data = data
        self.model= model
        self.manager= manager
        self.event_owner= event_owner
        self.model_list_box = model_list_box
        self.name=None
        self.window_name = "Page"
        self.window_caption = "Page"
    
class FitPanel(wx.aui.AuiNotebook):    

    """
        FitPanel class contains fields allowing to fit  models and  data
        @note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
       
    """
    ## Internal name for the AUI manager
    window_name = "Fit panel"
    ## Title to appear on top of the window
    window_caption = "Fit Panel "
    CENTER_PANE = True
    
    def __init__(self, parent, *args, **kwargs):
        wx.aui.AuiNotebook.__init__(self,parent,-1,
                    style= wx.aui.AUI_NB_WINDOWLIST_BUTTON|wx.aui.AUI_NB_DEFAULT_STYLE|wx.CLIP_CHILDREN  )
    
        self.manager=None
        self.parent=parent
        self.event_owner=None
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePage)
       
        #dictionary of miodel {model class name, model class}
        self.model_list_box={}
        ##dictionary of page info
        self.page_info_dict={}
        ## save the title of the last page tab added
        self.fit_page_name={}
        ## list of existing fit page
        self.list_fitpage_name=[]
    
        #model page info
        self.model_page_number = None
        ## fit page number for model plot
        self.fit_page1D_number = None
        self.fit_page2D_number = None
        self.model_page = None
        self.sim_page = None
        self.default_page = None
        self.check_first_data = False
        ## get the state of a page
        self.Bind(basepage.EVT_PAGE_INFO, self._onGetstate)
        self.Bind(basepage.EVT_PREVIOUS_STATE, self._onUndo)
        self.Bind(basepage.EVT_NEXT_STATE, self._onRedo)
        
        #add default page
        from hint_fitpage import HintFitPage
        self.hint_page = HintFitPage(self) 
        self.AddPage(page=self.hint_page, caption="Hint")
        #Add the first fit page
        self.default_page = self.add_fit_page(data=None)
        
        # increment number for model name
        self.count=0
        #updating the panel
        self.Update()
        self.Center()
        
        
    def onClosePage(self, event):
        """
             close page and remove all references to the closed page
        """
        selected_page = self.GetPage(self.GetSelection())
        #remove hint page
        if selected_page == self.hint_page:
            return
        ## removing sim_page
        if selected_page == self.sim_page :
            self.manager.sim_page=None 
            return
        
        ## closing other pages
        state = selected_page.createMemento()
        page_name = selected_page.window_name
        page_finder = self.manager.get_page_finder() 
        fitproblem = None
        ## removing model page
        if selected_page == self.model_page:
            #fitproblem = selected_page.model.clone()
            self.model_page = None
            self.count =0
            ## page on menu
            #self.manager._add_page_onmenu(page_name, fitproblem)
        else:
            if selected_page in page_finder:
       
                #fitproblem= page_finder[selected_page].clone()
                if self.GetPageIndex(selected_page)==self.fit_page1D_number:
                    self.fit_page1D_number=None
                if self.GetPageIndex(selected_page)==self.fit_page2D_number:
                    self.fit_page2D_number=None
                ## page on menu
                #self.manager._add_page_onmenu(page_name, fitproblem)
                del page_finder[selected_page]
            ##remove the check box link to the model name of this page (selected_page)
            try:
                self.sim_page.draw_page()
            except:
                ## that page is already deleted no need to remove check box on
                ##non existing page
                pass
                
        #Delete the name of the page into the list of open page
        if selected_page.window_name in self.list_fitpage_name:
            self.list_fitpage_name.remove(selected_page.window_name)
            
        
    def set_manager(self, manager):
        """
             set panel manager
             @param manager: instance of plugin fitting
        """
        self.manager = manager

        
    def set_owner(self,owner):
        """ 
            set and owner for fitpanel
            @param owner: the class responsible of plotting
        """
        self.event_owner = owner
    
    def set_model_list(self, dict):
         """ 
             copy a dictionary of model into its own dictionary
             @param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
        
  
    def get_current_page(self):
        """
            @return the current page selected
        """
        return self.GetPage(self.GetSelection() )
    
    def add_sim_page(self):
        """
            Add the simultaneous fit page
        """
        from simfitpage import SimultaneousFitPage
        page_finder= self.manager.get_page_finder()
        self.sim_page = SimultaneousFitPage(self,page_finder=page_finder, id=-1)
        
        self.AddPage(self.sim_page,caption="Simultaneous Fit",select=True)
        self.sim_page.set_manager(self.manager)
        return self.sim_page
        
        
    def add_fit_page( self,data=None, reset=False ):
        """ 
            Add a fitting page on the notebook contained by fitpanel
            @param data: data to fit
            @return panel : page just added for further used. is used by fitting module
        """    
        if data is not None:
            if data.is_data:
                name = data.name 
            else:
                if data.__class__.__name__=="Data2D":
                    name = 'Model 2D Fit'
                else:
                    name = 'Model 1D Fit'
            myinfo = PageInfo( data=data, name=name )
            myinfo.model_list_box = self.model_list_box.get_list()
            myinfo.event_owner = self.event_owner 
            myinfo.manager = self.manager
            myinfo.window_name = name
            myinfo.window_caption = name
        
        else :
            name = "Fit Page" 
            myinfo = PageInfo( data=data, name=name )
        
        if not name in self.list_fitpage_name:
            # the first data loading
            if not self.check_first_data and self.default_page is not None:
                page_number = self.GetPageIndex(self.default_page)
                self.SetPageText(page_number , name)
                self.default_page.set_data(data)
                self.default_page.set_page_info(page_info=myinfo)
                self.default_page.initialize_combox()
                if  data is not None:
                    self.check_first_data = True
                panel = self.default_page
            else:
                #if not name in self.fit_page_name :
                from fitpage import FitPage
                panel = FitPage(parent=self, page_info=myinfo)
                
                self.AddPage(page=panel, caption=name, select=True)
                if name == 'Model 1D Fit':
                    self.fit_page1D_number= self.GetPageIndex(panel)
                if name =='Model 2D Fit':
                    self.fit_page2D_number= self.GetPageIndex(panel)
                    
                self.list_fitpage_name.append(name)
                if data is not None:
                    if reset:
                        if name in self.fit_page_name.keys():
                            memento= self.fit_page_name[name][0]
                            panel.reset_page(memento)
                        else:
                            self.fit_page_name[name]=ListOfState()
                    
                    #self.fit_page_name[name].appendItem(panel.createMemento())
            #GetPage(self, page_idx) 
            return panel 
        elif name =='Model 1D Fit':
            if self.fit_page1D_number!=None:
                panel =self.GetPage(self.fit_page1D_number) 
                #self.fit_page_name[name]=[]
                self.fit_page_name[name]= ListOfState()
                #self.fit_page_name[name].insert(0,panel.createMemento())
                #self.fit_page_name[name].append(panel.createMemento())
                return panel
            return None
        elif name =='Model 2D Fit':
            if self.fit_page2D_number!=None:
                panel =self.GetPage(self.fit_page2D_number) 
                self.fit_page_name[name]=ListOfState()
                #self.fit_page_name[name].append(panel.createMemento())
                return panel
            return None
        return None
        
   
    def add_model_page(self,model,page_title="Model", qmin=0.0001, qmax=0.13,
                        npts=50, topmenu=False, reset=False):
        """
            Add a model page only one  to display any model selected from the menu or the page combo box.
            when this page is closed than the user will be able to open a new one
            
            @param model: the model for which paramters will be changed
            @param page_title: the name of the page
            @param page_info: contains info about the state of the page
            @param qmin: mimimum Q
            @param qmax: maximum Q
            @param npts: number of Q points
        """
        if topmenu==True:
            ##first time to open model page
            if self.count==0 :
                #if not page_title in self.list_fitpage_name :
                self._help_add_model_page(model=model, page_title=page_title,
                                qmin=qmin, qmax=qmax, npts=npts, reset=reset)
                self.count +=1
            else:
                self.model_page.select_model(model)
                self.fit_page_name[page_title]=ListOfState()
                #self.fit_page_name[page_title].insert(0,self.model_page.createMemento())
      
      
      
    def _close_fitpage(self,data):
        """
            close a fit page when its data is completely remove from the graph
        """
        name = data.name
        for index in range(self.GetPageCount()):
            if self.GetPageText(index)== name:
                selected_page = self.GetPage(index) 
    
                if index ==self.fit_page1D_number:
                    self.fit_page1D_number=None
                if index ==self.fit_page2D_number:
                    self.fit_page2D_number=None
                if selected_page in self.manager.page_finder:
                    del self.manager.page_finder[selected_page]
                ##remove the check box link to the model name of this page (selected_page)
                try:
                    self.sim_page.draw_page()
                except:
                    ## that page is already deleted no need to remove check box on
                    ##non existing page
                    pass
                
                #Delete the name of the page into the list of open page
                if selected_page.window_name in self.list_fitpage_name:
                    self.list_fitpage_name.remove(selected_page.window_name)
                self.DeletePage(index)
                break
        
        
    def  _onGetstate(self, event):
        """
            copy the state of a page
        """
        page= event.page
        if page.window_name in self.fit_page_name:
            self.fit_page_name[page.window_name].appendItem(page.createMemento()) 
            
    def _onUndo(self, event ):
        """
            return the previous state of a given page is available
        """
        page = event.page 
        if page.window_name in self.fit_page_name:
            if self.fit_page_name[page.window_name].getCurrentPosition()==0:
                state = None
            else:
                state = self.fit_page_name[page.window_name].getPreviousItem()
                page._redo.Enable(True)
            page.reset_page(state)
        
    def _onRedo(self, event ): 
        """
            return the next state available
        """       
        page = event.page 
        if page.window_name in self.fit_page_name:
            length= len(self.fit_page_name[page.window_name])
            if self.fit_page_name[page.window_name].getCurrentPosition()== length -1:
                state = None
                page._redo.Enable(False)
                page._redo.Enable(True)
            else:
                state = self.fit_page_name[page.window_name].getNextItem()
            page.reset_page(state)  
                
    def _help_add_model_page(self,model,page_title="Model", qmin=0.0001, 
                             qmax=0.13, npts=50,reset= False):
        """
            #TODO: fill in description
            
            @param qmin: mimimum Q
            @param qmax: maximum Q
            @param npts: number of Q points
        """
        ## creating object that contaning info about model 
        myinfo = PageInfo(model= model ,name= page_title)
        myinfo.model_list_box = self.model_list_box.get_list()
        myinfo.event_owner = self.event_owner 
        myinfo.manager = self.manager
        myinfo.window_name = page_title
        myinfo.window_caption = page_title
      
        from modelpage import ModelPage
        panel = ModelPage(self,myinfo)
        
        self.AddPage(page=panel, caption=page_title, select=True)

        self.model_page_number=self.GetSelection()
        self.model_page=self.GetPage(self.GetSelection())
     
        ##resetting page
        if reset:
            if page_title in self.fit_page_name.keys():

                memento= self.fit_page_name[page_title][0]
                panel.reset_page(memento)
        else:
            self.fit_page_name[page_title]=ListOfState()
            #self.fit_page_name[page_title]=[]
            #self.fit_page_name[page_title].insert(0,panel.createMemento())
       
  
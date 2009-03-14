import wx
import wx.aui
import wx.lib
import numpy
import string ,re
#import models
_BOX_WIDTH = 80

(FitPageEvent, EVT_FIT_PAGE)   = wx.lib.newevent.NewEvent()
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
        wx.aui.AuiNotebook.__init__(self,parent,-1, style=wx.aui.AUI_NB_DEFAULT_STYLE  )
        
        
        self.manager=None
        self.parent=parent
        self.event_owner=None
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePage)
        #Creating the default page --welcomed page
        self.about_page=None
        from welcome_panel import PanelAbout
        self.about_page = PanelAbout(self, -1)
        self.AddPage(self.about_page,"welcome!")
      
       
        #dictionary of miodel {model class name, model class}
        self.model_list_box={}
        # save the title of the last page tab added
        self.fit_page_name=[]
        self.draw_model_name=None
        #model page info
        self.model_page_number=None
       
        self.model_page=None
        self.sim_page=None
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
        page_number = self.GetSelection()
        if self.sim_page != selected_page and selected_page!=self.about_page:
            # remove the check box link to the model name of this page (selected_page)
            if self.sim_page !=None :
                self.sim_page.remove_model(selected_page)
            #remove that page from page_finder of fitting module
            page_finder=self.manager.get_page_finder() 
            for page, value in page_finder.iteritems():
                if page==selected_page:
                    del page_finder[page]
                    break
            #Delete the page from notebook
            if selected_page.name in self.fit_page_name:
                self.fit_page_name.remove(selected_page.name)
                
            if selected_page.name== self.draw_model_name:
                self.draw_model_name=None
                self.model_page=None
            if  page_number == 1:
                self.model_page=None
                self.draw_model_name=None
            
        elif selected_page==self.about_page:
            self.about_page=None
        else:
            self.manager.sim_page=None  
        
        
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
        
    def add_sim_page(self):
        """
            Add the simultaneous fit page
        """
        from simfitpage import SimultaneousFitPage
        self.sim_page = SimultaneousFitPage(self, id=-1)
        self.AddPage(self.sim_page,caption="Simultaneous Fit",select=True)
        self.sim_page.set_manager(self.manager)
        return self.sim_page
        
    def add_fit_page( self,data ):
        """ 
            Add a fitting page on the notebook contained by fitpanel
            @param data: data to fit
            @return panel : page just added for futher used. is used by fitting module
        """     
        try:
            name = data.name 
        except:
            name = 'Fit'
        
        if not name in self.fit_page_name :
            from fitpage1D import FitPage1D
            panel = FitPage1D(parent=self,data=data, id=-1)
            panel.name=name
            
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            
            self.AddPage(page=panel,caption=name,select=True)
            panel.populate_box( self.model_list_box)
            self.fit_page_name.append(name)
    
            return panel 
        else:
            return None 
        
    def _help_add_model_page(self,model,description,page_title, qmin=0, qmax=0.1, npts=50):
        """
            #TODO: fill in description
            
            @param qmin: mimimum Q
            @param qmax: maximum Q
            @param npts: number of Q points
        """
        from modelpage import ModelPage
        
        panel = ModelPage(self,model,page_title, -1)
        panel.set_manager(self.manager)
        panel.set_owner(self.event_owner)
        self.AddPage(page=panel,caption="Model",select=True)
        panel.populate_box( self.model_list_box)
        panel.name = page_title
        self.draw_model_name=page_title
        self.model_page_number=self.GetSelection()
        self.model_page=self.GetPage(self.GetSelection())
        
        
        # Set the range used to plot models
        self.model_page.set_range(qmin, qmax, npts)
        
        # We just created a model page, we are ready to plot the model
        #self.manager.draw_model(model, model.name)
        #FOR PLUGIN  for somereason model.name is = BASEcomponent
        self.manager.draw_model(model, page_title)
        
        
    def add_model_page(self,model,description,page_title, qmin=0, qmax=0.1, npts=50, topmenu=False):
        """
            Add a model page only one  to display any model selected from the menu or the page combo box.
            when this page is closed than the user will be able to open a new one
            
            @param model: the model for which paramters will be changed
            @param page_title: the name of the page
            @param description: [Coder: fill your description!]
            @param page_title: [Coder: fill your description!]
            @param qmin: mimimum Q
            @param qmax: maximum Q
            @param npts: number of Q points
        """
        if topmenu==True:
            if  self.draw_model_name ==None:
                self._help_add_model_page(model,description,page_title, qmin=qmin, qmax=qmax, npts=npts)
            else:
                self.model_page.select_model(model, page_title)
          
    def get_current_page(self):
        """
            @return the current page selected
        """
        return self.GetPage(self.GetSelection() )
  
   
    def set_model_list(self,dict):
         """ 
             copy a dictionary of model into its own dictionary
             @param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
  
import wx
import wx.aui
import wx.lib
import numpy
import string ,re
#import models
_BOX_WIDTH = 80

(FitPageEvent, EVT_FIT_PAGE)   = wx.lib.newevent.NewEvent()
class FitPanel(wx.aui.AuiNotebook):    
#class FitPanel(wx.aui.AuiNotebook,wx.panel):
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
        
        wx.aui.AuiNotebook.__init__(self,parent,-1, style=wx.aui.AUI_NB_SCROLL_BUTTONS )
        #wx.aui.AuiNotebook.__init__(self,parent,-1, style=wx.aui.AUI_NB_DEFAULT_STYLE  )
        
        
        self.manager=None
        self.parent=parent
        self.event_owner=None
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePage)
        #Creating the default page --welcomed page
        from sans.guiframe.welcome_panel import PanelAbout
        self.about_page = PanelAbout(self, -1)
        self.AddPage(self.about_page,"welcome!")
        #self.about_page.Disable()
        #Creating a page for simultaneous fitting
        from simfitpage import SimultaneousFitPage
        self.sim_page = SimultaneousFitPage(self, id=-1)
        self.AddPage(self.sim_page,"Simultaneous Fit")
        
        self._mgr = self.GetAuiManager()

        
        #dictionary of miodel {model class name, model class}
        self.model_list_box={}
        # save the title of the last page tab added
        self.fit_page_name=None
        self.draw_model_name=None
        #model page info
        self.model_page_number=None
       
        self.model_page=None
        # increment number for model name
        self.count=0
        #updating the panel
        self.Update()
        self.Center()
        
        
    def onClosePage(self, event):
        self.ToggleWindowStyle(wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
        #print "went here",self.get_current_page(), self.GetPage(0)
        #event.Skip()
        if self.GetPageCount() <= 2:
            #print "wente here"
            
            # Prevent last tab from being closed
            self.ToggleWindowStyle(~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
            

   


        
    def set_manager(self, manager):
        """
             set panel manager
             @param manager: instance of plugin fitting
        """
        self.manager = manager
        self.sim_page.set_manager(manager)
        
    def set_owner(self,owner):
        """ 
            set and owner for fitpanel
            @param owner: the class responsible of plotting
        """
        self.event_owner=owner
      
        
    def add_fit_page( self,data ):
        """ 
            Add a fitting page on the notebook contained by fitpanel
            @param panel: contains in the page to add
            @param name: title of the page tab
            @return panel : page just added for futher used. is used by fitting module
        """     
        try:
            name = data.name # item in Data1D
        except:
            name = 'Fit'
       
        if self.fit_page_name != name and self.draw_model_name !=name:
            #self.about_page.Disable()
            from fitpage1D import FitPage1D
            panel = FitPage1D(self,data, -1)
            panel.name=name
            #m_name= "M"+str(self.count)  
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            
            self.AddPage(page=panel,caption=name,select=True)
            panel.populate_box( self.model_list_box)
            self.fit_page_name = name
            EVT_FIT_PAGE
            return panel #,m_name
        else:
            return None #, None
        
    def _help_add_model_page(self,model,description,page_title, qmin=0, qmax=0.1, npts=50):
        """
            #TODO: fill in description
            
            @param qmin: mimimum Q
            @param qmax: maximum Q
            @param npts: number of Q points
        """
        from modelpage import ModelPage
        #print "fitpanel model", model
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
        print "self.draw_model_name none",self.draw_model_name
        if topmenu==True:
            if  self.draw_model_name ==None:
                print "self.draw_model_name none"
                self._help_add_model_page(model,description,page_title, qmin=qmin, qmax=qmax, npts=npts)
            else:
                #self.model_page.name=page_title
                #self.draw_model_name=page_title
                #print "wnent here self.draw_model_name ",self.draw_model_name,self.model_page.name,self.model_page
                
                self.model_page.select_model(model, page_title)
          
    def get_current_page(self):
        """
            @return the current page selected
        """
        #return self.nb.GetCurrentPage()
        return self.GetPage(self.GetSelection() )
  
    
    def onClose(self, page=None,page_number=None):
        """
             close the current page except the simpage. remove each check box link to the model
             selected on that page. remove its reference into page_finder (fitting module)
        """
        print "model page", page_number, page, self.draw_model_name
        if page!=None and page_number!=None:
            i=self.DeletePage(page_number)
            #self.nb.RemovePage(page_number)
            #page.Destroy()
            self.model_page_number=None
            self.model_page=None
            self.draw_model_name=None
            print"self.draw_model_name",self.draw_model_name
            return 
        try:
            sim_page = self.GetPage(1)
            selected_page = self.GetPage(self.GetSelection())
            print "sim_page ",sim_page ,selected_page
            if sim_page != selected_page:
                print "sim_page ",sim_page ,selected_page
                # remove the check box link to the model name of this page (selected_page)
                sim_page.remove_model(selected_page)
                #remove that page from page_finder of fitting module
                page_finder=self.manager.get_page_finder() 
                for page, value in page_finder.iteritems():
                    if page==selected_page:
                        del page_finder[page]
                        break
                #Delete the page from notebook
                page_number = self.GetSelection()
                print "on close",selected_page.name,self.GetPageText(page_number),self.draw_model_name
                if selected_page.name== self.draw_model_name:
                    print "went here"
                    self.draw_model_name=None
                    self.model_page=None
                if  page_number == 1:
                    self.model_page=None
                    self.draw_model_name=None
                #selected_page.Destroy()
                #self.RemovePage(page_number)
                i=self.DeletePage(page_number)
                #self.count =self.count -1 
                self.fit_page_name=None
        except:
            raise
        #print "fitpanel", self.draw_model_name 
        
    def set_model_list(self,dict):
         """ 
             copy a dictionary of model into its own dictionary
             @param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
  
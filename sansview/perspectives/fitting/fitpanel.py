import wx
import wx.lib
import numpy
import string ,re
#import models
_BOX_WIDTH = 80


    
class FitPanel(wx.Panel):
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
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.manager=None
        self.parent=parent
        self.event_owner=None
        #self.menu_mng = models.ModelManager()
        self.nb = wx.Notebook(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.nb, 0, wx.EXPAND)
        #Creating an initial page for simultaneous fitting
        from simfitpage import SimultaneousFitPage
        self.sim_page = SimultaneousFitPage(self.nb, -1)
        
        #self.fit_panel.add_page(self.sim_page,"Simultaneous Fit")
        self.nb.AddPage(self.sim_page,"Simultaneous Fit")
        
        #dictionary of miodel {model class name, model class}
        self.model_list_box={}
        # save the title of the last page tab added
        self.fit_page_name=None
        self.draw_model_name=None
        self.page_name="Model View"
        self.nb.Update()
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.Center()
        
        
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
            name = data.group_id # item in Data1D
        except:
            name = 'Fit'
        if self.fit_page_name != name:
            if data.__class__.__name__=='MetaData2D':
                 from fitpage2D import FitPage2D
                 panel = FitPage2D(self.nb,data, -1)
            else:
                from fitpage1D import FitPage1D
                panel = FitPage1D(self.nb,data, -1)
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            
            self.nb.AddPage(page=panel,text=name,select=True)
            panel.populate_box( self.model_list_box)
            self.fit_page_name = name
            return panel
        
        
    def add_model_page(self,model,description,page_title):
        """
            Add a model page only one  to display any model selected from the menu or the page combo box.
            when this page is closed than the user will be able to open a new one
            @param model: the model for which paramters will be changed
            @param page_title: the name of the page
        """
        if  page_title !=self.draw_model_name or self.draw_model_name ==None: 
            from modelpage import ModelPage
            panel = ModelPage(self.nb,model,description, -1)
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            self.nb.AddPage(page=panel,text=page_title,select=True)
            panel.populate_box( self.model_list_box)
            self.draw_model_name=page_title
        else:
            for i in range(self.nb.GetPageCount()):
                if self.nb.GetPageText(i)==self.page_name:
                    page=self.nb.GetPage(i)
                    page.set_page(model,description)
                    break
                
           
    def get_notebook(self):
        """
            @return self.nb: return its own notebook mostly used by fitting module 
        """
        return self.nb
    
    def get_page(self, n):
        """
            @return page at position n
            @param n: page number
        """
        return self.nb.GetPage(n)
    
    
    def get_page_count(self):
        """ @return  number total of pages contained in notebook"""
        return self.nb.GetPageCount()
        
        
    def get_current_page(self):
        """
            @return the current page selected
        """
        return self.nb.GetCurrentPage()
    
    
    def get_selected_page(self):
        """ @return the page just selected by the user """
        return self.nb.GetPage(self.nb.GetSelection())
    
    def onClose(self):
        """
             close the current page except the simpage. remove each check box link to the model
             selected on that page. remove its reference into page_finder (fitting module)
        """
       
        sim_page = self.nb.GetPage(0)
        selected_page = self.nb.GetPage(self.nb.GetSelection())
        
        if sim_page != selected_page:
            # remove the check box link to the model name of this page (selected_page)
            sim_page.remove_model(selected_page)
            #remove that page from page_finder of fitting module
            page_finder=self.manager.get_page_finder() 
            for page, value in page_finder.iteritems():
                if page==selected_page:
                    del page_finder[page]
                    break
            #Delete the page from notebook
            page_number = self.nb.GetSelection()
            if self.nb.GetPageText(page_number)== self.page_name:
                self.draw_model_name=None
                
            selected_page.Destroy()
            self.nb.RemovePage(page_number)
            #self.name=None
            self.fit_page_name=None
            
    def set_model_list(self,dict):
         """ 
             copy a dictionary of model into its own dictionary
             @param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
  
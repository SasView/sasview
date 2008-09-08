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
        
        id = wx.NewId()
        self.btClose =wx.Button(self,id,'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self.onClose,id=id)
        self.btClose.SetToolTipString("Close page.")
    
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.btClose, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        self.sizer.Add(sizer_button,1, wx.EXPAND)
        #dictionary of miodel {model class name, model class}
        self.model_list_box={}
        # save the title of the last page tab added
        self.fit_page_name=None
        self.draw_model_name=[]
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
      
        
    def add_fit_page( self,page_title ):
        """ 
            Add a fitting page on the notebook contained by fitpanel
            @param panel: contains in the page to add
            @param name: title of the page tab
            @return panel : page just added for futher used. is used by fitting module
        """     
        if self.fit_page_name != page_title:
            from fitpage import FitPage
            panel = FitPage(self.nb, -1)
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            self.nb.AddPage(page=panel,text=page_title,select=True)
            panel.populate_box( self.model_list_box)
            self.fit_page_name = page_title
            return panel
    def add_model_page(self,model,page_title):
        if not  page_title in self.draw_model_name: 
            from modelpage import ModelPage
            panel = ModelPage(self.nb,model, -1)
            panel.set_manager(self.manager)
            panel.set_owner(self.event_owner)
            self.nb.AddPage(page=panel,text=page_title,select=True)
            panel.populate_box( self.model_list_box)
            self.draw_model_name.append(page_title)
           
  
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
    
    def onClose(self,event):
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
            #delete the page from notebook
            selected_page.Destroy()
            self.nb.RemovePage(self.nb.GetSelection())
            self.name=None
            
            
    def set_model_list(self,dict):
         """ 
             copy a dictionary of model into its own dictionary
             @param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
  
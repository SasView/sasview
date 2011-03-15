
import numpy
import string 
import wx
import wx.lib.flatnotebook as fnb

from sans.guiframe.panel_base import PanelBase
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import StatusEvent
import basepage
import models
_BOX_WIDTH = 80


class FitPanel(fnb.FlatNotebook, PanelBase):    

    """
    FitPanel class contains fields allowing to fit  models and  data
    
    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
       
    """
    ## Internal name for the AUI manager
    window_name = "Fit panel"
    ## Title to appear on top of the window
    window_caption = "Fit Panel "
    CENTER_PANE = True
    
    def __init__(self, parent, manager=None, *args, **kwargs):
        """
        """
        fnb.FlatNotebook.__init__(self, parent, -1,
                    style= wx.aui.AUI_NB_WINDOWLIST_BUTTON|
                    wx.aui.AUI_NB_DEFAULT_STYLE|
                    wx.CLIP_CHILDREN)
        PanelBase.__init__(self, parent)
        self.SetWindowStyleFlag(style=fnb.FNB_FANCY_TABS)
        self._manager = manager
        self.parent = parent
        self.event_owner = None
        #dictionary of miodel {model class name, model class}
        self.menu_mng = models.ModelManager()
        self.model_list_box = self.menu_mng.get_model_list()
        #pageClosedEvent = fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING 
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING , self.on_close_page)
         ## save the title of the last page tab added
        self.fit_page_name = {}
        ## list of existing fit page
        self.opened_pages = {}
        #page of simultaneous fit 
        self.sim_page = None
        ## get the state of a page
        self.Bind(basepage.EVT_PAGE_INFO, self._onGetstate)
        self.Bind(basepage.EVT_PREVIOUS_STATE, self._onUndo)
        self.Bind(basepage.EVT_NEXT_STATE, self._onRedo)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changing)
       
        #add default pages
        self.add_default_pages()
    
    def update_model_list(self):
        """
        """
        self.model_list_box = self.menu_mng.update()
        return self.model_list_box
        
        
    def get_page_by_id(self, id):  
        """
        """
        if id not in self.opened_pages:
            msg = "Fitpanel cannot find ID: %s in self.opened_pages" % str(id)
            raise ValueError, msg
        else:
            return self.opened_pages[id]
        
    def on_page_changing(self, event):
        """
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=selected_page))
            
    def on_set_focus(self, event):
        """
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=selected_page))
        
    def get_data(self):
        """
        get the data in the current page
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            return selected_page.get_data()
    
    def set_model_state(state):
        """
        receive a state to reset the model in the current page
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            selected_page.set_model_state(state)
            
    def get_state(self):
        """
         return the state of the current selected page
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            return selected_page.get_state()
    
    def add_default_pages(self):
        """
        Add default pages such as a hint page and an empty fit page
        """
        #add default page
        from hint_fitpage import HintFitPage
        self.hint_page = HintFitPage(self) 
        self.AddPage(self.hint_page,"Hint")
        self.hint_page.set_manager(self._manager)
  
    def close_all(self):
        """
        remove all pages, used when a svs file is opened
        """
        
        #get number of pages
        nop = self.GetPageCount()
        #use while-loop, for-loop will not do the job well.
        while (nop>0):
            #delete the first page until no page exists
            page = self.GetPage(0)
            if self._manager.parent.panel_on_focus == page:
                self._manager.parent.panel_on_focus = None
            self._close_helper(selected_page=page)
            self.DeletePage(0)
            nop = nop - 1
            
        ## save the title of the last page tab added
        self.fit_page_name = {}
        ## list of existing fit page
        self.opened_pages = {}  
         
    def set_state(self, state):
        """
        Restore state of the panel
        """
        page_is_opened = False
        if state is not None:
            for id, panel in self.opened_pages.values():
                #Don't return any panel is the exact same page is created
                if id == panel.id:
                    # the page is still opened
                    panel.reset_page(state=state)
                    panel.save_current_state() 
                    page_is_opened = True
            if not page_is_opened:
                panel = self._manager.add_fit_page(data=state.data)
                # add data associated to the page created
                if panel is not None:  
                    self._manager.store_page(page=panel.id, data=state.data)
                    panel.reset_page(state=state)
                    panel.save_current_state()
                    
    def clear_panel(self):
        """
        Clear and close all panels, used by guimanager
        """
       
        #close all panels only when svs file opened
        self.close_all()
        self._manager.mypanels = []
        
                       
    def on_close_page(self, event=None):
        """
        close page and remove all references to the closed page
        """
        nbr_page = self.GetPageCount()
        if nbr_page == 1:
           
            event.Veto()
            return 
        selected_page = self.GetPage(self.GetSelection())
        self._close_helper(selected_page=selected_page)
        
    def close_page_with_data(self, deleted_data):
        """
        close a fit page when its data is completely remove from the graph
        """
        if deleted_data is None:
            return
        for index in range(self.GetPageCount()):
            selected_page = self.GetPage(index) 
            if hasattr(selected_page,"get_data"):
                data = selected_page.get_data()
                
                if data is None:
                    #the fitpanel exists and only the initial fit page is open 
                    #with no selected data
                    return
                if data.name == deleted_data.name:
                    self._close_helper(selected_page)
                    self.DeletePage(index)
                    break
        
    def set_manager(self, manager):
        """
        set panel manager
        
        :param manager: instance of plugin fitting
        
        """
        self._manager = manager
        for pos in range(self.GetPageCount()):
            page = self.GetPage(pos)
            if page is not None:
                page.set_manager(self._manager)

    def set_model_list(self, dict):
         """ 
         copy a dictionary of model into its own dictionary
         
         :param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
        
    def get_current_page(self):
        """
        :return: the current page selected
        
        """
        return self.GetPage(self.GetSelection())
    
    def add_sim_page(self):
        """
        Add the simultaneous fit page
        """
        from simfitpage import SimultaneousFitPage
        page_finder= self._manager.get_page_finder()
        self.sim_page = SimultaneousFitPage(self,page_finder=page_finder, id=-1)
        self.sim_page.id = wx.NewId()
        self.AddPage(self.sim_page,"Simultaneous Fit", True)
        self.sim_page.set_manager(self._manager)
        return self.sim_page
        
 
    def add_empty_page(self):
        """
        add an empty page
        """
        from fitpage import FitPage
        panel = FitPage(parent=self)
        panel.id = wx.NewId()
        panel.populate_box(dict=self.model_list_box)
        panel.set_manager(self._manager)
        caption = str(panel.window_name) + " " + str(self._manager.index_model)
        self.AddPage(panel, caption, select=True)
        self.opened_pages[panel.id] = panel
        return panel 
    
    def delete_data(self, data):
        """
        Delete the given data
        """
        if data is None:
            return None
    def set_data(self, data):
        """ 
        Add a fitting page on the notebook contained by fitpanel
        
        :param data: data to fit
        
        :return panel : page just added for further used. is used by fitting module
        
        """
        if data is None:
            return None
        for page in self.opened_pages.values():
            #check if the selected data existing in the fitpanel
            pos = self.GetPageIndex(page)
            if page.get_data() is None:
                enable2D = page.get_view_mode()
                if (data.__class__.__name__ == "Data2D" and enable2D)\
                or (data.__class__.__name__ == "Data1D" and not enable2D):
                    page.set_data(data)
                    self.SetPageText(pos, str(data.name))
                    self.SetSelection(pos)
                    return page
                
            elif page.get_data().id == data.id:
                msg = "Data already existing in the fitting panel"
                wx.PostEvent(self._manager.parent, 
                             StatusEvent(status=msg, info='warning'))  
                self.SetSelection(pos)
                return page
        
        page = self.add_empty_page()
        pos = self.GetPageIndex(page)
        page.id = wx.NewId()
        page.set_data(data)
        self.SetPageText(pos, str(data.name))
        self.opened_pages[page.id] = page
        
        return page
       
    def _onGetstate(self, event):
        """
        copy the state of a page
        """
        page = event.page
        if page.id in self.fit_page_name:
           self.fit_page_name[page.id].appendItem(page.createMemento()) 
            
    def _onUndo(self, event ):
        """
        return the previous state of a given page is available
        """
        page = event.page 
        if page.id in self.fit_page_name:
            if self.fit_page_name[page.id].getCurrentPosition()==0:
                state = None
            else:
                state = self.fit_page_name[page.id].getPreviousItem()
                page._redo.Enable(True)
            page.reset_page(state)
        
    def _onRedo(self, event): 
        """
        return the next state available
        """       
        page = event.page 
        if page.id in self.fit_page_name:
            length= len(self.fit_page_name[page.id])
            if self.fit_page_name[page.id].getCurrentPosition()== length -1:
                state = None
                page._redo.Enable(False)
                page._redo.Enable(True)
            else:
                state =self.fit_page_name[page.id].getNextItem()
            page.reset_page(state)  
                 
    def _close_helper(self, selected_page):
        """
        Delete the given page from the notebook
        """
        #remove hint page
        if selected_page == self.hint_page:
            return
        ## removing sim_page
        if selected_page == self.sim_page :
            self._manager.sim_page=None 
            return
        
        ## closing other pages
        state = selected_page.createMemento()
        page_name = selected_page.window_name
        page_finder = self._manager.get_page_finder() 
        fitproblem = None
        ## removing fit page
        data = selected_page.get_data()
        #Don' t remove plot for 2D
        flag = True
        if data.__class__.__name__ == 'Data2D':
            flag = False
        if selected_page in page_finder:
            #Delete the name of the page into the list of open page
            for id, list in self.opened_pages.iteritems():
                #Don't return any panel is the exact same page is created
                
                if flag and selected_page.id == id:
                    self._manager.remove_plot(id, theory=False)
                    break 
            del page_finder[selected_page]
        ##remove the check box link to the model name of this page (selected_page)
        try:
            self.sim_page.draw_page()
        except:
            ## that page is already deleted no need to remove check box on
            ##non existing page
            pass
                
        #Delete the name of the page into the list of open page
        for id, list in self.opened_pages.iteritems():
            #Don't return any panel is the exact same page is created
            
            if selected_page.id == id:
                del self.opened_pages[selected_page.id]
                break 
     
  
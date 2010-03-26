
import numpy
import string 
import wx
import wx.aui
import wx.lib
from wx.aui import AuiNotebook 


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
    #type of page can be real data , theory 1D or therory2D
    type = "Data"
    def __init__(self, model=None, data=None, manager=None,
                  event_owner=None, model_list_box=None, name=None):
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
        self.type = "Data"
        
class FitPanel(AuiNotebook):    

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
        AuiNotebook.__init__(self,parent,-1,
                    style= wx.aui.AUI_NB_WINDOWLIST_BUTTON|
                    wx.aui.AUI_NB_DEFAULT_STYLE|
                    wx.CLIP_CHILDREN)
    
        self.manager=None
        self.parent=parent
        self.event_owner=None
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_page)
       
        #dictionary of miodel {model class name, model class}
        self.model_list_box = {}
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
        
        #add default page
        from hint_fitpage import HintFitPage
        self.hint_page = HintFitPage(self) 
        self.AddPage(page=self.hint_page, caption="Hint")
        #Add the first fit page
        self.add_empty_page()
        
        # increment number for model name
        self.count=0
        #updating the panel
        self.Update()
        self.Center()
  
    def on_close_page(self, event):
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
        for index in range(self.GetPageCount()):
            selected_page = self.GetPage(index) 
            if hasattr(selected_page,"get_data"):
                data = selected_page.get_data()
                if data.name == deleted_data.name:
                    self._close_helper(selected_page)
                    self.DeletePage(index)
                    break
        
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
        
    def get_page_info(self, data=None):
        """
            fill information required to add a page in the fit panel
        """
        name = "Fit Page"
        type = 'empty'
        if data is not None:
            if data.is_data:
                name = data.name 
                type = 'Data'
            else:
                if data.__class__.__name__ == "Data2D":
                    name = 'Model 2D Fit'
                    type = 'Theory2D'
                else:
                    name = 'Model 1D Fit'
                    type = 'Theory1D'
        page_info = PageInfo(data=data, name=name)
        page_info.event_owner = self.event_owner 
        page_info.manager = self.manager
        page_info.window_name = name
        page_info.window_caption = name
        page_info.type = type
        return page_info
   
    def add_empty_page(self):
        """
            add an empty page
        """
        page_info = self.get_page_info()
        from fitpage import FitPage
        panel = FitPage(parent=self, page_info=page_info)
        self.AddPage(page=panel, caption=page_info.window_name, select=True)
        self.opened_pages[page_info.type] = [page_info.window_name, panel]
        return panel 
    
    def add_page(self, page_info):
        """
            add a new page
        """
        from fitpage import FitPage
        panel = FitPage(parent=self, page_info=page_info)
        self.AddPage(page=panel, caption=page_info.window_name, select=True)
        index = self.GetPageIndex(panel)
        self.change_page_content(data=page_info.data, index=index)
        return panel
    
    def change_page_content(self, data, index):
        """
            replace the contains of an existing page
        """
        page_info = self.get_page_info(data=data)
        self.SetPageText(index, page_info.window_name)
        panel = self.GetPage(index)
        panel.set_data(data)
        if panel.model_list_box is None or len(panel.model_list_box) == 0: 
            page_info.model_list_box = self.model_list_box.get_list()
            panel.populate_box(dict=page_info.model_list_box)
            panel.initialize_combox()
        panel.set_page_info(page_info=page_info)
        self.opened_pages[page_info.type] = [page_info.window_name, panel]
        return panel
    
    def replace_page(self, index, page_info, type):
        """
            replace an existing page
        """
        self.DeletePage(index)
        del self.opened_pages[type]
        return self.add_page(page_info=page_info)
        
    def add_fit_page(self, data, reset=False):
        """ 
            Add a fitting page on the notebook contained by fitpanel
            @param data: data to fit
            @return panel : page just added for further used. is used by fitting module
        """
        if data is None:
            return None
        page_info = self.get_page_info(data=data)
        type = page_info.type
        npages = len(self.opened_pages.keys())
        #check if only and empty page is opened
        if len(self.opened_pages.keys()) > 0:
            first_page_type = self.opened_pages.keys()[0]
            if npages == 1 and first_page_type in ['empty']:
                #replace the first empty page
                name, panel = self.opened_pages[first_page_type]
                index = self.GetPageIndex(panel)
                panel = self.change_page_content(data=data, index=index)
                del self.opened_pages[first_page_type]
                return panel
        if type in self.opened_pages.keys():
            #this type of page is already created but it is a theory
            # meaning the same page is just to fit different data
            if not type.lower() in ['data']:
                #delete the previous theory page and add a new one
                name, panel = self.opened_pages[type]
                self.manager.reset_plot_panel(panel.get_data())
                #delete the existing page and replace it
                index = self.GetPageIndex(panel)
                panel = self.replace_page(index=index, page_info=page_info, type=type)
                return panel 
            else:
                for name, panel in self.opened_pages.values():
                    #Don't return any panel is the exact same page is created
                    if name == page_info.window_name:
                        return None
                    else:
                        panel = self.add_page(page_info=page_info)
                        return panel        
        else:
            #a new type of page is created
            panel = self.add_page(page_info=page_info)
            return panel
    
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
        
    def _onRedo(self, event): 
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
                 
    def _close_helper(self, selected_page):
        """
            Delete the given page from the notebook
        """
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
        ## removing fit page
        if selected_page in page_finder:
            #Delete the name of the page into the list of open page
            for type, list in self.opened_pages.iteritems():
                #Don't return any panel is the exact same page is created
                name = str(list[0])
                if selected_page.window_name == name:
                    if type.lower() in ['theory1d', 'theory2d']:
                        self.manager.remove_plot(selected_page, theory=True)
                    else:
                        self.manager.remove_plot(selected_page, theory=False)
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
        for type, list in self.opened_pages.iteritems():
            #Don't return any panel is the exact same page is created
            name = str(list[0])
            if selected_page.window_name == name:
                del self.opened_pages[type]
                break 
     
  
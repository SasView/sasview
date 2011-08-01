
import numpy
import string 
import wx
import sys
#from wx.lib.flatnotebook import FlatNotebook as nb
from wx.aui import AuiNotebook as nb

from sans.guiframe.panel_base import PanelBase
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import StatusEvent

import basepage
import models
_BOX_WIDTH = 80


class FitPanel(nb, PanelBase):    

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
        nb.__init__(self, parent, -1,
                    style= wx.aui.AUI_NB_WINDOWLIST_BUTTON|
                    wx.aui.AUI_NB_DEFAULT_STYLE|
                    wx.CLIP_CHILDREN)
        PanelBase.__init__(self, parent)
        #self.SetWindowStyleFlag(style=nb.FNB_FANCY_TABS)
        self._manager = manager
        self.parent = parent
        self.event_owner = None
        #dictionary of miodel {model class name, model class}
        self.menu_mng = models.ModelManager()
        self.model_list_box = self.menu_mng.get_model_list()
        #pageClosedEvent = nb.EVT_FLATNOTEBOOK_PAGE_CLOSING 
        self.pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        
        self.Bind(self.pageClosedEvent, self.on_close_page)
         ## save the title of the last page tab added
        self.fit_page_name = {}
        ## list of existing fit page
        self.opened_pages = {}
        #index of fit page
        self.fit_page_index = 0
        #index of batch page
        self.batch_page_index = 0
        #page of simultaneous fit 
        self.sim_page = None
        self.fit_engine_type = "scipy"
        ## get the state of a page
        self.Bind(basepage.EVT_PAGE_INFO, self._onGetstate)
        self.Bind(basepage.EVT_PREVIOUS_STATE, self._onUndo)
        self.Bind(basepage.EVT_NEXT_STATE, self._onRedo)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changing)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.on_closed)

    def on_closed(self, event):
        """
        """
        if self.GetPageCount() == 0:
            self.add_empty_page()
            self.enable_close_button()
        
    def save_project(self, doc=None):
        """
        return an xml node containing state of the panel
         that guiframe can write to file
        """
        for uid, page in self.opened_pages.iteritems():
            data = page.get_data()
            # state must be cloned
            state = page.get_state().clone()
            if data is not None:
                new_doc = self._manager.state_reader.write_toXML(data, state)
                if doc != None and hasattr(doc, "firstChild"):
                    child = new_doc.firstChild.firstChild
                    doc.firstChild.appendChild(child)  
                else:
                    doc = new_doc 
        return doc    
    
    def _on_engine_change(self, name='scipy'):
        """
        """
        for panel in self.opened_pages.values():
            self.set_engine_helper(panel=panel, name=name)
            
    def set_engine_helper(self, panel, name='scipy'):
        """
        """
        self.fit_engine_type = name
        if panel != self.sim_page:
            panel._on_engine_change(name=self.fit_engine_type)
                
    def update_model_list(self):
        """
        """
        temp = self.menu_mng.update()
        if len(temp):
            self.model_list_box = temp
        return temp
        
        
    def get_page_by_id(self, uid):  
        """
        """
        if uid not in self.opened_pages:
            msg = "Fitpanel cannot find ID: %s in self.opened_pages" % str(uid)
            raise ValueError, msg
        else:
            return self.opened_pages[uid]
        
    def on_page_changing(self, event):
        """
        calls the function when the current event handler has exited. avoiding
        to call panel on focus on a panel that is currently deleted
        """
        wx.CallAfter(self.helper_on_page_change)
        
        
    def helper_on_page_change(self):
        """
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=selected_page))
        self.enable_close_button()
       
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
            for uid, panel in self.opened_pages.iteritems():
                #Don't return any panel is the exact same page is created
                if uid == panel.uid and panel.data == state.data:
                    # the page is still opened
                    panel.reset_page(state=state)
                    panel.save_current_state() 
                    page_is_opened = True
            if not page_is_opened:
                panel = self._manager.add_fit_page(data=state.data)
                # add data associated to the page created
                if panel is not None:  
                    self._manager.store_data(uid=panel.uid, 
                                             data=state.data,
                                             caption=panel.window_caption)
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
        selected_page = self.GetPage(self.GetSelection())
        if nbr_page == 1:
            if selected_page.get_data() == None:
                if event is not None:
                    event.Veto()
                return 
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
                if data.id == deleted_data.id:
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
        self.sim_page.uid = wx.NewId()
        self.AddPage(self.sim_page,"Simultaneous Fit", True)
        self.sim_page.set_manager(self._manager)
        self.enable_close_button()
        return self.sim_page
        
 
    def add_empty_page(self):
        """
        add an empty page
        """
        """
        if self.batch_on:
            from batchfitpage import BatchFitPage
            panel = BatchFitPage(parent=self)
            #Increment index of batch page
            self.batch_page_index += 1
            index = self.batch_page_index
        else:
        """
        from fitpage import FitPage
        panel = FitPage(parent=self)
        #Increment index of fit page
        self.fit_page_index += 1
        index = self.fit_page_index
        panel.uid = wx.NewId()
        panel.populate_box(dict=self.model_list_box)
        panel.set_manager(self._manager)
        caption = str(panel.window_caption) + " " + str(index)
        self.AddPage(panel, caption, select=True)
        self.opened_pages[panel.uid] = panel
        self.set_engine_helper(panel=panel)
        self.enable_close_button()
        return panel 
    
    def enable_close_button(self):
        """
        display the close button on tab for more than 1 tabs else remove the 
        close button
        """
        if self.GetPageCount() <= 1:
            style = self.GetWindowStyleFlag() 
            flag = wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            if style & wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB == flag:
                style = style & ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
                self.SetWindowStyle(style)
        else:
            style = self.GetWindowStyleFlag()
            flag = wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            if style & wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB != flag:
                style |= wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
                self.SetWindowStyle(style)
            
    def delete_data(self, data):
        """
        Delete the given data
        """
        if data.__class__.__name__ != "list":
            raise ValueError, "Fitpanel delete_data expect list of id"
        else:
            n = self.GetPageCount()
            for page in self.opened_pages.values():
                pos = self.GetPageIndex(page)
                temp_data = page.get_data()
                #stop the fitting before deleting the page
                page.is_fitting()
                if temp_data is not None and temp_data.id in data:
                    self.SetSelection(pos)
                    self.on_close_page(event=None)
                    temp = self.GetSelection()
                    self.DeletePage(temp)
            if self.GetPageCount()== 0:
                self._manager.on_add_new_page(event=None)
        
    def set_data_on_batch_mode(self, data_list):
        """
        Add all data to a single tab when the application is on Batch mode.
        However all data in the set of data must be either 1D or 2D type. 
        This method presents option to select the data type before creating a 
        tab. 
        """
        data_1d_list = []
        data_2d_list = []
        for data in data_list:
            if data.__class__.__name__ == "Data1D":
                data_1d_list.append(data)
            if data.__class__.__name__ == "Data2D":
                data_2d_list.append(data)
        page = None
        for p in self.opened_pages.values():
            #check if the selected data existing in the fitpanel
            pos = self.GetPageIndex(page)
            if p.get_data() is None:
                page = p
                break
               
        if data_1d_list and data_2d_list:
            # need to warning the user that this batch is a special case
            from .fitting_widgets import BatchDataDialog
            dlg = BatchDataDialog(self)
            if dlg.ShowModal() == wx.ID_OK:
                data_type = dlg.get_data()
                dlg.Destroy()
                if page  is None:
                    page = self.add_empty_page()
                if data_type == 1:
                    #user has selected only data1D
                    page.fill_data_combobox(data_1d_list)
                elif data_type == 2:
                    page.fill_data_combobox(data_2d_list)
            else:
                #the batch analysis is canceled
                 dlg.Destroy()
                 return None
        else:
            if page is None:
                page = self.add_empty_page()
            if data_1d_list and not data_2d_list:
                #only on type of data 
                page.fill_data_combobox(data_1d_list)
            elif not data_1d_list and data_2d_list:
                page.fill_data_combobox(data_2d_list)
            
        self.opened_pages[page.uid] = page
        return page
    
    def set_data(self, data_list):
        """ 
        Add a fitting page on the notebook contained by fitpanel
        
        :param data: data to fit
        
        :return panel : page just added for further used. 
        is used by fitting module
        
        """
        if not data_list:
            return None
        if self.batch_on:
           return self.set_data_on_batch_mode(data_list)
        else:
            data = None
            data = data_list[0]
            if data is None:
                return None
        for page in self.opened_pages.values():
            #check if the selected data existing in the fitpanel
            pos = self.GetPageIndex(page)
            if page.get_data() is None:
                #make sure data get placed in 1D empty tab if data is 1D
                #else data get place on 2D tab empty tab
                enable2D = page.get_view_mode()
                if (data.__class__.__name__ == "Data2D" and enable2D)\
                or (data.__class__.__name__ == "Data1D" and not enable2D):
                    #page.set_data(data)
                    page.fill_data_combobox(data_list)
                    self.SetPageText(pos, str(data.name))
                    self.SetSelection(pos)
                    return page
                # Todo: Need to set different window name when has same data
                # Todo: to catch page with same data even if it is not on the top.
                """
                elif page.get_data().id == data.id:
                    msg = "Data already existing in the fitting panel"
                    wx.PostEvent(self._manager.parent, 
                                 StatusEvent(status=msg, info='warning')) 
                    self.SetSelection(pos)
                    return page
                """
        page = self.add_empty_page()
        pos = self.GetPageIndex(page)
        page.fill_data_combobox(data_list)
        #page.set_data(data)
        self.SetPageText(pos, str(data.name))
        self.opened_pages[page.uid] = page
        
        return page
       
    def _onGetstate(self, event):
        """
        copy the state of a page
        """
        page = event.page
        if page.uid in self.fit_page_name:
           self.fit_page_name[page.uid].appendItem(page.createMemento()) 
            
    def _onUndo(self, event):
        """
        return the previous state of a given page is available
        """
        page = event.page 
        if page.uid in self.fit_page_name:
            if self.fit_page_name[page.uid].getCurrentPosition()==0:
                state = None
            else:
                state = self.fit_page_name[page.uid].getPreviousItem()
                page._redo.Enable(True)
            page.reset_page(state)
        
    def _onRedo(self, event): 
        """
        return the next state available
        """       
        page = event.page 
        if page.uid in self.fit_page_name:
            length= len(self.fit_page_name[page.uid])
            if self.fit_page_name[page.uid].getCurrentPosition()== length -1:
                state = None
                page._redo.Enable(False)
                page._redo.Enable(True)
            else:
                state =self.fit_page_name[page.uid].getNextItem()
            page.reset_page(state)  
                 
    def _close_helper(self, selected_page):
        """
        Delete the given page from the notebook
        """
        #remove hint page
        #if selected_page == self.hint_page:
        #    return
        ## removing sim_page
        if selected_page == self.sim_page :
            self._manager.sim_page=None 
            return
        if selected_page.__class__.__name__ == "FitPage":
            self.fit_page_index -= 1
        else:
            self.batch_page_index -= 1
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
            for uid, list in self.opened_pages.iteritems():
                #Don't return any panel is the exact same page is created
                
                if flag and selected_page.uid == uid:
                    self._manager.remove_plot(uid, theory=False)
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
        for uid, list in self.opened_pages.iteritems():
            #Don't return any panel is the exact same page is created
            if selected_page.uid == uid:
                del self.opened_pages[selected_page.uid]
                break 
      
  
"""
    Fitting perspective
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import re
import sys
import os
import wx
import logging
import numpy
import time
from copy import deepcopy
import models

from sas.dataloader.loader import Loader
from sas.guiframe.dataFitting import Data2D
from sas.guiframe.dataFitting import Data1D
from sas.guiframe.dataFitting import check_data_validity
from sas.guiframe.events import NewPlotEvent
from sas.guiframe.events import StatusEvent
from sas.guiframe.events import EVT_SLICER_PANEL
from sas.guiframe.events import EVT_SLICER_PARS_UPDATE
from sas.guiframe.gui_style import GUIFRAME_ID
from sas.guiframe.plugin_base import PluginBase
from sas.guiframe.data_processor import BatchCell
from sas.fit.BumpsFitting import BumpsFit as Fit
from sas.perspectives.fitting.console import ConsoleUpdate
from sas.perspectives.fitting.fitproblem import FitProblemDictionary
from sas.perspectives.fitting.fitpanel import FitPanel
from sas.perspectives.fitting.resultpanel import ResultPanel, PlotResultEvent

from sas.perspectives.fitting.fit_thread import FitThread
from sas.perspectives.fitting.pagestate import Reader
from sas.perspectives.fitting.fitpage import Chi2UpdateEvent
from sas.perspectives.calculator.model_editor import TextDialog
from sas.perspectives.calculator.model_editor import EditorWindow
from sas.guiframe.gui_manager import MDIFrame
from sas.guiframe.documentation_window import DocumentationWindow

MAX_NBR_DATA = 4

(PageInfoEvent, EVT_PAGE_INFO) = wx.lib.newevent.NewEvent()


if sys.platform == "win32":
    ON_MAC = False
else:
    ON_MAC = True



class Plugin(PluginBase):
    """
    Fitting plugin is used to perform fit
    """
    def __init__(self):
        PluginBase.__init__(self, name="Fitting")

        #list of panel to send to guiframe
        self.mypanels = []
        # reference to the current running thread
        self.calc_2D = None
        self.calc_1D = None

        self.color_dict = {}

        self.fit_thread_list = {}
        self.residuals = None
        self.weight = None
        self.fit_panel = None
        self.plot_panel = None
        # Start with a good default
        self.elapsed = 0.022
        self.fit_panel = None
        ## dictionary of page closed and id
        self.closed_page_dict = {}
        ## Relative error desired in the sum of squares (float)
        self.batch_reset_flag = True
        #List of selected data
        self.selected_data_list = []
        ## list of slicer panel created to display slicer parameters and results
        self.slicer_panels = []
        # model 2D view
        self.model2D_id = None
        #keep reference of the simultaneous fit page
        self.sim_page = None
        self.sim_menu = None
        self.batch_page = None
        self.batch_menu = None
        self.index_model = 0
        self.test_model_color = None
        #Create a reader for fit page's state
        self.state_reader = None
        self._extensions = '.fitv'
        self.menu1 = None
        self.new_model_frame = None

        self.temp_state = []
        self.state_index = 0
        self.sfile_ext = None
        # take care of saving  data, model and page associated with each other
        self.page_finder = {}
        # Log startup
        logging.info("Fitting plug-in started")
        self.batch_capable = self.get_batch_capable()

    def get_batch_capable(self):
        """
        Check if the plugin has a batch capability
        """
        return True

    def create_fit_problem(self, page_id):
        """
        Given an ID create a fitproblem container
        """
        self.page_finder[page_id] = FitProblemDictionary()

    def delete_fit_problem(self, page_id):
        """
        Given an ID create a fitproblem container
        """
        if page_id in self.page_finder.iterkeys():
            del self.page_finder[page_id]

    def add_color(self, color, id):
        """
        adds a color as a key with a plot id as its value to a dictionary
        """
        self.color_dict[id] = color

    def on_batch_selection(self, flag):
        """
        switch the the notebook of batch mode or not
        """
        self.batch_on = flag
        if self.fit_panel is not None:
            self.fit_panel.batch_on = self.batch_on

    def populate_menu(self, owner):
        """
        Create a menu for the Fitting plug-in

        :param id: id to create a menu
        :param owner: owner of menu

        :return: list of information to populate the main menu

        """
        #Menu for fitting
        self.menu1 = wx.Menu()
        id1 = wx.NewId()
        simul_help = "Add new fit panel"
        self.menu1.Append(id1, '&New Fit Page', simul_help)
        wx.EVT_MENU(owner, id1, self.on_add_new_page)
        self.menu1.AppendSeparator()
        self.id_simfit = wx.NewId()
        simul_help = "Constrained or Simultaneous Fit"
        self.menu1.Append(self.id_simfit, '&Constrained or Simultaneous Fit', simul_help)
        wx.EVT_MENU(owner, self.id_simfit, self.on_add_sim_page)
        self.sim_menu = self.menu1.FindItemById(self.id_simfit)
        self.sim_menu.Enable(False)
        #combined Batch
        self.id_batchfit = wx.NewId()
        batch_help = "Combined Batch"
        self.menu1.Append(self.id_batchfit, '&Combine Batch Fit', batch_help)
        wx.EVT_MENU(owner, self.id_batchfit, self.on_add_sim_page)
        self.batch_menu = self.menu1.FindItemById(self.id_batchfit)
        self.batch_menu.Enable(False)

        self.menu1.AppendSeparator()
        self.id_bumps_options = wx.NewId()
        bopts_help = "Fitting options"
        self.menu1.Append(self.id_bumps_options, 'Fit &Options', bopts_help)
        wx.EVT_MENU(owner, self.id_bumps_options, self.on_bumps_options)
        self.bumps_options_menu = self.menu1.FindItemById(self.id_bumps_options)
        self.bumps_options_menu.Enable(True)

        self.id_result_panel = wx.NewId()
        self.menu1.Append(self.id_result_panel, "Fit Results", "Show fit results panel")
        wx.EVT_MENU(owner, self.id_result_panel, self.on_fit_results)
        self.menu1.AppendSeparator()

        self.id_reset_flag = wx.NewId()
        resetf_help = "BatchFit: If checked, the initial param values will be "
        resetf_help += "propagated from the previous results. "
        resetf_help += "Otherwise, the same initial param values will be used "
        resetf_help += "for all fittings."
        self.menu1.AppendCheckItem(self.id_reset_flag,
                                   "Chain Fitting [BatchFit Only]",
                                   resetf_help)
        wx.EVT_MENU(owner, self.id_reset_flag, self.on_reset_batch_flag)
        chain_menu = self.menu1.FindItemById(self.id_reset_flag)
        chain_menu.Check(not self.batch_reset_flag)
        chain_menu.Enable(self.batch_on)

        self.menu1.AppendSeparator()
        self.edit_model_menu = wx.Menu()
        # Find and put files name in menu
        try:
            self.set_edit_menu(owner=owner)
        except:
            raise

        self.id_edit = wx.NewId()
        editmodel_help = "Edit customized model sample file"
        self.menu1.AppendMenu(self.id_edit, "Edit Custom Model",
                              self.edit_model_menu, editmodel_help)
        #create  menubar items
        return [(self.menu1, self.sub_menu)]

    def edit_custom_model(self, event):
        """
        Get the python editor panel
        """
        event_id = event.GetId()
        label = self.edit_menu.GetLabel(event_id)
        from sas.perspectives.calculator.pyconsole import PyConsole
        filename = os.path.join(models.find_plugins_dir(), label)
        frame = PyConsole(parent=self.parent, manager=self,
                          panel=self.fit_panel,
                          title='Advanced Custom Model Editor',
                          filename=filename)
        self.put_icon(frame)
        frame.Show(True)

    def delete_custom_model(self, event):
        """
        Delete custom model file
        """
        event_id = event.GetId()
        label = self.delete_menu.GetLabel(event_id)
        toks = os.path.splitext(label)
        path = os.path.join(models.find_plugins_dir(), toks[0])
        try:
            for ext in ['.py', '.pyc']:
                p_path = path + ext
                os.remove(p_path)
            self.update_custom_combo()
            if os.path.isfile(p_path):
                msg = "Sorry! Could not be able to delete the default "
                msg += "custom model... \n"
                msg += "Please manually remove the files (.py, .pyc) "
                msg += "in the 'plugin_models' folder \n"
                msg += "inside of the SasView application, "
                msg += "and try it again."
                wx.MessageBox(msg, 'Info')
                #wx.PostEvent(self.parent, StatusEvent(status=msg, type='stop',
                #                                      info='warning'))
            else:
                self.delete_menu.Delete(event_id)
                for item in self.edit_menu.GetMenuItems():
                    if item.GetLabel() == label:
                        self.edit_menu.DeleteItem(item)
                        msg = "The custom model, %s, has been deleted." % label
                        wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                type='stop', info='info'))
                        break
        except:
            msg = 'Delete Error: \nCould not delete the file; Check if in use.'
            wx.MessageBox(msg, 'Error')

    def make_sum_model(self, event):
        """
        Edit summodel template and make one
        """
        event_id = event.GetId()
        model_manager = models.ModelManager()
        model_list = model_manager.get_model_name_list()
        plug_dir = models.find_plugins_dir()
        textdial = TextDialog(None, self, wx.ID_ANY, 'Easy Sum/Multi(p1, p2) Editor',
                              model_list, plug_dir)
        self.put_icon(textdial)
        textdial.ShowModal()
        textdial.Destroy()

    def make_new_model(self, event):
        """
        Make new model
        """
        if self.new_model_frame != None:
            self.new_model_frame.Show(False)
            self.new_model_frame.Show(True)
        else:
            event_id = event.GetId()
            dir_path = models.find_plugins_dir()
            title = "New Custom Model Function"
            self.new_model_frame = EditorWindow(parent=self, base=self,
                                                path=dir_path, title=title)
            self.put_icon(self.new_model_frame)
        self.new_model_frame.Show(True)

    def update_custom_combo(self):
        """
        Update custom model list in the fitpage combo box
        """
        custom_model = 'Customized Models'
        try:
            # Update edit menus
            self.set_edit_menu_helper(self.parent, self.edit_custom_model)
            self.set_edit_menu_helper(self.parent, self.delete_custom_model)
            temp = self.fit_panel.reset_pmodel_list()
            if temp:
                # Set the new custom model list for all fit pages
                for uid, page in self.fit_panel.opened_pages.iteritems():
                    if hasattr(page, "formfactorbox"):
                        page.model_list_box = temp
                        current_val = page.formfactorbox.GetLabel()
                        #if page.plugin_rbutton.GetValue():
                        mod_cat = page.categorybox.GetStringSelection()
                        if mod_cat == custom_model:
                            #pos = page.formfactorbox.GetSelection()
                            page._show_combox_helper()
                            new_val = page.formfactorbox.GetLabel()
                            if current_val != new_val and new_val != '':
                                page.formfactorbox.SetLabel(new_val)
                            else:
                                page.formfactorbox.SetLabel(current_val)
        except:
            pass


    def set_edit_menu(self, owner):
        """
        Set list of the edit model menu labels
        """
        wx_id = wx.NewId()
        #new_model_menu = wx.Menu()
        self.edit_model_menu.Append(wx_id, 'New',
                                   'Add a new model function')
        wx.EVT_MENU(owner, wx_id, self.make_new_model)
        wx_id = wx.NewId()
        self.edit_model_menu.Append(wx_id, 'Sum|Multi(p1, p2)',
                                    'Sum of two model functions')
        wx.EVT_MENU(owner, wx_id, self.make_sum_model)
        e_id = wx.NewId()
        self.edit_menu = wx.Menu()
        self.edit_model_menu.AppendMenu(e_id,
                                    'Advanced', self.edit_menu)
        self.set_edit_menu_helper(owner, self.edit_custom_model)

        d_id = wx.NewId()
        self.delete_menu = wx.Menu()
        self.edit_model_menu.AppendMenu(d_id,
                                        'Delete', self.delete_menu)
        self.set_edit_menu_helper(owner, self.delete_custom_model)

    def set_edit_menu_helper(self, owner=None, menu=None):
        """
        help for setting list of the edit model menu labels
        """
        if menu == None:
            menu = self.edit_custom_model
        list_fnames = os.listdir(models.find_plugins_dir())
        list_fnames.sort()
        for f_item in list_fnames:
            name = os.path.basename(f_item)
            toks = os.path.splitext(name)
            if toks[-1] == '.py' and not toks[0] == '__init__':
                if menu == self.edit_custom_model:
                    if toks[0] == 'easy_sum_of_p1_p2':
                        continue
                    submenu = self.edit_menu
                else:
                    submenu = self.delete_menu
                has_file = False
                for item in submenu.GetMenuItems():
                    if name == submenu.GetLabel(item.GetId()):
                        has_file = True
                if not has_file:
                    wx_id = wx.NewId()
                    submenu.Append(wx_id, name)
                    wx.EVT_MENU(owner, wx_id, menu)
                    has_file = False

    def put_icon(self, frame):
        """
        Put icon in the frame title bar
        """
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass

    def on_add_sim_page(self, event):
        """
        Create a page to access simultaneous fit option
        """
        event_id = event.GetId()
        caption = "Const & Simul Fit"
        page = self.sim_page
        if event_id == self.id_batchfit:
            caption = "Combined Batch"
            page = self.batch_page

        def set_focus_page(page):
            page.Show(True)
            page.Refresh()
            page.SetFocus()
            #self.parent._mgr.Update()
            msg = "%s already opened\n" % str(page.window_caption)
            wx.PostEvent(self.parent, StatusEvent(status=msg))

        if page != None:
            return set_focus_page(page)
        if caption == "Const & Simul Fit":
            self.sim_page = self.fit_panel.add_sim_page(caption=caption)
        else:
            self.batch_page = self.fit_panel.add_sim_page(caption=caption)

    def get_context_menu(self, plotpanel=None):
        """
        Get the context menu items available for P(r).them allow fitting option
        for Data2D and Data1D only.

        :param graph: the Graph object to which we attach the context menu

        :return: a list of menu items with call-back function

        :note: if Data1D was generated from Theory1D
                the fitting option is not allowed

        """
        self.plot_panel = plotpanel
        graph = plotpanel.graph
        fit_option = "Select data for fitting"
        fit_hint = "Dialog with fitting parameters "

        if graph.selected_plottable not in plotpanel.plots:
            return []
        item = plotpanel.plots[graph.selected_plottable]
        if item.__class__.__name__ is "Data2D":
            if hasattr(item, "is_data"):
                if item.is_data:
                    return [[fit_option, fit_hint, self._onSelect]]
                else:
                    return []
            return [[fit_option, fit_hint, self._onSelect]]
        else:

            # if is_data is true , this in an actual data loaded
            #else it is a data created from a theory model
            if hasattr(item, "is_data"):
                if item.is_data:
                    return [[fit_option, fit_hint, self._onSelect]]
                else:
                    return []
            return [[fit_option, fit_hint, self._onSelect]]
        return []

    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        self.parent = parent
        #self.parent.Bind(EVT_FITSTATE_UPDATE, self.on_set_state_helper)
        # Creation of the fit panel
        self.frame = MDIFrame(self.parent, None, 'None', (100, 200))
        self.fit_panel = FitPanel(parent=self.frame, manager=self)
        self.frame.set_panel(self.fit_panel)
        self._frame_set_helper()
        self.on_add_new_page(event=None)
        #Set the manager for the main panel
        self.fit_panel.set_manager(self)
        # List of windows used for the perspective
        self.perspective = []
        self.perspective.append(self.fit_panel.window_name)

        self.result_frame = MDIFrame(self.parent, None, ResultPanel.window_caption, (220, 200))
        self.result_panel = ResultPanel(parent=self.result_frame, manager=self)
        self.perspective.append(self.result_panel.window_name)

        #index number to create random model name
        self.index_model = 0
        self.index_theory = 0
        self.parent.Bind(EVT_SLICER_PANEL, self._on_slicer_event)
        self.parent.Bind(EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PANEL)
        #self.parent._mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE,self._onclearslicer)
        #Create reader when fitting panel are created
        self.state_reader = Reader(self.set_state)
        #append that reader to list of available reader
        loader = Loader()
        loader.associate_file_reader(".fitv", self.state_reader)
        #Send the fitting panel to guiframe
        self.mypanels.append(self.fit_panel)
        self.mypanels.append(self.result_panel)
        return self.mypanels

    def clear_panel(self):
        """
        """
        self.fit_panel.clear_panel()

    def delete_data(self, data):
        """
        delete  the given data from panel
        """
        self.fit_panel.delete_data(data)

    def set_data(self, data_list=None):
        """
        receive a list of data to fit
        """
        if data_list is None:
            data_list = []
        selected_data_list = []
        if self.batch_on:
            self.add_fit_page(data=data_list)
        else:
            if len(data_list) > MAX_NBR_DATA:
                from fitting_widgets import DataDialog
                dlg = DataDialog(data_list=data_list, nb_data=MAX_NBR_DATA)
                if dlg.ShowModal() == wx.ID_OK:
                    selected_data_list = dlg.get_data()
                dlg.Destroy()

            else:
                selected_data_list = data_list
            try:
                group_id = wx.NewId()
                for data in selected_data_list:
                    if data is not None:
                        # 2D has no same group_id
                        if data.__class__.__name__ == 'Data2D':
                            group_id = wx.NewId()
                        data.group_id = group_id
                        if group_id not in data.list_group_id:
                            data.list_group_id.append(group_id)
                        self.add_fit_page(data=[data])
            except:
                msg = "Fitting set_data: " + str(sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))

    def set_theory(self, theory_list=None):
        """
        """
        #set the model state for a given theory_state:
        for item in theory_list:
            try:
                _, theory_state = item
                self.fit_panel.set_model_state(theory_state)
            except:
                msg = "Fitting: cannot deal with the theory received"
                logging.error("set_theory " + msg + "\n" + str(sys.exc_value))
                wx.PostEvent(self.parent,
                             StatusEvent(status=msg, info="error"))

    def set_state(self, state=None, datainfo=None, format=None):
        """
        Call-back method for the fit page state reader.
        This method is called when a .fitv/.svs file is loaded.

        : param state: PageState object
        : param datainfo: data
        """
        #state = self.state_reader.get_state()
        if state != None:
            state = state.clone()
            # store fitting state in temp_state
            self.temp_state.append(state)
        else:
            self.temp_state = []
        # index to start with for a new set_state
        self.state_index = 0
        # state file format
        self.sfile_ext = format

        self.on_set_state_helper(event=None)

    def  on_set_state_helper(self, event=None):
        """
        Set_state_helper. This actually sets state
        after plotting data from state file.

        : event: FitStateUpdateEvent called
            by dataloader.plot_data from guiframe
        """
        if len(self.temp_state) == 0:
            if self.state_index == 0 and len(self.mypanels) <= 0 \
            and self.sfile_ext == '.svs':
                self.temp_state = []
                self.state_index = 0
            return

        try:
            # Load fitting state
            state = self.temp_state[self.state_index]
            #panel state should have model selection to set_state
            if state.formfactorcombobox != None:
                #set state
                data = self.parent.create_gui_data(state.data)
                data.group_id = state.data.group_id
                self.parent.add_data(data_list={data.id: data})
                wx.PostEvent(self.parent, NewPlotEvent(plot=data,
                                        title=data.title))
                #need to be fix later make sure we are sendind guiframe.data
                #to panel
                state.data = data
                page = self.fit_panel.set_state(state)
            else:
                #just set data because set_state won't work
                data = self.parent.create_gui_data(state.data)
                data.group_id = state.data.group_id
                self.parent.add_data(data_list={data.id: data})
                wx.PostEvent(self.parent, NewPlotEvent(plot=data,
                                        title=data.title))
                page = self.add_fit_page([data])
                caption = page.window_caption
                self.store_data(uid=page.uid, data_list=page.get_data_list(),
                        caption=caption)
                self.mypanels.append(page)

            # get ready for the next set_state
            self.state_index += 1

            #reset state variables to default when all set_state is finished.
            if len(self.temp_state) == self.state_index:

                self.temp_state = []
                #self.state_index = 0
                # Make sure the user sees the fitting panel after loading
                #self.parent.set_perspective(self.perspective)
                self.on_perspective(event=None)
        except:
            self.state_index = 0
            self.temp_state = []
            raise

    def set_param2fit(self, uid, param2fit):
        """
        Set the list of param names to fit for fitprobelm
        """
        self.page_finder[uid].set_param2fit(param2fit)

    def set_graph_id(self, uid, graph_id):
        """
        Set graph_id for fitprobelm
        """
        self.page_finder[uid].set_graph_id(graph_id)

    def get_graph_id(self, uid):
        """
        Set graph_id for fitprobelm
        """
        return self.page_finder[uid].get_graph_id()

    def save_fit_state(self, filepath, fitstate):
        """
        save fit page state into file
        """
        self.state_reader.write(filename=filepath, fitstate=fitstate)

    def set_fit_weight(self, uid, flag, is2d=False, fid=None):
        """
        Set the fit weights of a given page for all
        its data by default. If fid is provide then set the range
        only for the data with fid as id
        :param uid: id corresponding to a fit page
        :param fid: id corresponding to a fit problem (data, model)
        :param weight: current dy data
        """
        # If we are not dealing with a specific fit problem, then
        # there is no point setting the weights.
        if fid is None:
            return
        if uid in self.page_finder.keys():
            self.page_finder[uid].set_weight(flag=flag, is2d=is2d)

    def set_fit_range(self, uid, qmin, qmax, fid=None):
        """
        Set the fitting range of a given page for all
        its data by default. If fid is provide then set the range
        only for the data with fid as id
        :param uid: id corresponding to a fit page
        :param fid: id corresponding to a fit problem (data, model)
        :param qmin: minimum  value of the fit range
        :param qmax: maximum  value of the fit range
        """
        if uid in self.page_finder.keys():
            self.page_finder[uid].set_range(qmin=qmin, qmax=qmax, fid=fid)

    def schedule_for_fit(self, value=0, uid=None):
        """
        Set the fit problem field to 0 or 1 to schedule that problem to fit.
        Schedule the specified fitproblem or get the fit problem related to
        the current page and set value.
        :param value: integer 0 or 1
        :param uid: the id related to a page contaning fitting information
        """
        if uid in self.page_finder.keys():
            self.page_finder[uid].schedule_tofit(value)

    def get_page_finder(self):
        """
        return self.page_finder used also by simfitpage.py
        """
        return self.page_finder

    def set_page_finder(self, modelname, names, values):
        """
        Used by simfitpage.py to reset a parameter given the string constrainst.

        :param modelname: the name ot the model for with the parameter
                            has to reset
        :param value: can be a string in this case.
        :param names: the paramter name
        """
        sim_page_id = self.sim_page.uid
        for uid, value in self.page_finder.iteritems():
            if uid != sim_page_id and uid != self.batch_page.uid:
                model_list = value.get_model()
                model = model_list[0]
                if model.name == modelname:
                    value.set_model_param(names, values)
                    break

    def split_string(self, item):
        """
        receive a word containing dot and split it. used to split parameterset
        name into model name and parameter name example: ::

            paramaterset (item) = M1.A
            Will return model_name = M1 , parameter name = A

        """
        if item.find(".") >= 0:
            param_names = re.split("\.", item)
            model_name = param_names[0]
            ##Assume max len is 3; eg., M0.radius.width
            if len(param_names) == 3:
                param_name = param_names[1] + "." + param_names[2]
            else:
                param_name = param_names[1]
            return model_name, param_name

    def on_bumps_options(self, event=None):
        """
        Open the bumps options panel.
        """
        try:
            from bumps.gui.fit_dialog import show_fit_config
            show_fit_config(self.parent, help=self.on_help)
        except ImportError:
            # CRUFT: Bumps 0.7.5.6 and earlier do not have the help button
            from bumps.gui.fit_dialog import OpenFitOptions
            OpenFitOptions()

    def on_help(self, algorithm_id):
        _TreeLocation = "user/perspectives/fitting/optimizer.html"
        _anchor = "#fit-"+algorithm_id
        DocumentationWindow(self.parent, wx.ID_ANY, _TreeLocation, _anchor, "Optimizer Help")


    def on_fit_results(self, event=None):
        """
        Make the Fit Results panel visible.
        """
        self.result_frame.Show()
        self.result_frame.Raise()

    def stop_fit(self, uid):
        """
        Stop the fit
        """
        if uid in self.fit_thread_list.keys():
            calc_fit = self.fit_thread_list[uid]
            if calc_fit is not  None and calc_fit.isrunning():
                calc_fit.stop()
                msg = "Fit stop!"
                wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
            del self.fit_thread_list[uid]
        #set the fit button label of page when fit stop is trigger from
        #simultaneous fit pane
        sim_flag = self.sim_page is not None and uid == self.sim_page.uid
        batch_flag = self.batch_page is not None and uid == self.batch_page.uid
        if sim_flag or batch_flag:
            for uid, value in self.page_finder.iteritems():
                if value.get_scheduled() == 1:
                    if uid in self.fit_panel.opened_pages.keys():
                        panel = self.fit_panel.opened_pages[uid]
                        panel._on_fit_complete()

    def set_smearer(self, uid, smearer, fid, qmin=None, qmax=None, draw=True,
                    enable_smearer=False):
        """
        Get a smear object and store it to a fit problem of fid as id. If proper
        flag is enable , will plot the theory with smearing information.

        :param smearer: smear object to allow smearing data of id fid
        :param enable_smearer: Define whether or not all (data, model) contained
            in the structure of id uid will be smeared before fitting.
        :param qmin: the maximum value of the theory plotting range
        :param qmax: the maximum value of the theory plotting range
        :param draw: Determine if the theory needs to be plot
        """
        if uid not in self.page_finder.keys():
            return
        self.page_finder[uid].enable_smearing(flag=enable_smearer)
        self.page_finder[uid].set_smearer(smearer, fid=fid)
        if draw:
            ## draw model 1D with smeared data
            data = self.page_finder[uid].get_fit_data(fid=fid)
            if data is None:
                msg = "set_mearer requires at least data.\n"
                msg += "Got data = %s .\n" % str(data)
                return
                #raise ValueError, msg
            model = self.page_finder[uid].get_model(fid=fid)
            if model is None:
                return
            enable1D = issubclass(data.__class__, Data1D)
            enable2D = issubclass(data.__class__, Data2D)
            ## if user has already selected a model to plot
            ## redraw the model with data smeared
            smear = self.page_finder[uid].get_smearer(fid=fid)

            # compute weight for the current data
            weight = self.page_finder[uid].get_weight(fid=fid)

            self.draw_model(model=model, data=data, page_id=uid, smearer=smear,
                enable1D=enable1D, enable2D=enable2D,
                qmin=qmin, qmax=qmax, weight=weight)
            self._mac_sleep(0.2)

    def _mac_sleep(self, sec=0.2):
        """
        Give sleep to MAC
        """
        if ON_MAC:
            time.sleep(sec)

    def draw_model(self, model, page_id, data=None, smearer=None,
                   enable1D=True, enable2D=False,
                   state=None,
                   fid=None,
                   toggle_mode_on=False,
                   qmin=None, qmax=None,
                   update_chisqr=True, weight=None, source='model'):
        """
        Draw model.

        :param model: the model to draw
        :param name: the name of the model to draw
        :param data: the data on which the model is based to be drawn
        :param description: model's description
        :param enable1D: if true enable drawing model 1D
        :param enable2D: if true enable drawing model 2D
        :param qmin:  Range's minimum value to draw model
        :param qmax:  Range's maximum value to draw model
        :param qstep: number of step to divide the x and y-axis
        :param update_chisqr: update chisqr [bool]

        """
        #self.weight = weight
        if issubclass(data.__class__, Data1D) or not enable2D:
            ## draw model 1D with no loaded data
            self._draw_model1D(model=model,
                               data=data,
                               page_id=page_id,
                               enable1D=enable1D,
                               smearer=smearer,
                               qmin=qmin,
                               qmax=qmax,
                               fid=fid,
                               weight=weight,
                               toggle_mode_on=toggle_mode_on,
                               state=state,
                               update_chisqr=update_chisqr,
                               source=source)
        else:
            ## draw model 2D with no initial data
            self._draw_model2D(model=model,
                                page_id=page_id,
                                data=data,
                                enable2D=enable2D,
                                smearer=smearer,
                                qmin=qmin,
                                qmax=qmax,
                                fid=fid,
                                weight=weight,
                                state=state,
                                toggle_mode_on=toggle_mode_on,
                                update_chisqr=update_chisqr,
                                source=source)

    def onFit(self, uid):
        """
        Get series of data, model, associates parameters and range and send then
        to  series of fitters. Fit data and model, display result to
        corresponding panels.
        :param uid: id related to the panel currently calling this fit function.
        """
        if uid is None: raise RuntimeError("no page to fit") # Should never happen

        sim_page_uid = getattr(self.sim_page, 'uid', None)
        batch_page_uid = getattr(self.batch_page, 'uid', None)

        if uid == sim_page_uid:
            fit_type = 'simultaneous'
        elif uid == batch_page_uid:
            fit_type = 'combined_batch'
        else:
            fit_type = 'single'

        fitter_list = []
        sim_fitter = None
        if fit_type == 'simultaneous':
            # for simultaneous fitting only one fitter is needed
            sim_fitter = Fit()
            sim_fitter.fitter_id = self.sim_page.uid
            fitter_list.append(sim_fitter)

        self.current_pg = None
        list_page_id = []
        fit_id = 0
        for page_id, page_info in self.page_finder.iteritems():
            # For simulfit (uid give with None), do for-loop
            # if uid is specified (singlefit), do it only on the page.
            if page_id in (sim_page_uid, batch_page_uid): continue
            if fit_type == "single" and page_id != uid: continue

            try:
                if page_info.get_scheduled() == 1:
                    page_info.nbr_residuals_computed = 0
                    page = self.fit_panel.get_page_by_id(page_id)
                    self.set_fit_weight(uid=page.uid,
                                     flag=page.get_weight_flag(),
                                     is2d=page._is_2D())
                    if not page.param_toFit:
                        msg = "No fitting parameters for %s" % page.window_caption
                        wx.PostEvent(page.parent.parent,
                                     StatusEvent(status=msg, info="error",
                                                 type="stop"))
                        return False
                    if not page._update_paramv_on_fit():
                        msg = "Fitting range or parameter values are"
                        msg += " invalid in %s" % \
                                    page.window_caption
                        wx.PostEvent(page.parent.parent,
                                     StatusEvent(status=msg, info="error",
                                     type="stop"))
                        return False

                    pars = [str(element[1]) for element in page.param_toFit]
                    fitproblem_list = page_info.values()
                    for fitproblem in  fitproblem_list:
                        if sim_fitter is None:
                            fitter = Fit()
                            fitter.fitter_id = page_id
                            fitter_list.append(fitter)
                        else:
                            fitter = sim_fitter
                        self._add_problem_to_fit(fitproblem=fitproblem,
                                             pars=pars,
                                             fitter=fitter,
                                             fit_id=fit_id)
                        fit_id += 1
                    list_page_id.append(page_id)
                    page_info.clear_model_param()
            except KeyboardInterrupt:
                msg = "Fitting terminated"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                                      type="stop"))
                return True
            except:
                raise
                msg = "Fitting error: %s" % str(sys.exc_value)
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error",
                                                      type="stop"))
                return False
        ## If a thread is already started, stop it
        #if self.calc_fit!= None and self.calc_fit.isrunning():
        #    self.calc_fit.stop()
        msg = "Fitting is in progress..."
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="progress"))

        #Handler used to display fit message
        handler = ConsoleUpdate(parent=self.parent,
                                manager=self,
                                improvement_delta=0.1)
        self._mac_sleep(0.2)

        # batch fit
        batch_inputs = {}
        batch_outputs = {}
        if fit_type == "simultaneous":
            page = self.sim_page
        elif fit_type == "combined_batch":
            page = self.batch_page
        else:
            page = self.fit_panel.get_page_by_id(uid)
        if page.batch_on:
            calc_fit = FitThread(handler=handler,
                                 fn=fitter_list,
                                 pars=pars,
                                 batch_inputs=batch_inputs,
                                 batch_outputs=batch_outputs,
                                 page_id=list_page_id,
                                 completefn=self._batch_fit_complete,
                                 reset_flag=self.batch_reset_flag)
        else:
            ## Perform more than 1 fit at the time
            calc_fit = FitThread(handler=handler,
                                    fn=fitter_list,
                                    batch_inputs=batch_inputs,
                                    batch_outputs=batch_outputs,
                                    page_id=list_page_id,
                                    updatefn=handler.update_fit,
                                    completefn=self._fit_completed)
        #self.fit_thread_list[current_page_id] = calc_fit
        self.fit_thread_list[uid] = calc_fit
        calc_fit.queue()
        calc_fit.ready(2.5)
        msg = "Fitting is in progress..."
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="progress"))

        return True

    def remove_plot(self, uid, fid=None, theory=False):
        """
        remove model plot when a fit page is closed
        :param uid: the id related to the fitpage to close
        :param fid: the id of the fitproblem(data, model, range,etc)
        """
        if uid not in self.page_finder.keys():
            return
        fitproblemList = self.page_finder[uid].get_fit_problem(fid)
        for fitproblem in fitproblemList:
            data = fitproblem.get_fit_data()
            model = fitproblem.get_model()
            plot_id = None
            if model is not None:
                plot_id = data.id + model.name
            if theory:
                plot_id = data.id + model.name
            group_id = data.group_id
            wx.PostEvent(self.parent, NewPlotEvent(id=plot_id,
                                                   group_id=group_id,
                                                   action='remove'))

    def store_data(self, uid, data_list=None, caption=None):
        """
        Recieve a list of data and store them ans well as a caption of
        the fit page where they come from.
        :param uid: if related to a fit page
        :param data_list: list of data to fit
        :param caption: caption of the window related to these data
        """
        if data_list is None:
            data_list = []

        self.page_finder[uid].set_fit_data(data=data_list)
        if caption is not None:
            self.page_finder[uid].set_fit_tab_caption(caption=caption)

    def on_add_new_page(self, event=None):
        """
        ask fit panel to create a new empty page
        """
        try:
            page = self.fit_panel.add_empty_page()
            # add data associated to the page created
            if page != None:
                wx.PostEvent(self.parent, StatusEvent(status="Page Created",
                                               info="info"))
            else:
                msg = "Page was already Created"
                wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                       info="warning"))
        except:
            msg = "Creating Fit page: %s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))

    def add_fit_page(self, data):
        """
        given a data, ask to the fitting panel to create a new fitting page,
        get this page and store it into the page_finder of this plug-in
        :param data: is a list of data
        """
        page = self.fit_panel.set_data(data)
        # page could be None when loading state files
        if page == None:
            return page
        #append Data1D to the panel containing its theory
        #if theory already plotted
        if page.uid in self.page_finder:
            data = page.get_data()
            theory_data = self.page_finder[page.uid].get_theory_data(data.id)
            if issubclass(data.__class__, Data2D):
                data.group_id = wx.NewId()
                if theory_data is not None:
                    group_id = str(page.uid) + " Model1D"
                    wx.PostEvent(self.parent,
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data,
                                             new_data=data)
            else:
                if theory_data is not None:
                    group_id = str(page.uid) + " Model2D"
                    data.group_id = theory_data.group_id
                    wx.PostEvent(self.parent,
                             NewPlotEvent(group_id=group_id,
                                               action="delete"))
                    self.parent.update_data(prev_data=theory_data,
                                             new_data=data)
        self.store_data(uid=page.uid, data_list=page.get_data_list(),
                        caption=page.window_caption)
        if self.sim_page is not None and not self.batch_on:
            self.sim_page.draw_page()
        if self.batch_page is not None and self.batch_on:
            self.batch_page.draw_page()

        return page

    def _onEVT_SLICER_PANEL(self, event):
        """
        receive and event telling to update a panel with a name starting with
        event.panel_name. this method update slicer panel
        for a given interactor.

        :param event: contains type of slicer , paramaters for updating
            the panel and panel_name to find the slicer 's panel concerned.
        """
        event.panel_name
        for item in self.parent.panels:
            name = event.panel_name
            if self.parent.panels[item].window_caption.startswith(name):
                self.parent.panels[item].set_slicer(event.type, event.params)

        #self.parent._mgr.Update()

    def _closed_fitpage(self, event):
        """
        request fitpanel to close a given page when its unique data is removed
        from the plot. close fitpage only when the a loaded data is removed
        """
        if event is None or event.data is None:
            return
        if hasattr(event.data, "is_data"):
            if not event.data.is_data or \
                event.data.__class__.__name__ == "Data1D":
                self.fit_panel.close_page_with_data(event.data)

    def _reset_schedule_problem(self, value=0, uid=None):
        """
        unschedule or schedule all fitproblem to be fit
        """
        # case that uid is not specified
        if uid == None:
            for page_id in self.page_finder.keys():
                self.page_finder[page_id].schedule_tofit(value)
        # when uid is given
        else:
            if uid in self.page_finder.keys():
                self.page_finder[uid].schedule_tofit(value)

    def _add_problem_to_fit(self, fitproblem, pars, fitter, fit_id):
        """
        Create and set fitter with series of data and model
        """
        data = fitproblem.get_fit_data()
        model = fitproblem.get_model()
        smearer = fitproblem.get_smearer()
        qmin, qmax = fitproblem.get_range()

        #Extra list of parameters and their constraints
        listOfConstraint = []
        param = fitproblem.get_model_param()
        if len(param) > 0:
            for item in param:
                ## check if constraint
                if item[0] != None and item[1] != None:
                    listOfConstraint.append((item[0], item[1]))
        new_model = model
        fitter.set_model(new_model, fit_id, pars, data=data,
                         constraints=listOfConstraint)
        fitter.set_data(data=data, id=fit_id, smearer=smearer, qmin=qmin,
                        qmax=qmax)
        fitter.select_problem_for_fit(id=fit_id, value=1)

    def _onSelect(self, event):
        """
        when Select data to fit a new page is created .Its reference is
        added to self.page_finder
        """
        panel = self.plot_panel
        if panel == None:
            raise ValueError, "Fitting:_onSelect: NonType panel"
        Plugin.on_perspective(self, event=event)
        self.select_data(panel)

    def select_data(self, panel):
        """
        """
        for plottable in panel.graph.plottables:
            if plottable.__class__.__name__ in ["Data1D", "Theory1D"]:
                data_id = panel.graph.selected_plottable
                if plottable == panel.plots[data_id]:
                    data = plottable
                    self.add_fit_page(data=[data])
                    return
            else:
                data = plottable
                self.add_fit_page(data=[data])

    def update_fit(self, result=None, msg=""):
        """
        """
        print "update_fit result", result

    def _batch_fit_complete(self, result, pars, page_id,
                            batch_outputs, batch_inputs, elapsed=None):
        """
        Display fit result in batch
        :param result: list of objects received from fitters
        :param pars: list of  fitted parameters names
        :param page_id: list of page ids which called fit function
        :param elapsed: time spent at the fitting level
        """
        self._mac_sleep(0.2)
        uid = page_id[0]
        if uid in self.fit_thread_list.keys():
            del self.fit_thread_list[uid]

        wx.CallAfter(self._update_fit_button, page_id)
        t1 = time.time()
        str_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime(t1))
        msg = "Fit completed on %s \n" % str_time
        msg += "Duration time: %s s.\n" % str(elapsed)
        wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                              type="stop"))

        if batch_outputs is None:
            batch_outputs = {}

        # format batch_outputs
        batch_outputs["Chi2"] = []
        #Don't like these loops
        # Need to create dictionary of all fitted parameters
        # since the number of parameters can differ between each fit result
        for list_res in result:
            for res in list_res:
                model, data = res.inputs[0]
                if model is not None and hasattr(model, "model"):
                    model = model.model
                #get all fittable parameters of the current model
                for param in  model.getParamList():
                    if param  not in batch_outputs.keys():
                        batch_outputs[param] = []
                for param in model.getDispParamList():
                    if not model.is_fittable(param) and \
                        param in batch_outputs.keys():
                        del batch_outputs[param]
                # Add fitted parameters and their error
                for param in res.param_list:
                    if param not in batch_outputs.keys():
                        batch_outputs[param] = []
                    err_param = "error on %s" % str(param)
                    if err_param not in batch_inputs.keys():
                        batch_inputs[err_param] = []
        msg = ""
        for list_res in result:
            for res in list_res:
                pid = res.fitter_id
                model, data = res.inputs[0]
                correct_result = False
                if model is not None and hasattr(model, "model"):
                    model = model.model
                if data is not None and hasattr(data, "sas_data"):
                    data = data.sas_data

                is_data2d = issubclass(data.__class__, Data2D)
                #check consistency of arrays
                if not is_data2d:
                    if len(res.theory) == len(res.index[res.index]) and \
                        len(res.index) == len(data.y):
                        correct_result = True
                else:
                    copy_data = deepcopy(data)
                    new_theory = copy_data.data
                    new_theory[res.index] = res.theory
                    new_theory[res.index == False] = numpy.nan
                    correct_result = True
                #get all fittable parameters of the current model
                param_list = model.getParamList()
                for param in model.getDispParamList():
                    if not model.is_fittable(param) and \
                        param in param_list:
                        param_list.remove(param)
                if not correct_result or res.fitness is None or \
                    not numpy.isfinite(res.fitness) or \
                    numpy.any(res.pvec == None) or not \
                    numpy.all(numpy.isfinite(res.pvec)):
                    data_name = str(None)
                    if data is not None:
                        data_name = str(data.name)
                    model_name = str(None)
                    if model is not None:
                        model_name = str(model.name)
                    msg += "Data %s and Model %s did not fit.\n" % (data_name,
                                                                    model_name)
                    ERROR = numpy.NAN
                    cell = BatchCell()
                    cell.label = res.fitness
                    cell.value = res.fitness
                    batch_outputs["Chi2"].append(ERROR)
                    for param in param_list:
                        # save value of  fixed parameters
                        if param not in res.param_list:
                            batch_outputs[str(param)].append(ERROR)
                        else:
                            #save only fitted values
                            batch_outputs[param].append(ERROR)
                            batch_inputs["error on %s" % str(param)].append(ERROR)
                else:
                    # TODO: Why sometimes res.pvec comes with numpy.float64?
                    # probably from scipy lmfit
                    if res.pvec.__class__ == numpy.float64:
                        res.pvec = [res.pvec]

                    cell = BatchCell()
                    cell.label = res.fitness
                    cell.value = res.fitness
                    batch_outputs["Chi2"].append(cell)
                    # add parameters to batch_results
                    for param in param_list:
                        # save value of  fixed parameters
                        if param not in res.param_list:
                            batch_outputs[str(param)].append(model.getParam(param))
                        else:
                            index = res.param_list.index(param)
                            #save only fitted values
                            batch_outputs[param].append(res.pvec[index])
                            if res.stderr is not None and \
                                len(res.stderr) == len(res.param_list):
                                item = res.stderr[index]
                                batch_inputs["error on %s" % param].append(item)
                            else:
                                batch_inputs["error on %s" % param].append('-')
                            model.setParam(param, res.pvec[index])
                #fill the batch result with emtpy value if not in the current
                #model
                EMPTY = "-"
                for key in batch_outputs.keys():
                    if key not in param_list and key not in ["Chi2", "Data"]:
                        batch_outputs[key].append(EMPTY)

                self.page_finder[pid].set_batch_result(batch_inputs=batch_inputs,
                                                       batch_outputs=batch_outputs)

                cpage = self.fit_panel.get_page_by_id(pid)
                cpage._on_fit_complete()
                self.page_finder[pid][data.id].set_result(res)
                fitproblem = self.page_finder[pid][data.id]
                qmin, qmax = fitproblem.get_range()
                plot_result = False
                if correct_result:
                    if not is_data2d:
                        self._complete1D(x=data.x[res.index], y=res.theory, page_id=pid,
                                         elapsed=None,
                                         index=res.index, model=model,
                                         weight=None, fid=data.id,
                                         toggle_mode_on=False, state=None,
                                         data=data, update_chisqr=False,
                                         source='fit', plot_result=plot_result)
                    else:
                        self._complete2D(image=new_theory, data=data,
                                         model=model,
                                         page_id=pid, elapsed=None,
                                         index=res.index,
                                         qmin=qmin,
                                         qmax=qmax, fid=data.id, weight=None,
                                         toggle_mode_on=False, state=None,
                                         update_chisqr=False,
                                         source='fit', plot_result=plot_result)
                self.on_set_batch_result(page_id=pid,
                                         fid=data.id,
                                         batch_outputs=batch_outputs,
                                         batch_inputs=batch_inputs)

        wx.PostEvent(self.parent, StatusEvent(status=msg, error="info",
                                              type="stop"))
        # Remove parameters that are not shown
        cpage = self.fit_panel.get_page_by_id(uid)
        tbatch_outputs = {}
        shownkeystr = cpage.get_copy_params()
        for key in batch_outputs.keys():
            if key in ["Chi2", "Data"] or shownkeystr.count(key) > 0:
                tbatch_outputs[key] = batch_outputs[key]

        wx.CallAfter(self.parent.on_set_batch_result, tbatch_outputs,
                     batch_inputs, self.sub_menu)

    def on_set_batch_result(self, page_id, fid, batch_outputs, batch_inputs):
        """
        """
        pid = page_id
        if fid not in self.page_finder[pid]:
            return
        fitproblem = self.page_finder[pid][fid]
        index = self.page_finder[pid].nbr_residuals_computed - 1
        residuals = fitproblem.get_residuals()
        theory_data = fitproblem.get_theory_data()
        data = fitproblem.get_fit_data()
        model = fitproblem.get_model()
        #fill batch result information
        if "Data" not in batch_outputs.keys():
            batch_outputs["Data"] = []
        from sas.guiframe.data_processor import BatchCell
        cell = BatchCell()
        cell.label = data.name
        cell.value = index

        if theory_data != None:
            #Suucessful fit
            theory_data.id = wx.NewId()
            theory_data.name = model.name + "[%s]" % str(data.name)
            if issubclass(theory_data.__class__, Data2D):
                group_id = wx.NewId()
                theory_data.group_id = group_id
                if group_id not in theory_data.list_group_id:
                    theory_data.list_group_id.append(group_id)

            try:
                # associate residuals plot
                if issubclass(residuals.__class__, Data2D):
                    group_id = wx.NewId()
                    residuals.group_id = group_id
                    if group_id not in residuals.list_group_id:
                        residuals.list_group_id.append(group_id)
                batch_outputs["Chi2"][index].object = [residuals]
            except:
                pass

        cell.object = [data, theory_data]
        batch_outputs["Data"].append(cell)
        for key, value in data.meta_data.iteritems():
            if key not in batch_inputs.keys():
                batch_inputs[key] = []
            #if key.lower().strip() != "loader":
            batch_inputs[key].append(value)
        param = "temperature"
        if hasattr(data.sample, param):
            if param not in  batch_inputs.keys():
                batch_inputs[param] = []
            batch_inputs[param].append(data.sample.temperature)

    def _fit_completed(self, result, page_id, batch_outputs,
                       batch_inputs=None, pars=None, elapsed=None):
        """
        Display result of the fit on related panel(s).
        :param result: list of object generated when fit ends
        :param pars: list of names of parameters fitted
        :param page_id: list of page ids which called fit function
        :param elapsed: time spent at the fitting level
        """
        t1 = time.time()
        str_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime(t1))
        msg = "Fit completed on %s \n" % str_time
        msg += "Duration time: %s s.\n" % str(elapsed)
        wx.PostEvent(self.parent, StatusEvent(status=msg, info="info",
                                                      type="stop"))
        wx.PostEvent(self.result_panel, PlotResultEvent(result=result))
        wx.CallAfter(self._update_fit_button, page_id)
        result = result[0]
        self.fit_thread_list = {}
        if page_id is None:
            page_id = []
        ## fit more than 1 model at the same time
        self._mac_sleep(0.2)
        try:
            index = 0
            for uid in page_id:
                res = result[index]
                if res.fitness is None or \
                    not numpy.isfinite(res.fitness) or \
                    numpy.any(res.pvec == None) or \
                    not numpy.all(numpy.isfinite(res.pvec)):
                    msg = "Fitting did not converge!!!"
                    wx.PostEvent(self.parent,
                             StatusEvent(status=msg,
                                         info="warning",
                                         type="stop"))
                    wx.CallAfter(self._update_fit_button, page_id)
                else:
                    #set the panel when fit result are float not list
                    if res.pvec.__class__ == numpy.float64:
                        pvec = [res.pvec]
                    else:
                        pvec = res.pvec
                    if res.stderr.__class__ == numpy.float64:
                        stderr = [res.stderr]
                    else:
                        stderr = res.stderr
                    cpage = self.fit_panel.get_page_by_id(uid)
                    # Make sure we got all results
                    #(CallAfter is important to MAC)
                    try:
                        #if res != None:
                        wx.CallAfter(cpage.onsetValues, res.fitness,
                                     res.param_list,
                                     pvec, stderr)
                        index += 1
                        wx.CallAfter(cpage._on_fit_complete)
                    except KeyboardInterrupt:
                        msg = "Singular point: Fitting Stoped."
                        wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                              info="info",
                                                              type="stop"))
                    except:
                        msg = "Singular point: Fitting Error occurred."
                        wx.PostEvent(self.parent, StatusEvent(status=msg,
                                                              info="error",
                                                              type="stop"))

        except:
            msg = ("Fit completed but the following error occurred: %s"
                   % sys.exc_value)
            #import traceback; msg = "\n".join((traceback.format_exc(), msg))
            wx.PostEvent(self.parent, StatusEvent(status=msg, info="warning",
                                                  type="stop"))

    def _update_fit_button(self, page_id):
        """
        Update Fit button when fit stopped

        : parameter page_id: fitpage where the button is
        """
        if page_id.__class__.__name__ != 'list':
            page_id = [page_id]
        for uid in page_id:
            page = self.fit_panel.get_page_by_id(uid)
            page._on_fit_complete()

    def _on_show_panel(self, event):
        """
        """
        pass

    def on_reset_batch_flag(self, event):
        """
        Set batch_reset_flag
        """
        event.Skip()
        if self.menu1 == None:
            return
        menu_item = self.menu1.FindItemById(self.id_reset_flag)
        flag = menu_item.IsChecked()
        if not flag:
            menu_item.Check(False)
            self.batch_reset_flag = True
        else:
            menu_item.Check(True)
            self.batch_reset_flag = False

        ## post a message to status bar
        msg = "Set Chain Fitting: %s" % str(not self.batch_reset_flag)
        wx.PostEvent(self.parent,
                     StatusEvent(status=msg))


    def _on_slicer_event(self, event):
        """
        Receive a panel as event and send it to guiframe

        :param event: event containing a panel

        """
        if event.panel is not None:
            self.slicer_panels.append(event.panel)
            # Set group ID if available
            event_id = self.parent.popup_panel(event.panel)
            event.panel.uid = event_id
            self.mypanels.append(event.panel)

    def _onclearslicer(self, event):
        """
        Clear the boxslicer when close the panel associate with this slicer
        """
        name = event.GetEventObject().frame.GetTitle()
        for panel in self.slicer_panels:
            if panel.window_caption == name:

                for item in self.parent.panels:
                    if hasattr(self.parent.panels[item], "uid"):
                        if self.parent.panels[item].uid == panel.base.uid:
                            self.parent.panels[item].onClearSlicer(event)
                            #self.parent._mgr.Update()
                            break
                break

    def _on_model_panel(self, evt):
        """
        react to model selection on any combo box or model menu.plot the model

        :param evt: wx.combobox event

        """
        model = evt.model
        uid = evt.uid
        qmin = evt.qmin
        qmax = evt.qmax
        caption = evt.caption
        enable_smearer = evt.enable_smearer
        if model == None:
            return
        if uid not in self.page_finder.keys():
            return
        # save the name containing the data name with the appropriate model
        self.page_finder[uid].set_model(model)
        self.page_finder[uid].enable_smearing(enable_smearer)
        self.page_finder[uid].set_range(qmin=qmin, qmax=qmax)
        self.page_finder[uid].set_fit_tab_caption(caption=caption)
        if self.sim_page is not None and not self.batch_on:
            self.sim_page.draw_page()
        if self.batch_page is not None and self.batch_on:
            self.batch_page.draw_page()

    def _update1D(self, x, output):
        """
        Update the output of plotting model 1D
        """
        msg = "Plot updating ... "
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="update"))

    def _complete1D(self, x, y, page_id, elapsed, index, model,
                    weight=None, fid=None,
                    toggle_mode_on=False, state=None,
                    data=None, update_chisqr=True,
                    source='model', plot_result=True):
        """
        Complete plotting 1D data
        """
        try:
            numpy.nan_to_num(y)

            new_plot = Data1D(x=x, y=y)
            new_plot.is_data = False
            new_plot.dy = numpy.zeros(len(y))
            new_plot.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
            _yaxis, _yunit = data.get_yaxis()
            _xaxis, _xunit = data.get_xaxis()
            new_plot.title = data.name

            new_plot.group_id = data.group_id
            if new_plot.group_id == None:
                new_plot.group_id = data.group_id
            new_plot.id = str(page_id) + " " + data.name
            #if new_plot.id in self.color_dict:
            #    new_plot.custom_color = self.color_dict[new_plot.id]
            #find if this theory was already plotted and replace that plot given
            #the same id
            self.page_finder[page_id].get_theory_data(fid=data.id)

            if data.is_data:
                data_name = str(data.name)
            else:
                data_name = str(model.__class__.__name__)

            new_plot.name = model.name + " [" + data_name + "]"
            new_plot.xaxis(_xaxis, _xunit)
            new_plot.yaxis(_yaxis, _yunit)
            self.page_finder[page_id].set_theory_data(data=new_plot,
                                                      fid=data.id)
            self.parent.update_theory(data_id=data.id, theory=new_plot,
                                       state=state)
            current_pg = self.fit_panel.get_page_by_id(page_id)
            title = new_plot.title
            batch_on = self.fit_panel.get_page_by_id(page_id).batch_on
            if not batch_on:
                wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                            title=str(title)))
            elif plot_result:
                top_data_id = self.fit_panel.get_page_by_id(page_id).data.id
                if data.id == top_data_id:
                    wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                            title=str(title)))
            caption = current_pg.window_caption
            self.page_finder[page_id].set_fit_tab_caption(caption=caption)

            self.page_finder[page_id].set_theory_data(data=new_plot,
                                                      fid=data.id)
            if toggle_mode_on:
                wx.PostEvent(self.parent,
                             NewPlotEvent(group_id=str(page_id) + " Model2D",
                                          action="Hide"))
            else:
                if update_chisqr:
                    wx.PostEvent(current_pg,
                                 Chi2UpdateEvent(output=self._cal_chisqr(
                                                                data=data,
                                                                fid=fid,
                                                                weight=weight,
                                                            page_id=page_id,
                                                            index=index)))
                else:
                    self._plot_residuals(page_id=page_id, data=data, fid=fid,
                                         index=index, weight=weight)

            msg = "Computation  completed!"
            wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))
        except:
            raise

    def _update2D(self, output, time=None):
        """
        Update the output of plotting model
        """
        wx.PostEvent(self.parent, StatusEvent(status="Plot \
        #updating ... ", type="update"))
        #self.ready_fit()

    def _complete2D(self, image, data, model, page_id, elapsed, index, qmin,
                qmax, fid=None, weight=None, toggle_mode_on=False, state=None,
                     update_chisqr=True, source='model', plot_result=True):
        """
        Complete get the result of modelthread and create model 2D
        that can be plot.
        """
        numpy.nan_to_num(image)
        new_plot = Data2D(image=image, err_image=data.err_data)
        new_plot.name = model.name + '2d'
        new_plot.title = "Analytical model 2D "
        new_plot.id = str(page_id) + " " + data.name
        new_plot.group_id = str(page_id) + " Model2D"
        new_plot.detector = data.detector
        new_plot.source = data.source
        new_plot.is_data = False
        new_plot.qx_data = data.qx_data
        new_plot.qy_data = data.qy_data
        new_plot.q_data = data.q_data
        new_plot.mask = data.mask
        ## plot boundaries
        new_plot.ymin = data.ymin
        new_plot.ymax = data.ymax
        new_plot.xmin = data.xmin
        new_plot.xmax = data.xmax
        title = data.title

        new_plot.is_data = False
        if data.is_data:
            data_name = str(data.name)
        else:
            data_name = str(model.__class__.__name__) + '2d'

        if len(title) > 1:
            new_plot.title = "Model2D for %s " % model.name + data_name
        new_plot.name = model.name + " [" + \
                                    data_name + "]"
        theory_data = deepcopy(new_plot)

        self.page_finder[page_id].set_theory_data(data=theory_data,
                                                  fid=data.id)
        self.parent.update_theory(data_id=data.id,
                                       theory=new_plot,
                                       state=state)
        current_pg = self.fit_panel.get_page_by_id(page_id)
        title = new_plot.title
        if not source == 'fit' and plot_result:
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot,
                                               title=title))
        if toggle_mode_on:
            wx.PostEvent(self.parent,
                             NewPlotEvent(group_id=str(page_id) + " Model1D",
                                               action="Hide"))
        else:
            # Chisqr in fitpage
            if update_chisqr:
                wx.PostEvent(current_pg,
                             Chi2UpdateEvent(output=self._cal_chisqr(data=data,
                                                                    weight=weight,
                                                                    fid=fid,
                                                         page_id=page_id,
                                                         index=index)))
            else:
                self._plot_residuals(page_id=page_id, data=data, fid=fid,
                                      index=index, weight=weight)
        msg = "Computation  completed!"
        wx.PostEvent(self.parent, StatusEvent(status=msg, type="stop"))

    def _draw_model2D(self, model, page_id, qmin,
                      qmax,
                      data=None, smearer=None,
                      description=None, enable2D=False,
                      state=None,
                      fid=None,
                      weight=None,
                      toggle_mode_on=False,
                       update_chisqr=True, source='model'):
        """
        draw model in 2D

        :param model: instance of the model to draw
        :param description: the description of the model
        :param enable2D: when True allows to draw model 2D
        :param qmin: the minimum value to  draw model 2D
        :param qmax: the maximum value to draw model 2D
        :param qstep: the number of division of Qx and Qy of the model to draw

        """
        if not enable2D:
            return None
        try:
            from model_thread import Calc2D
            ## If a thread is already started, stop it
            if (self.calc_2D is not None) and self.calc_2D.isrunning():
                self.calc_2D.stop()
                ## stop just raises a flag to tell the thread to kill
                ## itself -- see the fix in Calc1D implemented to fix
                ## an actual problem.  Seems the fix should also go here
                ## and may be the cause of other noted instabilities
                ##
                ##    -PDB August 12, 2014 
                while self.calc_2D.isrunning():
                    time.sleep(0.1)
            self.calc_2D = Calc2D(model=model,
                                    data=data,
                                    page_id=page_id,
                                    smearer=smearer,
                                    qmin=qmin,
                                    qmax=qmax,
                                    weight=weight,
                                    fid=fid,
                                    toggle_mode_on=toggle_mode_on,
                                    state=state,
                                    completefn=self._complete2D,
                                    update_chisqr=update_chisqr, source=source)
            self.calc_2D.queue()
        except:
            raise

    def _draw_model1D(self, model, page_id, data,
                      qmin, qmax, smearer=None,
                state=None,
                weight=None,
                fid=None,
                toggle_mode_on=False, update_chisqr=True, source='model',
                enable1D=True):
        """
        Draw model 1D from loaded data1D

        :param data: loaded data
        :param model: the model to plot

        """
        if not enable1D:
            return
        try:
            from model_thread import Calc1D
            ## If a thread is already started, stop it
            if (self.calc_1D is not None) and self.calc_1D.isrunning():
                self.calc_1D.stop()
                ## stop just raises the flag -- the thread is supposed to 
                ## then kill itself but cannot.  Paul Kienzle came up with
                ## this fix to prevent threads from stepping on each other
                ## which was causing a simple custom model to crash Sasview.
                ## We still don't know why the fit sometimes lauched a second
                ## thread -- something which should also be investigated.
                ## The thread approach was implemented in order to be able
                ## to lauch a computation in a separate thread from the GUI so
                ## that the GUI can still respond to user input including
                ## a request to stop the computation.
                ## It seems thus that the whole thread approach used here
                ## May need rethinking  
                ##
                ##    -PDB August 12, 2014                  
                while self.calc_1D.isrunning():
                    time.sleep(0.1)
            self.calc_1D = Calc1D(data=data,
                                  model=model,
                                  page_id=page_id,
                                  qmin=qmin,
                                  qmax=qmax,
                                  smearer=smearer,
                                  state=state,
                                  weight=weight,
                                  fid=fid,
                                  toggle_mode_on=toggle_mode_on,
                                  completefn=self._complete1D,
                                  #updatefn = self._update1D,
                                  update_chisqr=update_chisqr,
                                  source=source)
            self.calc_1D.queue()
        except:
            msg = " Error occurred when drawing %s Model 1D: " % model.name
            msg += " %s" % sys.exc_value
            wx.PostEvent(self.parent, StatusEvent(status=msg))

    def _cal_chisqr(self, page_id, data, weight, fid=None, index=None):
        """
        Get handy Chisqr using the output from draw1D and 2D,
        instead of calling expansive CalcChisqr in guithread
        """
        try:
            data_copy = deepcopy(data)
        except:
            return
        # default chisqr
        chisqr = None
        #to compute chisq make sure data has valid data
        # return None if data == None
        if not check_data_validity(data_copy) or data_copy == None:
            return chisqr

        # Get data: data I, theory I, and data dI in order
        if data_copy.__class__.__name__ == "Data2D":
            if index == None:
                index = numpy.ones(len(data_copy.data), dtype=bool)
            if weight != None:
                data_copy.err_data = weight
            # get rid of zero error points
            index = index & (data_copy.err_data != 0)
            index = index & (numpy.isfinite(data_copy.data))
            fn = data_copy.data[index]
            theory_data = self.page_finder[page_id].get_theory_data(fid=data_copy.id)
            if theory_data == None:
                return chisqr
            gn = theory_data.data[index]
            en = data_copy.err_data[index]
        else:
            # 1 d theory from model_thread is only in the range of index
            if index == None:
                index = numpy.ones(len(data_copy.y), dtype=bool)
            if weight != None:
                data_copy.dy = weight
            if data_copy.dy == None or data_copy.dy == []:
                dy = numpy.ones(len(data_copy.y))
            else:
                ## Set consistently w/AbstractFitengine:
                # But this should be corrected later.
                dy = deepcopy(data_copy.dy)
                dy[dy == 0] = 1
            fn = data_copy.y[index]

            theory_data = self.page_finder[page_id].get_theory_data(fid=data_copy.id)
            if theory_data == None:
                return chisqr
            gn = theory_data.y
            en = dy[index]

        # residual
        try:
            res = (fn - gn) / en
        except ValueError:
            print "Unmatch lengths %s, %s, %s" % (len(fn), len(gn), len(en))
            return

        residuals = res[numpy.isfinite(res)]
        # get chisqr only w/finite
        chisqr = numpy.average(residuals * residuals)

        self._plot_residuals(page_id=page_id, data=data_copy,
                             fid=fid,
                             weight=weight, index=index)

        return chisqr

    def _plot_residuals(self, page_id, weight, fid=None,
                        data=None, index=None):
        """
        Plot the residuals

        :param data: data
        :param index: index array (bool)
        : Note: this is different from the residuals in cal_chisqr()
        """
        data_copy = deepcopy(data)
        # Get data: data I, theory I, and data dI in order
        if data_copy.__class__.__name__ == "Data2D":
            # build residuals
            residuals = Data2D()
            #residuals.copy_from_datainfo(data)
            # Not for trunk the line below, instead use the line above
            data_copy.clone_without_data(len(data_copy.data), residuals)
            residuals.data = None
            fn = data_copy.data
            theory_data = self.page_finder[page_id].get_theory_data(fid=data_copy.id)
            gn = theory_data.data
            if weight == None:
                en = data_copy.err_data
            else:
                en = weight
            residuals.data = (fn - gn) / en
            residuals.qx_data = data_copy.qx_data
            residuals.qy_data = data_copy.qy_data
            residuals.q_data = data_copy.q_data
            residuals.err_data = numpy.ones(len(residuals.data))
            residuals.xmin = min(residuals.qx_data)
            residuals.xmax = max(residuals.qx_data)
            residuals.ymin = min(residuals.qy_data)
            residuals.ymax = max(residuals.qy_data)
            residuals.q_data = data_copy.q_data
            residuals.mask = data_copy.mask
            residuals.scale = 'linear'
            # check the lengths
            if len(residuals.data) != len(residuals.q_data):
                return
        else:
            # 1 d theory from model_thread is only in the range of index
            if data_copy.dy == None or data_copy.dy == []:
                dy = numpy.ones(len(data_copy.y))
            else:
                if weight == None:
                    dy = numpy.ones(len(data_copy.y))
                ## Set consitently w/AbstractFitengine:
                ## But this should be corrected later.
                else:
                    dy = weight
                dy[dy == 0] = 1
            fn = data_copy.y[index]
            theory_data = self.page_finder[page_id].get_theory_data(fid=data_copy.id)
            gn = theory_data.y
            en = dy[index]
            # build residuals
            residuals = Data1D()
            try:
                residuals.y = (fn - gn) / en
            except:
                msg = "ResidualPlot Error: different # of data points in theory"
                wx.PostEvent(self.parent, StatusEvent(status=msg, info="error"))
                residuals.y = (fn - gn[index]) / en
            residuals.x = data_copy.x[index]
            residuals.dy = numpy.ones(len(residuals.y))
            residuals.dx = None
            residuals.dxl = None
            residuals.dxw = None
            residuals.ytransform = 'y'
            # For latter scale changes 
            residuals.xaxis('\\rm{Q} ', 'A^{-1}')
            residuals.yaxis('\\rm{Residuals} ', 'normalized')
        theory_name = str(theory_data.name.split()[0])
        new_plot = residuals
        new_plot.name = "Residuals for " + str(theory_name) + "[" + \
                        str(data.name) + "]"
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        new_plot.id = "res" + str(data_copy.id) + str(theory_name)
        ##group_id specify on which panel to plot this data
        group_id = self.page_finder[page_id].get_graph_id()
        if group_id == None:
            group_id = data.group_id
        new_plot.group_id = "res" + str(group_id)
        #new_plot.is_data = True
        ##post data to plot
        title = new_plot.name
        self.page_finder[page_id].set_residuals(residuals=new_plot,
                                                fid=data.id)
        self.parent.update_theory(data_id=data.id, theory=new_plot)
        batch_on = self.fit_panel.get_page_by_id(page_id).batch_on
        if not batch_on:
            wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=title))

'''
This module provides three model editor classes: the composite model editor,
the easy editor which provides a simple interface with tooltip help to enter
the parameters of the model and their default value and a panel to input a
function of y (usually the intensity).  It also provides a drop down of
standard available math functions.  Finally a full python editor panel for
complete customization is provided.

:TODO the writing of the file and name checking (and maybe some other
functions?) should be moved to a computational module which could be called
from a python script.  Basically one just needs to pass the name,
description text and function text (or in the case of the composite editor
the names of the first and second model and the operator to be used).
'''

################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################


import wx
import sys
import os
import math
import re
import logging
import datetime

from wx.py.editwindow import EditWindow

from sas.sasgui.guiframe.documentation_window import DocumentationWindow

from .pyconsole import show_model_output, check_model

logger = logging.getLogger(__name__)

if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
    PNL_WIDTH = 450
    PNL_HEIGHT = 320
else:
    FONT_VARIANT = 1
    PNL_WIDTH = 590
    PNL_HEIGHT = 350
M_NAME = 'Model'
EDITOR_WIDTH = 800
EDITOR_HEIGTH = 735
PANEL_WIDTH = 500
_BOX_WIDTH = 55

def _delete_file(path):
    """
    Delete file in the path
    """
    try:
        os.remove(path)
    except:
        raise


class TextDialog(wx.Dialog):
    """
    Dialog for easy custom composite models.  Provides a wx.Dialog panel
    to choose two existing models (including pre-existing Plugin Models which
    may themselves be composite models) as well as an operation on those models
    (add or multiply) the resulting model will add a scale parameter for summed
    models and a background parameter for a multiplied model.

    The user also gives a brief help for the model in a description box and
    must provide a unique name which is verified as unique before the new
    model is saved.

    This Dialog pops up for the user when they press 'Sum|Multi(p1,p2)' under
    'Plugin Model Operations' under 'Fitting' menu.  This is currently called as
    a Modal Dialog.

    :TODO the built in compiler currently balks at when it tries to import
    a model whose name contains spaces or symbols (such as + ... underscore
    should be fine).  Have fixed so the editor cannot save such a file name
    but if a file is dropped in the plugin directory from outside this class
    will create a file that cannot be compiled.  Should add the check to
    the write method or to the on_modelx method.

    - PDB:April 5, 2015
    """
    def __init__(self, parent=None, base=None, id=None, title='',
                 model_list=[], plugin_dir=None):
        """
        This class is run when instatiated.  The __init__ initializes and
        calls the internal methods necessary.  On exiting the wx.Dialog
        window should be destroyed.
        """
        wx.Dialog.__init__(self, parent=parent, id=id,
                           title=title, size=(PNL_WIDTH, PNL_HEIGHT))
        self.parent = base
        #Font
        self.SetWindowVariant(variant=FONT_VARIANT)
        # default
        self.overwrite_name = False
        self.plugin_dir = plugin_dir
        self.model_list = model_list
        self.model1_string = "sphere"
        self.model2_string = "cylinder"
        self.name = 'Sum' + M_NAME
        self._notes = ''
        self._operator = '+'
        self._operator_choice = None
        self.explanation = ''
        self.explanationctr = None
        self.type = None
        self.name_sizer = None
        self.name_tcl = None
        self.desc_sizer = None
        self.desc_tcl = None
        self._selection_box = None
        self.model1 = None
        self.model2 = None
        self.static_line_1 = None
        self.ok_button = None
        self.close_button = None
        self._msg_box = None
        self.msg_sizer = None
        self.fname = None
        self.cm_list = None
        self.is_p1_custom = False
        self.is_p2_custom = False
        self._build_sizer()
        self.model1_name = str(self.model1.GetValue())
        self.model2_name = str(self.model2.GetValue())
        self.good_name = True
        self.fill_operator_combox()

    def _layout_name(self):
        """
        Do the layout for file/function name related widgets
        """
        #container for new model name input
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #set up label and input box with tool tip and event handling
        name_txt = wx.StaticText(self, -1, 'Function Name : ')
        self.name_tcl = wx.TextCtrl(self, -1, value='MySumFunction')
        self.name_tcl.Bind(wx.EVT_TEXT_ENTER, self.on_change_name)
        hint_name = "Unique Sum/Multiply Model Function Name."
        self.name_tcl.SetToolTipString(hint_name)

        self.name_sizer.AddMany([(name_txt, 0, wx.LEFT | wx.TOP, 10),
                                 (self.name_tcl, -1,
                                  wx.EXPAND | wx.RIGHT | wx.TOP | wx.BOTTOM,
                                  10)])


    def _layout_description(self):
        """
        Do the layout for description related widgets
        """
        #container for new model description input
        self.desc_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #set up description label and input box with tool tip and event handling
        desc_txt = wx.StaticText(self, -1, 'Description (optional) : ')
        self.desc_tcl = wx.TextCtrl(self, -1)
        hint_desc = "Write a short description of this model function."
        self.desc_tcl.SetToolTipString(hint_desc)

        self.desc_sizer.AddMany([(desc_txt, 0, wx.LEFT | wx.TOP, 10),
                                 (self.desc_tcl, -1,
                                  wx.EXPAND | wx.RIGHT | wx.TOP | wx.BOTTOM,
                                  10)])


    def _layout_model_selection(self):
        """
        Do the layout for model selection related widgets
        """
        box_width = 195 # combobox width

        #First set up main sizer for the selection
        selection_box_title = wx.StaticBox(self, -1, 'Select',
                                           size=(PNL_WIDTH - 30, 70))
        self._selection_box = wx.StaticBoxSizer(selection_box_title,
                                                wx.VERTICAL)

        #Next create the help labels for the model selection
        select_help_box = wx.BoxSizer(wx.HORIZONTAL)
        model_string = " Model%s (p%s):"
        select_help_box.Add(wx.StaticText(self, -1, model_string % (1, 1)),
                            0, 0)
        select_help_box.Add((box_width - 25, 10), 0, 0)
        select_help_box.Add(wx.StaticText(self, -1, model_string % (2, 2)),
                            0, 0)
        self._selection_box.Add(select_help_box, 0, 0)

        #Next create the actual selection box with 3 combo boxes
        selection_box_choose = wx.BoxSizer(wx.HORIZONTAL)

        self.model1 = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.model1, -1, self.on_model1)
        self.model1.SetMinSize((box_width * 5 / 6, -1))
        self.model1.SetToolTipString("model1")

        self._operator_choice = wx.ComboBox(self, -1, size=(50, -1),
                                            style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self._operator_choice, -1, self.on_select_operator)
        operation_tip = "Add: +, Multiply: * "
        self._operator_choice.SetToolTipString(operation_tip)

        self.model2 = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.model2, -1, self.on_model2)
        self.model2.SetMinSize((box_width * 5 / 6, -1))
        self.model2.SetToolTipString("model2")
        self._set_model_list()

        selection_box_choose.Add(self.model1, 0, 0)
        selection_box_choose.Add((15, 10))
        selection_box_choose.Add(self._operator_choice, 0, 0)
        selection_box_choose.Add((15, 10))
        selection_box_choose.Add(self.model2, 0, 0)
        # add some space between labels and selection
        self._selection_box.Add((20, 5), 0, 0)
        self._selection_box.Add(selection_box_choose, 0, 0)

    def _build_sizer(self):
        """
        Build GUI with calls to _layout_name, _layout Description
        and _layout_model_selection which each build a their portion of the
        GUI.
        """
        mainsizer = wx.BoxSizer(wx.VERTICAL) # create main sizer for dialog

        # build fromm top by calling _layout_name and _layout_description
        # and adding to main sizer
        self._layout_name()
        mainsizer.Add(self.name_sizer, 0, wx.EXPAND)
        self._layout_description()
        mainsizer.Add(self.desc_sizer, 0, wx.EXPAND)

        # Add an explanation of dialog (short help)
        self.explanationctr = wx.StaticText(self, -1, self.explanation)
        self.fill_explanation_helpstring(self._operator)
        mainsizer.Add(self.explanationctr, 0, wx.LEFT | wx.EXPAND, 15)

        # Add the selection box stuff with border and labels built
        # by _layout_model_selection
        self._layout_model_selection()
        mainsizer.Add(self._selection_box, 0, wx.LEFT, 15)

        # Add a space and horizontal line before the notification
        #messages and the buttons at the bottom
        mainsizer.Add((10, 10))
        self.static_line_1 = wx.StaticLine(self, -1)
        mainsizer.Add(self.static_line_1, 0, wx.EXPAND, 10)

        # Add action status notification line (null at startup)
        self._msg_box = wx.StaticText(self, -1, self._notes)
        self.msg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.msg_sizer.Add(self._msg_box, 0, wx.LEFT, 0)
        mainsizer.Add(self.msg_sizer, 0,
                      wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE | wx.BOTTOM, 10)

        # Finally add the buttons (apply and close) on the bottom
        # Eventually need to add help here
        self.ok_button = wx.Button(self, wx.ID_OK, 'Apply')
        _app_tip = "Save the new Model."
        self.ok_button.SetToolTipString(_app_tip)
        self.ok_button.Bind(wx.EVT_BUTTON, self.check_name)
        self.help_button = wx.Button(self, -1, 'HELP')
        _app_tip = "Help on composite model creation."
        self.help_button.SetToolTipString(_app_tip)
        self.help_button.Bind(wx.EVT_BUTTON, self.on_help)
        self.close_button = wx.Button(self, wx.ID_CANCEL, 'Close')
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.AddMany([((20, 20), 1, 0),
                              (self.ok_button, 0, 0),
                              (self.help_button, 0, 0),
                              (self.close_button, 0, wx.LEFT | wx.RIGHT, 10)])
        mainsizer.Add(sizer_button, 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 10)

        self.SetSizer(mainsizer)
        self.Centre()

    def on_change_name(self, event=None):
        """
        Change name
        """
        if event is not None:
            event.Skip()
        self.name_tcl.SetBackgroundColour('white')
        self.Refresh()

    def check_name(self, event=None):
        """
        Check that proposed new model name is a valid Python module name
        and that it does not already exist. If not show error message and
        pink background in text box else call on_apply

        :TODO this should be separated out from the GUI code.  For that we
        need to pass it the name (or if we want to keep the default name
        option also need to pass the self._operator attribute) We just need
        the function to return an error code that the name is good or if
        not why (not a valid name, name exists already).  The rest of the
        error handling should be done in this module. so on_apply would then
        start by checking the name and then either raise errors or do the
        deed.
        """
        #Get the function/file name
        mname = M_NAME
        self.on_change_name(None)
        title = self.name_tcl.GetValue().lstrip().rstrip()
        if title == '':
            text = self._operator
            if text.count('+') > 0:
                mname = 'Sum'
            else:
                mname = 'Multi'
            mname += M_NAME
            title = mname
        self.name = title
        t_fname = title + '.py'

        #First check if the name is a valid Python name
        if re.match('^[A-Za-z0-9_]*$', title):
            self.good_name = True
        else:
            self.good_name = False
            msg = ("%s is not a valid Python name. Only alphanumeric \n" \
                   "and underscore allowed" % self.name)

        #Now check if the name already exists
        if not self.overwrite_name and self.good_name:
            #Create list of existing model names for comparison
            list_fnames = os.listdir(self.plugin_dir)
            # fake existing regular model name list
            m_list = [model.name + ".py" for model in self.model_list]
            list_fnames.append(m_list)
            if t_fname in list_fnames and title != mname:
                self.good_name = False
                msg = "Name exists already."

        if self.good_name == False:
            self.name_tcl.SetBackgroundColour('pink')
            info = 'Error'
            wx.MessageBox(msg, info)
            self._notes = msg
            color = 'red'
            self._msg_box.SetLabel(msg)
            self._msg_box.SetForegroundColour(color)
            return self.good_name
        self.fname = os.path.join(self.plugin_dir, t_fname)
        s_title = title
        if len(title) > 20:
            s_title = title[0:19] + '...'
        self._notes = "Model function (%s) has been set! \n" % str(s_title)
        self.good_name = True
        self.on_apply(self.fname)
        return self.good_name

    def on_apply(self, path):
        """
        This method is a misnomer - it is not bound to the apply button
        event.  Instead the apply button event goes to check_name which
        then calls this method if the name of the new file is acceptable.

        :TODO this should be bound to the apply button.  The first line
        should call the check_name method which itself should be in another
        module separated from the the GUI modules.
        """
        self.name_tcl.SetBackgroundColour('white')
        try:
            label = self.get_textnames()
            fname = path
            name1 = label[0]
            name2 = label[1]
            self.write_string(fname, name1, name2)
            success = show_model_output(self, fname)
            if success:
                self.parent.update_custom_combo()
            msg = self._notes
            info = 'Info'
            color = 'blue'
        except:
            msg = "Easy Sum/Multipy Plugin: Error occurred..."
            info = 'Error'
            color = 'red'
        self._msg_box.SetLabel(msg)
        self._msg_box.SetForegroundColour(color)
        if self.parent.parent is not None:
            from sas.sasgui.guiframe.events import StatusEvent
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg,
                                                         info=info))

    def on_help(self, event):
        """
        Bring up the Composite Model Editor Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/fitting/fitting_help.html"
        _PageAnchor = "#sum-multi-p1-p2"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, _PageAnchor,
                                          "Composite Model Editor Help")

    def _set_model_list(self):
        """
        Set the list of models
        """
        # list of model names
        # get regular models
        main_list = self.model_list
        # get custom models
        self.update_cm_list()
        # add custom models to model list
        for name in self.cm_list:
            if name not in main_list:
                main_list.append(name)

        if len(main_list) > 1:
            main_list.sort()
        for idx in range(len(main_list)):
            self.model1.Append(str(main_list[idx]), idx)
            self.model2.Append(str(main_list[idx]), idx)
        self.model1.SetStringSelection(self.model1_string)
        self.model2.SetStringSelection(self.model2_string)

    def update_cm_list(self):
        """
        Update custom model list
        """
        cm_list = []
        al_list = os.listdir(self.plugin_dir)
        for c_name in al_list:
            if c_name.split('.')[-1] == 'py' and \
                    c_name.split('.')[0] != '__init__':
                name = str(c_name.split('.')[0])
                cm_list.append(name)
        self.cm_list = cm_list

    def on_model1(self, event):
        """
        Set model1
        """
        event.Skip()
        self.update_cm_list()
        self.model1_name = str(self.model1.GetValue())
        self.model1_string = self.model1_name
        if self.model1_name in self.cm_list:
            self.is_p1_custom = True
        else:
            self.is_p1_custom = False

    def on_model2(self, event):
        """
        Set model2
        """
        event.Skip()
        self.update_cm_list()
        self.model2_name = str(self.model2.GetValue())
        self.model2_string = self.model2_name
        if self.model2_name in self.cm_list:
            self.is_p2_custom = True
        else:
            self.is_p2_custom = False

    def on_select_operator(self, event=None):
        """
        On Select an Operator
        """
        # For Mac
        if event is not None:
            event.Skip()
        item = event.GetEventObject()
        text = item.GetValue()
        self.fill_explanation_helpstring(text)

    def fill_explanation_helpstring(self, operator):
        """
        Choose the equation to use depending on whether we now have
        a sum or multiply model then create the appropriate string
        """
        name = ''
        if operator == '*':
            name = 'Multi'
            factor = 'background'
        else:
            name = 'Sum'
            factor = 'scale_factor'

        self._operator = operator
        self.explanation = ("  Plugin_model = scale_factor * (model_1 {} "
            "model_2) + background").format(operator)
        self.explanationctr.SetLabel(self.explanation)
        self.name = name + M_NAME


    def fill_operator_combox(self):
        """
        fill the current combobox with the operator
        """
        operator_list = ['+', '*']
        for oper in operator_list:
            pos = self._operator_choice.Append(str(oper))
            self._operator_choice.SetClientData(pos, str(oper))
        self._operator_choice.SetSelection(0)

    def get_textnames(self):
        """
        Returns model name string as list
        """
        return [self.model1_name, self.model2_name]

    def write_string(self, fname, model1_name, model2_name):
        """
        Write and Save file
        """
        self.fname = fname
        description = self.desc_tcl.GetValue().lstrip().rstrip()
        desc_line = ''
        if description.strip() != '':
            # Sasmodels generates a description for us. If the user provides
            # their own description, add a line to overwrite the sasmodels one
            desc_line = "\nmodel_info.description = '{}'".format(description)
        name = os.path.splitext(os.path.basename(self.fname))[0]
        output = SUM_TEMPLATE.format(name=name, model1=model1_name,
            model2=model2_name, operator=self._operator, desc_line=desc_line)
        with open(self.fname, 'w') as out_f:
            out_f.write(output)

    def compile_file(self, path):
        """
        Compile the file in the path
        """
        path = self.fname
        show_model_output(self, path)

    def delete_file(self, path):
        """
        Delete file in the path
        """
        _delete_file(path)


class EditorPanel(wx.ScrolledWindow):
    """
    Simple Plugin Model function editor
    """
    def __init__(self, parent, base, path, title, *args, **kwds):
        kwds['name'] = title
#        kwds["size"] = (EDITOR_WIDTH, EDITOR_HEIGTH)
        kwds["style"] = wx.FULL_REPAINT_ON_RESIZE
        wx.ScrolledWindow.__init__(self, parent, *args, **kwds)
        self.SetScrollbars(1,1,1,1)
        self.parent = parent
        self.base = base
        self.path = path
        self.font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(10)
        self.reader = None
        self.name = 'untitled'
        self.overwrite_name = False
        self.is_2d = False
        self.fname = None
        self.main_sizer = None
        self.name_sizer = None
        self.name_hsizer = None
        self.name_tcl = None
        self.overwrite_cb = None
        self.desc_sizer = None
        self.desc_tcl = None
        self.param_sizer = None
        self.param_tcl = None
        self.function_sizer = None
        self.func_horizon_sizer = None
        self.button_sizer = None
        self.param_strings = ''
        self.function_strings = ''
        self._notes = ""
        self._msg_box = None
        self.msg_sizer = None
        self.warning = ""
        #This does not seem to be used anywhere so commenting out for now
        #    -- PDB 2/26/17
        #self._description = "New Plugin Model"
        self.function_tcl = None
        self.math_combo = None
        self.bt_apply = None
        self.bt_close = None
        #self._default_save_location = os.getcwd()
        self._do_layout()



    def _define_structure(self):
        """
        define initial sizer
        """
        #w, h = self.parent.GetSize()
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.name_sizer = wx.BoxSizer(wx.VERTICAL)
        self.name_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.desc_sizer = wx.BoxSizer(wx.VERTICAL)
        self.param_sizer = wx.BoxSizer(wx.VERTICAL)
        self.function_sizer = wx.BoxSizer(wx.VERTICAL)
        self.func_horizon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.msg_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_name(self):
        """
        Do the layout for file/function name related widgets
        """
        #title name [string]
        name_txt = wx.StaticText(self, -1, 'Function Name : ')
        self.overwrite_cb = wx.CheckBox(self, -1, "Overwrite existing plugin model of this name?", (10, 10))
        self.overwrite_cb.SetValue(False)
        self.overwrite_cb.SetToolTipString("Overwrite it if already exists?")
        wx.EVT_CHECKBOX(self, self.overwrite_cb.GetId(), self.on_over_cb)
        self.name_tcl = wx.TextCtrl(self, -1, size=(PANEL_WIDTH * 3 / 5, -1))
        self.name_tcl.Bind(wx.EVT_TEXT_ENTER, self.on_change_name)
        self.name_tcl.SetValue('')
        self.name_tcl.SetFont(self.font)
        hint_name = "Unique Model Function Name."
        self.name_tcl.SetToolTipString(hint_name)
        self.name_hsizer.AddMany([(self.name_tcl, 0, wx.LEFT | wx.TOP, 0),
                                  (self.overwrite_cb, 0, wx.LEFT, 20)])
        self.name_sizer.AddMany([(name_txt, 0, wx.LEFT | wx.TOP, 10),
                                 (self.name_hsizer, 0,
                                  wx.LEFT | wx.TOP | wx.BOTTOM, 10)])


    def _layout_description(self):
        """
        Do the layout for description related widgets
        """
        #title name [string]
        desc_txt = wx.StaticText(self, -1, 'Description (optional) : ')
        self.desc_tcl = wx.TextCtrl(self, -1, size=(PANEL_WIDTH * 3 / 5, -1))
        self.desc_tcl.SetValue('')
        hint_desc = "Write a short description of the model function."
        self.desc_tcl.SetToolTipString(hint_desc)
        self.desc_sizer.AddMany([(desc_txt, 0, wx.LEFT | wx.TOP, 10),
                                 (self.desc_tcl, 0,
                                  wx.LEFT | wx.TOP | wx.BOTTOM, 10)])
    def _layout_param(self):
        """
        Do the layout for parameter related widgets
        """
        param_txt = wx.StaticText(self, -1, 'Fit Parameters NOT requiring' + \
                                  ' polydispersity (if any): ')

        param_tip = "#Set the parameters NOT requiring polydispersity " + \
        "and their initial values.\n"
        param_tip += "#Example:\n"
        param_tip += "A = 1\nB = 1"
        #param_txt.SetToolTipString(param_tip)
        newid = wx.NewId()
        self.param_tcl = EditWindow(self, newid, wx.DefaultPosition,
                                    wx.DefaultSize,
                                    wx.CLIP_CHILDREN | wx.SUNKEN_BORDER)
        self.param_tcl.setDisplayLineNumbers(True)
        self.param_tcl.SetToolTipString(param_tip)

        self.param_sizer.AddMany([(param_txt, 0, wx.LEFT, 10),
                                  (self.param_tcl, 1, wx.EXPAND | wx.ALL, 10)])

        # Parameters with polydispersity
        pd_param_txt = wx.StaticText(self, -1, 'Fit Parameters requiring ' + \
                                     'polydispersity (if any): ')

        pd_param_tip = "#Set the parameters requiring polydispersity and " + \
        "their initial values.\n"
        pd_param_tip += "#Example:\n"
        pd_param_tip += "C = 2\nD = 2"
        newid = wx.NewId()
        self.pd_param_tcl = EditWindow(self, newid, wx.DefaultPosition,
                                    wx.DefaultSize,
                                    wx.CLIP_CHILDREN | wx.SUNKEN_BORDER)
        self.pd_param_tcl.setDisplayLineNumbers(True)
        self.pd_param_tcl.SetToolTipString(pd_param_tip)

        self.param_sizer.AddMany([(pd_param_txt, 0, wx.LEFT, 10),
                                  (self.pd_param_tcl, 1, wx.EXPAND | wx.ALL, 10)])

    def _layout_function(self):
        """
        Do the layout for function related widgets
        """
        function_txt = wx.StaticText(self, -1, 'Function(x) : ')
        hint_function = "#Example:\n"
        hint_function += "if x <= 0:\n"
        hint_function += "    y = A + B\n"
        hint_function += "else:\n"
        hint_function += "    y = A + B * cos(2 * pi * x)\n"
        hint_function += "return y\n"
        math_txt = wx.StaticText(self, -1, '*Useful math functions: ')
        math_combo = self._fill_math_combo()

        newid = wx.NewId()
        self.function_tcl = EditWindow(self, newid, wx.DefaultPosition,
                                       wx.DefaultSize,
                                       wx.CLIP_CHILDREN | wx.SUNKEN_BORDER)
        self.function_tcl.setDisplayLineNumbers(True)
        self.function_tcl.SetToolTipString(hint_function)

        self.func_horizon_sizer.Add(function_txt)
        self.func_horizon_sizer.Add(math_txt, 0, wx.LEFT, 250)
        self.func_horizon_sizer.Add(math_combo, 0, wx.LEFT, 10)

        self.function_sizer.Add(self.func_horizon_sizer, 0, wx.LEFT, 10)
        self.function_sizer.Add(self.function_tcl, 1, wx.EXPAND | wx.ALL, 10)

    def _layout_msg(self):
        """
        Layout msg
        """
        self._msg_box = wx.StaticText(self, -1, self._notes,
                                      size=(PANEL_WIDTH, -1))
        self.msg_sizer.Add(self._msg_box, 0, wx.LEFT, 10)

    def _layout_button(self):
        """
        Do the layout for the button widgets
        """
        self.bt_apply = wx.Button(self, -1, "Apply", size=(_BOX_WIDTH, -1))
        self.bt_apply.SetToolTipString("Save changes into the imported data.")
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)

        self.bt_help = wx.Button(self, -1, "HELP", size=(_BOX_WIDTH, -1))
        self.bt_help.SetToolTipString("Get Help For Model Editor")
        self.bt_help.Bind(wx.EVT_BUTTON, self.on_help)

        self.bt_close = wx.Button(self, -1, 'Close', size=(_BOX_WIDTH, -1))
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.bt_close.SetToolTipString("Close this panel.")

        self.button_sizer.AddMany([(self.bt_apply, 0,0),
                                   (self.bt_help, 0, wx.LEFT | wx.BOTTOM,15),
                                   (self.bt_close, 0, wx.LEFT | wx.RIGHT, 15)])

    def _do_layout(self):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_name()
        self._layout_description()
        self._layout_param()
        self._layout_function()
        self._layout_msg()
        self._layout_button()
        self.main_sizer.AddMany([(self.name_sizer, 0, wx.EXPAND | wx.ALL, 5),
                                 (wx.StaticLine(self), 0,
                                  wx.ALL | wx.EXPAND, 5),
                                 (self.desc_sizer, 0, wx.EXPAND | wx.ALL, 5),
                                 (wx.StaticLine(self), 0,
                                  wx.ALL | wx.EXPAND, 5),
                                 (self.param_sizer, 1, wx.EXPAND | wx.ALL, 5),
                                 (wx.StaticLine(self), 0,
                                  wx.ALL | wx.EXPAND, 5),
                                 (self.function_sizer, 2,
                                  wx.EXPAND | wx.ALL, 5),
                                 (wx.StaticLine(self), 0,
                                  wx.ALL | wx.EXPAND, 5),
                                 (self.msg_sizer, 0, wx.EXPAND | wx.ALL, 5),
                                 (self.button_sizer, 0, wx.ALIGN_RIGHT)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def _fill_math_combo(self):
        """
        Fill up the math combo box
        """
        self.math_combo = wx.ComboBox(self, -1, size=(100, -1),
                                      style=wx.CB_READONLY)
        for item in dir(math):
            if item.count("_") < 1:
                try:
                    exec("float(math.%s)" % item)
                    self.math_combo.Append(str(item))
                except Exception:
                    self.math_combo.Append(str(item) + "()")
        self.math_combo.Bind(wx.EVT_COMBOBOX, self._on_math_select)
        self.math_combo.SetSelection(0)
        return self.math_combo

    def _on_math_select(self, event):
        """
        On math selection on ComboBox
        """
        event.Skip()
        label = self.math_combo.GetValue()
        self.function_tcl.SetFocus()
        # Put the text at the cursor position
        pos = self.function_tcl.GetCurrentPos()
        self.function_tcl.InsertText(pos, label)
        # Put the cursor at appropriate position
        length = len(label)
        print(length)
        if label[length-1] == ')':
            length -= 1
        f_pos = pos + length
        self.function_tcl.GotoPos(f_pos)

    def get_notes(self):
        """
        return notes
        """
        return self._notes

    def on_change_name(self, event=None):
        """
        Change name
        """
        if event is not None:
            event.Skip()
        self.name_tcl.SetBackgroundColour('white')
        self.Refresh()

    def check_name(self):
        """
        Check name if exist already
        """
        self._notes = ''
        self.on_change_name(None)
        plugin_dir = self.path
        list_fnames = os.listdir(plugin_dir)
        # function/file name
        title = self.name_tcl.GetValue().lstrip().rstrip()
        self.name = title
        t_fname = title + '.py'
        if not self.overwrite_name:
            if t_fname in list_fnames:
                self.name_tcl.SetBackgroundColour('pink')
                return False
        self.fname = os.path.join(plugin_dir, t_fname)
        s_title = title
        if len(title) > 20:
            s_title = title[0:19] + '...'
        self._notes += "Model function name is set "
        self._notes += "to %s. \n" % str(s_title)
        return True

    def on_over_cb(self, event):
        """
        Set overwrite name flag on cb event
        """
        if event is not None:
            event.Skip()
        cb_value = event.GetEventObject()
        self.overwrite_name = cb_value.GetValue()

    def on_click_apply(self, event):
        """
        Changes are saved in data object imported to edit.

        checks firs for valid name, then if it already exists then checks
        that a function was entered and finally that if entered it contains at
        least a return statement.  If all passes writes file then tries to
        compile.  If compile fails or import module fails or run method fails
        tries to remove any .py and pyc files that may have been created and
        sets error message.

        :todo this code still could do with a careful going over to clean
        up and simplify. the non GUI methods such as this one should be removed
        to computational code of SasView. Most of those computational methods
        would be the same for both the simple editors.
        """
        #must post event here
        event.Skip()
        name = self.name_tcl.GetValue().lstrip().rstrip()
        info = 'Info'
        msg = ''
        result, check_err = '', ''
        # Sort out the errors if occur
        # First check for valid python name then if the name already exists
        if not name or not bool(re.match('^[A-Za-z0-9_]*$', name)):
            msg = '"%s" '%name
            msg += "is not a valid model name. Name must not be empty and \n"
            msg += "may include only alpha numeric or underline characters \n"
            msg += "and no spaces"
        elif self.check_name():
            description = self.desc_tcl.GetValue()
            param_str = self.param_tcl.GetText()
            pd_param_str = self.pd_param_tcl.GetText()
            func_str = self.function_tcl.GetText()
            # No input for the model function
            if func_str.lstrip().rstrip():
                if func_str.count('return') > 0:
                    self.write_file(self.fname, name, description, param_str,
                                    pd_param_str, func_str)
                    try:
                        result, msg = check_model(self.fname), None
                    except Exception:
                        import traceback
                        result, msg = None, "error building model"
                        check_err = "\n"+traceback.format_exc(limit=2)
                else:
                    msg = "Error: The func(x) must 'return' a value at least.\n"
                    msg += "For example: \n\nreturn 2*x"
            else:
                msg = 'Error: Function is not defined.'
        else:
            msg = "Name exists already."

        #
        if self.base is not None and not msg:
            self.base.update_custom_combo()

        # Prepare the messagebox
        if msg:
            info = 'Error'
            color = 'red'
            self.overwrite_cb.SetValue(True)
            self.overwrite_name = True
        else:
            self._notes = result
            msg = "Successful! Please look for %s in Plugin Models."%name
            msg += "  " + self._notes
            info = 'Info'
            color = 'blue'
        self._msg_box.SetLabel(msg)
        self._msg_box.SetForegroundColour(color)
        # Send msg to the top window
        if self.base is not None:
            from sas.sasgui.guiframe.events import StatusEvent
            wx.PostEvent(self.base.parent,
                         StatusEvent(status=msg+check_err, info=info))
        self.warning = msg

    def write_file(self, fname, name, desc_str, param_str, pd_param_str, func_str):
        """
        Write content in file

        :param fname: full file path
        :param desc_str: content of the description strings
        :param param_str: content of params; Strings
        :param pd_param_str: content of params requiring polydispersity; Strings
        :param func_str: content of func; Strings
        """
        out_f = open(fname, 'w')

        out_f.write(CUSTOM_TEMPLATE % {
            'name': name,
            'title': 'User model for ' + name,
            'description': desc_str,
            'date': datetime.datetime.now().strftime('%YYYY-%mm-%dd'),
        })

        # Write out parameters
        param_names = []    # to store parameter names
        pd_params = []
        out_f.write('parameters = [ \n')
        out_f.write('#   ["name", "units", default, [lower, upper], "type", "description"],\n')
        for pname, pvalue, desc in self.get_param_helper(param_str):
            param_names.append(pname)
            out_f.write("    ['%s', '', %s, [-inf, inf], '', '%s'],\n"
                        % (pname, pvalue, desc))
        for pname, pvalue, desc in self.get_param_helper(pd_param_str):
            param_names.append(pname)
            pd_params.append(pname)
            out_f.write("    ['%s', '', %s, [-inf, inf], 'volume', '%s'],\n"
                        % (pname, pvalue, desc))
        out_f.write('    ]\n')

        # Write out function definition
        out_f.write('def Iq(%s):\n' % ', '.join(['x'] + param_names))
        out_f.write('    """Absolute scattering"""\n')
        if "scipy." in func_str:
            out_f.write('    import scipy')
        if "numpy." in func_str:
            out_f.write('    import numpy')
        if "np." in func_str:
            out_f.write('    import numpy as np')
        for func_line in func_str.split('\n'):
            out_f.write('%s%s\n' % (spaces4, func_line))
        out_f.write('## uncomment the following if Iq works for vector x\n')
        out_f.write('#Iq.vectorized = True\n')

        # If polydisperse, create place holders for form_volume, ER and VR
        if pd_params:
            out_f.write('\n')
            out_f.write(CUSTOM_TEMPLATE_PD % {'args': ', '.join(pd_params)})

        # Create place holder for Iqxy
        out_f.write('\n')
        out_f.write('#def Iqxy(%s):\n' % ', '.join(["x", "y"] + param_names))
        out_f.write('#    """Absolute scattering of oriented particles."""\n')
        out_f.write('#    ...\n')
        out_f.write('#    return oriented_form(x, y, args)\n')
        out_f.write('## uncomment the following if Iqxy works for vector x, y\n')
        out_f.write('#Iqxy.vectorized = True\n')

        out_f.close()

    def get_param_helper(self, param_str):
        """
        yield a sequence of name, value pairs for the parameters in param_str

        Parameters can be defined by one per line by name=value, or multiple
        on the same line by separating the pairs by semicolon or comma.  The
        value is optional and defaults to "1.0".
        """
        for line in param_str.replace(';', ',').split('\n'):
            for item in line.split(','):
                defn, desc = item.split('#', 1) if '#' in item else (item, '')
                name, value = defn.split('=', 1) if '=' in defn else (defn, '1.0')
                if name:
                    yield [v.strip() for v in (name, value, desc)]

    def set_function_helper(self, line):
        """
        Get string in line to define the local params

        :param line: one line of string got from the param_str
        """
        params_str = ''
        spaces = '        '#8spaces
        items = line.split(";")
        for item in items:
            name = item.split("=")[0].lstrip().rstrip()
            params_str += spaces + "%s = self.params['%s']\n" % (name, name)
        return params_str

    def get_warning(self):
        """
        Get the warning msg
        """
        return self.warning

    def on_help(self, event):
        """
        Bring up the New Plugin Model Editor Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

        :param evt: Triggers on clicking the help button
        """

        _TreeLocation = "user/sasgui/perspectives/fitting/fitting_help.html"
        _PageAnchor = "#new-plugin-model"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, _PageAnchor,
                                          "Plugin Model Editor Help")

    def on_close(self, event):
        """
        leave data as it is and close
        """
        self.parent.Show(False)#Close()
        event.Skip()

class EditorWindow(wx.Frame):
    """
    Editor Window
    """
    def __init__(self, parent, base, path, title,
                 size=(EDITOR_WIDTH, EDITOR_HEIGTH), *args, **kwds):
        """
        Init
        """
        kwds["title"] = title
        kwds["size"] = size
        wx.Frame.__init__(self, parent=None, *args, **kwds)
        self.parent = parent
        self.panel = EditorPanel(parent=self, base=parent,
                                 path=path, title=title)
        self.Show(True)
        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, event):
        """
        On close event
        """
        self.Show(False)
        #if self.parent is not None:
        #    self.parent.new_model_frame = None
        #self.Destroy()

## Templates for plugin models

CUSTOM_TEMPLATE = '''\
r"""
Definition
----------

Calculates %(name)s.

%(description)s

References
----------

Authorship and Verification
---------------------------

* **Author:** --- **Date:** %(date)s
* **Last Modified by:** --- **Date:** %(date)s
* **Last Reviewed by:** --- **Date:** %(date)s
"""

from math import *
from numpy import inf

name = "%(name)s"
title = "%(title)s"
description = """%(description)s"""

'''

CUSTOM_TEMPLATE_PD = '''\
def form_volume(%(args)s):
    """
    Volume of the particles used to compute absolute scattering intensity
    and to weight polydisperse parameter contributions.
    """
    return 0.0

def ER(%(args)s):
    """
    Effective radius of particles to be used when computing structure factors.

    Input parameters are vectors ranging over the mesh of polydispersity values.
    """
    return 0.0

def VR(%(args)s):
    """
    Volume ratio of particles to be used when computing structure factors.

    Input parameters are vectors ranging over the mesh of polydispersity values.
    """
    return 1.0
'''

SUM_TEMPLATE = """
from sasmodels.core import load_model_info
from sasmodels.sasview_model import make_model_from_info

model_info = load_model_info('{model1}{operator}{model2}')
model_info.name = '{name}'{desc_line}
Model = make_model_from_info(model_info)
"""
if __name__ == "__main__":
    main_app = wx.App()
    main_frame = TextDialog(id=1, model_list=["SphereModel", "CylinderModel"],
                            plugin_dir='../fitting/plugin_models')
    main_frame.ShowModal()
    main_app.MainLoop()

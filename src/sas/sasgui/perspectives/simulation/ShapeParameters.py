"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
from __future__ import print_function

import sys
from copy import deepcopy

import wx
import wx.lib.newevent

from . import SimCanvas

(CreateShapeEvent, EVT_ADD_SHAPE) = wx.lib.newevent.NewEvent()
(EditShapeEvent, EVT_EDIT_SHAPE)  = wx.lib.newevent.NewEvent()
(DelShapeEvent, EVT_DEL_SHAPE)    = wx.lib.newevent.NewEvent()
(QRangeEvent, EVT_Q_RANGE)        = wx.lib.newevent.NewEvent() 
(PtDensityEvent, EVT_PT_DENSITY)  = wx.lib.newevent.NewEvent() 

class ShapeParameterPanel(wx.Panel):
    #TODO: show units
    #TODO: order parameters properly
    CENTER_PANE = True
    
    def __init__(self, parent, q_min=0.001, q_max=0.5, q_npts=10, pt_density=0.1, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.window_name = "ShapeParams"
        self.window_caption = "Shape parameter"
        
      
        self.params = {}
        self.parent = parent
        self.type = None
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5,5)
        self.SetSizer(self.bck)
        
        # position and orientation ctrl
        self.xctrl = None
        self.yctrl = None
        self.zctrl = None
        self.actrl = None
        self.bctrl = None
        self.cctrl = None
               
        # Sizer to hold the shape parameters
        self.shape_sizer = wx.GridBagSizer(5,5)
        
        ny = 0       
        title = wx.StaticText(self, -1, "[Temporary form]", style=wx.ALIGN_LEFT)
        self.bck.Add(title, (ny,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        
        # Shape list
        shape_text = wx.StaticText(self, -1, "Geometric shape", style=wx.ALIGN_LEFT)
        self.shape_list = SimCanvas.getShapes()
        value_list = []
        for item in self.shape_list:
            value_list.append(item['name'])
            
        self.model_combo = wx.ComboBox(self, -1, value=value_list[0], choices=value_list, style=wx.CB_READONLY)
        self.model_combo.SetToolTip(wx.ToolTip("Select a geometric shape from the drop-down list"))
        
        ny+=1
        self.bck.Add(shape_text, (ny,0), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        self.bck.Add(self.model_combo, (ny,1), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
        wx.EVT_COMBOBOX(self.model_combo,-1, self._on_select_shape)
   
        # Placeholder for parameter form
        ny+=1
        self.bck.Add(self.shape_sizer, (ny,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=0)   
        
        # Point density control
        point_density_text = wx.StaticText(self, -1, "Point density", style=wx.ALIGN_LEFT)
        ny+=1
        self.bck.Add(point_density_text, (ny,0), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        self.point_density_ctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
        self.point_density_ctrl.SetValue(str(pt_density))
        self.point_density_ctrl.SetToolTip(wx.ToolTip("Enter the number of real-space points per Angstrom cube"))
        self.point_density_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_density_changed)
        self.point_density_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_density_changed)
        self.bck.Add(self.point_density_ctrl, (ny,1), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        
        # Q range
        q_min_text = wx.StaticText(self, -1, "Q min", style=wx.ALIGN_LEFT)
        ny+=1
        self.bck.Add(q_min_text, (ny,0), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        self.q_min_ctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
        self.q_min_ctrl.SetValue(str(q_min))
        self.q_min_ctrl.SetToolTip(wx.ToolTip("Enter the minimum Q value to be simulated"))
        self.q_min_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_q_range_changed)
        self.q_min_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_q_range_changed)
        self.bck.Add(self.q_min_ctrl, (ny,1), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        
        q_max_text = wx.StaticText(self, -1, "Q max", style=wx.ALIGN_LEFT)
        self.bck.Add(q_max_text, (ny,2), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        self.q_max_ctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
        self.q_max_ctrl.SetValue(str(q_max))
        self.q_min_ctrl.SetToolTip(wx.ToolTip("Enter the maximum Q value to be simulated"))
        self.q_max_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_q_range_changed)
        self.q_max_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_q_range_changed)
        self.bck.Add(self.q_max_ctrl, (ny,3), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        
        q_npts_text = wx.StaticText(self, -1, "No. of Q pts", style=wx.ALIGN_LEFT)
        self.bck.Add(q_npts_text, (ny,4), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        self.q_npts_ctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
        self.q_npts_ctrl.SetValue(str(q_npts))
        self.q_min_ctrl.SetToolTip(wx.ToolTip("Enter the number of Q points to be simulated"))
        self.q_npts_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_q_range_changed)
        self.q_npts_ctrl.Bind(wx.EVT_KILL_FOCUS, self._on_q_range_changed)
        self.bck.Add(self.q_npts_ctrl, (ny,5), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        
        # Shape List
        # Internal counter of shapes in the listbox
        self.counter = 0
        # Buffer filled flag
        self.buffer_filled = False
        # Save current flag
        self.current_saved = False       
         
        id = wx.NewId()
        shape_listbox_text = wx.StaticText(self, -1, "List of shapes on 3D canvas", style=wx.ALIGN_LEFT)
        self.shape_listbox = wx.ListBox(self, id, wx.DefaultPosition, (295, 200), 
                                   [], wx.LB_SINGLE | wx.LB_HSCROLL)
        
        # Listen to history events
        self.parent.Bind(EVT_ADD_SHAPE, self._on_add_shape_to_listbox)
        self.shape_listbox.Bind(wx.EVT_LISTBOX, self._on_select_from_listbox, id=id)
        self.shape_listbox.Bind(wx.EVT_CONTEXT_MENU, self._on_listbox_context_menu, id=id)
        
        ny+=1
        self.bck.Add(shape_listbox_text, (ny,0), (1,2), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        ny+=1
        self.bck.Add(self.shape_listbox, (ny,0), (1,5), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
        
        self.current_shape = None
        
        # Default shape
        if type(self.shape_list)==list and len(self.shape_list)>0:
            shape = SimCanvas.getShapeClassByName(self.shape_list[0]['name'])()
            self.editShape(shape)                        

    def _on_select_shape(self, event):
        shape = SimCanvas.getShapeClassByName(self.shape_list[event.GetEventObject().GetSelection()]['name'])()
        self.editShape(shape)    

    def _on_density_changed(self, event):
        """
            Process event that might mean a change of the simulation point density
        """
        npts  = self._readCtrlFloat(self.point_density_ctrl)
        if npts is not None:
            event = PtDensityEvent(npts=npts)
            wx.PostEvent(self.parent, event)
            
    def _on_q_range_changed(self, event):
        """
            Process event that might mean a change in Q range
            @param event: EVT_Q_RANGE event
        """
        q_min = self._readCtrlFloat(self.q_min_ctrl)
        q_max = self._readCtrlFloat(self.q_max_ctrl)
        npts  = self._readCtrlInt(self.q_npts_ctrl)
        if q_min is not None or q_max is not None or npts is not None:
            event = QRangeEvent(q_min=q_min, q_max=q_max, npts=npts)
            wx.PostEvent(self.parent, event)
            
    def _onEditShape(self, evt):
        """
            Process an EVT_EDIT_SHAPE event 
            @param evt: EVT_EDIT_SHAPE object
        """
        evt.Skip()
        self.editShape(evt.shape, False)
        
    def editShape(self, shape=None, new=True):
        """
            Rebuild the panel
        """
        self.current_shape = shape
        self.shape_sizer.Clear(True)  
        #self.type = type  
        
        if shape==None:
            title = wx.StaticText(self, -1, "Use menu to add a shapes", style=wx.ALIGN_LEFT)
            self.shape_sizer.Add(title, (0,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)

        else:
            if new==False:
                title = wx.StaticText(self, -1, "Edit shape parameters", style=wx.ALIGN_LEFT)
            else:
                title = wx.StaticText(self, -1, "Create shape from parameters", style=wx.ALIGN_LEFT)
                
            self.shape_sizer.Add(title, (0,0), (1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=15)
            
            n = 1
            self.parameters = []
            
            for item in sorted(shape.params.keys()):
                if item in ['contrast', 'order']:
                    continue
                n += 1
                text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                self.shape_sizer.Add(text, (n-1,0), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
                ctl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
                
                
                ctl.SetValue(str(shape.params[item]))
                self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
                ctl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
                self.parameters.append([item, ctl])
                self.shape_sizer.Add(ctl, (n-1,1), flag=wx.TOP|wx.BOTTOM, border = 0)
                
                # Units
                units = wx.StaticText(self, -1, shape.details[item], style=wx.ALIGN_LEFT)
                self.shape_sizer.Add(units, (n-1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)

            for item in ['contrast', 'order']:
                n += 1
                text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                self.shape_sizer.Add(text, (n-1,0), flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
                ctl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
                
                
                ctl.SetValue(str(shape.params[item]))
                self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
                ctl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
                self.parameters.append([item, ctl])
                self.shape_sizer.Add(ctl, (n-1,1), flag=wx.TOP|wx.BOTTOM, border = 0)
                
                # Units
                units = wx.StaticText(self, -1, shape.details[item], style=wx.ALIGN_LEFT)
                self.shape_sizer.Add(units, (n-1,2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border = 15)
                
                
            # Add position
            n += 1
            
            pos_sizer = wx.GridBagSizer(0,0)
            
            text = wx.StaticText(self, -1, 'x', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,0), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            text = wx.StaticText(self, -1, 'y', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,1), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            text = wx.StaticText(self, -1, 'z', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,2), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            
            self.xctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.xctrl.SetValue(str(shape.x))
            self.xctrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.xctrl, (1,0), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            self.yctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.yctrl.SetValue(str(shape.y))
            self.yctrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.yctrl, (1,1), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            self.zctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.zctrl.SetValue(str(shape.z))
            self.zctrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.zctrl, (1,2), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            
            self.shape_sizer.Add(pos_sizer, (n-1, 0), (1,3), flag=wx.LEFT|wx.ALIGN_CENTER)
            
            # Add orientation
            n += 1
            
            pos_sizer = wx.GridBagSizer(0,0)
            
            text = wx.StaticText(self, -1, 'theta_x', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,0), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            text = wx.StaticText(self, -1, 'theta_y', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,1), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            text = wx.StaticText(self, -1, 'theta_z', style=wx.ALIGN_LEFT)
            pos_sizer.Add(text, (0,2), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            
            self.actrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.actrl.SetValue(str(shape.theta_x))
            self.actrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.actrl, (1,0), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            self.bctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.bctrl.SetValue(str(shape.theta_y))
            self.bctrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.bctrl, (1,1), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            self.cctrl = wx.TextCtrl(self, -1, size=(40,20), style=wx.TE_PROCESS_ENTER)
            self.cctrl.SetValue(str(shape.theta_z))
            self.cctrl.Bind(wx.EVT_KILL_FOCUS, self.onTextEnter)
            pos_sizer.Add(self.cctrl, (1,2), (1,1), flag = wx.LEFT|wx.ALIGN_CENTER, border = 15)
            
            self.shape_sizer.Add(pos_sizer, (n-1, 0), (1,3), flag=wx.LEFT|wx.ALIGN_CENTER)
            
            
            # Add a button to create the new shape on the canvas
            n += 1
            if new==True:
                create = wx.Button(self, 1,"Create")
                self.shape_sizer.Add(create, (n-1,1), (1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border = 15)
                self.Bind(wx.EVT_BUTTON, self._onCreate, id = 1)        
            else:
                create = wx.Button(self, 1,"Apply")
                self.shape_sizer.Add(create, (n-1,1), (1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border = 15)
                self.Bind(wx.EVT_BUTTON, self._onEdited, id = 1)        
                


        self.shape_sizer.Layout()
        self.shape_sizer.Fit(self)
        try:
            self.parent.GetSizer().Layout()
        except:
            print("TODO: move the Layout call of editShape up to the caller")

    def _readCtrlFloat(self, ctrl):
        """
            Parses a TextCtrl for a float value.
            Returns None is the value hasn't changed or the value is not a float.
            The control background turns pink if the value is not a float.
            
            @param ctrl: TextCtrl object
        """
        if ctrl.IsModified():
            ctrl.SetModified(False)
            str_value = ctrl.GetValue().lstrip().rstrip()
            try:
                flt_value = float(str_value)
                ctrl.SetBackgroundColour(
                        wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                ctrl.Refresh()
                return flt_value
            except:
                ctrl.SetBackgroundColour("pink")
                ctrl.Refresh()
        return None

    def _readCtrlInt(self, ctrl):
        """
            Parses a TextCtrl for a float value.
            Returns None is the value hasn't changed or the value is not a float.
            The control background turns pink if the value is not a float.
            
            @param ctrl: TextCtrl object
        """
        if ctrl.IsModified():
            ctrl.SetModified(False)
            str_value = ctrl.GetValue().lstrip().rstrip()
            try:
                int_value = int(str_value)
                ctrl.SetBackgroundColour(
                        wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                ctrl.Refresh()
                return int_value
            except:
                ctrl.SetBackgroundColour("pink")
                ctrl.Refresh()
        return None

    def _parseCtrl(self):
        try:
            # Position
            tmp = self._readCtrlFloat(self.xctrl)
            if not tmp==None:
                self.current_shape.x = tmp
                
            tmp = self._readCtrlFloat(self.yctrl)
            if not tmp==None:
                self.current_shape.y = tmp
                
            tmp = self._readCtrlFloat(self.zctrl)
            if not tmp==None:
                self.current_shape.z = tmp
                
            # Orientation
            tmp = self._readCtrlFloat(self.actrl)
            if not tmp==None:
                self.current_shape.theta_x = tmp
                
            tmp = self._readCtrlFloat(self.bctrl)
            if not tmp==None:
                self.current_shape.theta_y = tmp
                
            tmp = self._readCtrlFloat(self.cctrl)
            if not tmp==None:
                self.current_shape.theta_z = tmp
                
            # Parameters
            for item in self.parameters:
                tmp = self._readCtrlFloat(item[1])
                if not tmp==None:
                    self.current_shape.params[item[0]] = tmp 
        except Exception as exc:
            print("Could not create")
            print(exc)
                
    def _onCreate(self, evt):
        """
            Create a new shape with the parameters given by the user
        """
        self._parseCtrl()
        event = CreateShapeEvent(shape=self.current_shape, new=True)
        wx.PostEvent(self.parent, event)
        self.editShape(self.current_shape, False)
            
        
    def _onEdited(self, evt):
        self._parseCtrl()
        event = CreateShapeEvent(shape=self.current_shape, new=False)
        wx.PostEvent(self.parent, event)
        self.editShape(self.current_shape, False)

    def onTextEnter(self, evt): 
        """
            Read text field to check values
        """ 
        self._readCtrlFloat(self.xctrl)
        self._readCtrlFloat(self.yctrl)
        self._readCtrlFloat(self.zctrl)
        self._readCtrlFloat(self.actrl)
        self._readCtrlFloat(self.bctrl)
        self._readCtrlFloat(self.cctrl)
        for item in self.parameters:
            self._readCtrlFloat(item[1])
 
    #-- Methods to support list of shapes --
    def _on_add_shape_to_listbox(self, event):
        """
            Process a new shape            
            @param event: EVT_ADD_SHAPE event
        """
        event.Skip()
        if event.new:
            self.counter += 1
            self.shape_listbox.Insert("%d: %s" % (self.counter, event.shape.name), 
                                 self.shape_listbox.GetCount(), event.shape)

    def _on_select_from_listbox(self, event):
        """
            Process item selection events
        """
        index = event.GetSelection()
        view_name = self.shape_listbox.GetString(index)
        self.editShape(shape=event.GetClientData(), new=False)
        # The following event is bound to the SimPanel to highlight the shape in blue
        #TODO: how come it doesn't work? 
        wx.PostEvent(self.parent, EditShapeEvent(shape=event.GetClientData()))
        #TODO: select the shape from the drop down
        
    def _on_listbox_context_menu(self, event):
        """
            Popup context menu event
        """
        # Create context menu
        popupmenu = wx.Menu()
        
        # Create an item to delete the selected shape from the canvas
        id = wx.NewId()
        popupmenu.Append(id, "&Remove Selected")
        wx.EVT_MENU(self, id, self._on_remove_shape_from_listbox)
        
        # Create an item to rename a shape to a more user friendly name
        #id = wx.NewId()
        #popupmenu.Append(102, "&Rename Selected")
        #wx.EVT_MENU(self, 102, self.onRename)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(popupmenu, pos)        
        
    def _on_remove_shape_from_listbox(self, ev):
        """
            Remove an item
        """
        indices = self.shape_listbox.GetSelections()
        if len(indices)>0:
            name =  self.shape_listbox.GetClientData(indices[0]).name
            self.shape_listbox.Delete(indices[0])
            wx.PostEvent(self.parent, DelShapeEvent(id = name))
        
    def _on_rename_shape_from_listbox(self, ev):
        """
            Rename an item
        """
        indices = self.shape_listbox.GetSelections()
        if len(indices)>0:
            print("NOT YET IMPLMENTED")
            print("renaming", self.shape_listbox.GetString(indices[0]))

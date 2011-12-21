
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
from wx.lib.scrolledpanel import ScrolledPanel

#TextDialog size
if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
    PNL_WIDTH = 460
    PNL_HITE = 210
else:
    FONT_VARIANT = 1
    PNL_WIDTH = 500
    PNL_HITE = 250

MAX_NBR_DATA = 4
WIDTH = 430
HEIGHT = 350

class DialogPanel(ScrolledPanel):
    def __init__(self, *args, **kwds):
        ScrolledPanel.__init__(self, *args, **kwds)
        self.SetupScrolling()
        
class BatchDataDialog(wx.Dialog):
    """
    The current design of Batch  fit allows only of type of data in the data
    set. This allows the user to make a quick selection of the type of data
    to use in fit tab.
    """
    def __init__(self, parent=None,  *args, **kwds):
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetSize((WIDTH, HEIGHT))
        self.data_1d_selected = None
        self.data_2d_selected = None
        self._do_layout()
   
    def _do_layout(self):
        """
        Draw the content of the current dialog window
        """
        vbox = wx.BoxSizer(wx.VERTICAL)
        box_description= wx.StaticBox(self, -1,str("Hint"))
        hint_sizer = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        selection_sizer = wx.GridBagSizer(5,5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.data_1d_selected = wx.RadioButton(self, -1, 'Data1D',
                                                style=wx.RB_GROUP)
        self.data_2d_selected  = wx.RadioButton(self, -1, 'Data2D')
        self.data_1d_selected.SetValue(True)
        self.data_2d_selected.SetValue(False)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        hint = "Selected Data set contains both 1D and 2D Data.\n"
        hint += "Please select on type of analysis before proceeding.\n"
        hint_sizer.Add(wx.StaticText(self, -1, hint))
        #draw area containing radio buttons
        ix = 0
        iy = 0
        selection_sizer.Add(self.data_1d_selected, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        selection_sizer.Add(self.data_2d_selected, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        #contruction the sizer contaning button
        button_sizer.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        button_sizer.Add(button_cancel, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        button_sizer.Add(button_OK, 0,
                                wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        vbox.Add(hint_sizer,  0, wx.EXPAND|wx.ALL, 10)
        vbox.Add(selection_sizer, 0, wx.TOP|wx.BOTTOM, 10)
        vbox.Add(wx.StaticLine(self, -1),  0, wx.EXPAND, 0)
        vbox.Add(button_sizer, 0 , wx.TOP|wx.BOTTOM, 10)
        self.SetSizer(vbox)
        self.Layout()
        
    def get_data(self):
        """
        return 1 if  user requested Data1D , 2 if user requested Data2D
        """
        if self.data_1d_selected.GetValue():
            return 1
        else:
            return 2



class DataDialog(wx.Dialog):
    """
    Allow file selection at loading time
    """
    def __init__(self, data_list, parent=None, text='',
                 nb_data=MAX_NBR_DATA, *args, **kwds):
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetTitle("Data Selection")
        self._max_data = nb_data
        self._nb_selected_data = nb_data
        
        self.SetSize((WIDTH, HEIGHT))
        self.list_of_ctrl = []
        if not data_list:
            return 
        select_data_text = " %s Data selected.\n" % str(self._nb_selected_data)
        self._data_text_ctrl = wx.StaticText(self, -1, str(select_data_text))
                               
        self._data_text_ctrl.SetForegroundColour('blue')
        self._sizer_main = wx.BoxSizer(wx.VERTICAL)
        self._sizer_txt = wx.BoxSizer(wx.VERTICAL)
        self._sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self._choice_sizer = wx.GridBagSizer(5, 5)
        self._panel = DialogPanel(self, style=wx.RAISED_BORDER,
                               size=(WIDTH-20, HEIGHT/3))
        self.__do_layout(data_list, text=text)
        
    def __do_layout(self, data_list, text=''):
        """
        layout the dialog
        """
        if not data_list or len(data_list) <= 1:
            return 
        #add text
        if text.strip() == "":
            text = "Fitting: We recommend that you selected"
            text += " no more than '%s' data\n" % str(self._max_data)
            text += "for adequate plot display size. \n" 
            text += "unchecked data won't be send to fitting . \n" 
        text_ctrl = wx.StaticText(self, -1, str(text))
        self._sizer_txt.Add(text_ctrl)
        iy = 0
        ix = 0
        data_count = 0
        for i in range(len(data_list)):
            data_count += 1
            cb = wx.CheckBox(self._panel, -1, str(data_list[i].name), (10, 10))
            wx.EVT_CHECKBOX(self, cb.GetId(), self._count_selected_data)
            if data_count <= MAX_NBR_DATA:
                cb.SetValue(True)
            else:
                cb.SetValue(False)
            self.list_of_ctrl.append((cb, data_list[i]))
            self._choice_sizer.Add(cb, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            iy += 1
        self._panel.SetSizer(self._choice_sizer)
        #add sizer
        self._sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._sizer_button.Add(button_cancel, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        self._sizer_button.Add(button_OK, 0,
                                wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        static_line = wx.StaticLine(self, -1)
        self._sizer_txt.Add(self._panel, 0, wx.EXPAND|wx.ALL, 10)
        self._sizer_main.Add(self._sizer_txt, 0, wx.EXPAND|wx.ALL, 10)
        self._sizer_main.Add(self._data_text_ctrl, 0,  wx.EXPAND|wx.ALL, 10)
        self._sizer_main.Add(static_line, 0, wx.EXPAND, 0)
        self._sizer_main.Add(self._sizer_button, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self._sizer_main)
        self.Layout()
        
    def get_data(self):
        """
        return the selected data
        """
        temp = []
        for item in self.list_of_ctrl:
            cb, data = item
            if cb.GetValue():
                temp.append(data)
        return temp
    
    def _count_selected_data(self, event):
        """
        count selected data
        """
        if event.GetEventObject().GetValue():
            self._nb_selected_data += 1
        else:
            self._nb_selected_data -= 1
        select_data_text = " %s Data selected.\n" % str(self._nb_selected_data)
        self._data_text_ctrl.SetLabel(select_data_text)
        if self._nb_selected_data <= self._max_data:
            self._data_text_ctrl.SetForegroundColour('blue')
        else:
            self._data_text_ctrl.SetForegroundColour('red')
        
 
class TextDialog(wx.Dialog):
    """
    Dialog for easy custom sum models  
    """
    def __init__(self, parent=None, id=None, title='', model_list=[]):
        """
        Dialog window popup when selecting 'Easy Custom Sum' on the menu
        """
        wx.Dialog.__init__(self, parent=parent, id=id, 
                           title=title, size=(PNL_WIDTH, PNL_HITE))
        self.parent = parent
        #Font
        self.SetWindowVariant(variant=FONT_VARIANT)
        # default
        self.model_list = model_list
        self.model1_string = "SphereModel"
        self.model2_string = "CylinderModel"
        self._build_sizer()
        self.model1_name = str(self.model1.GetValue())
        self.model2_name = str(self.model2.GetValue())
        
    def _build_sizer(self):
        """
        Build gui
        """
        _BOX_WIDTH = 195 # combobox width
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(1, 3)
        sum_description= wx.StaticBox(self, -1, 'Select', 
                                       size=(PNL_WIDTH-30, 70))
        sum_box = wx.StaticBoxSizer(sum_description, wx.VERTICAL)
        model1_box = wx.BoxSizer(wx.HORIZONTAL)
        model2_box = wx.BoxSizer(wx.HORIZONTAL)
        model_vbox = wx.BoxSizer(wx.VERTICAL)
        self.model1 =  wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.model1, -1, self.on_model1)
        self.model1.SetMinSize((_BOX_WIDTH, -1))
        self.model1.SetToolTipString("model1")
        self.model2 =  wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.model2, -1, self.on_model2)
        self.model2.SetMinSize((_BOX_WIDTH, -1))
        self.model2.SetToolTipString("model2")
        self._set_model_list()
        
         # Buttons on the bottom
        self.static_line_1 = wx.StaticLine(self, -1)
        self.okButton = wx.Button(self,wx.ID_OK, 'OK', size=(_BOX_WIDTH/2, 25))
        self.closeButton = wx.Button(self,wx.ID_CANCEL, 'Cancel', 
                                     size=(_BOX_WIDTH/2, 25))
        # Intro
        explanation  = "  custom model = scale_factor * (model1 + model2)\n"
        model_string = " Model%s (p%s):"
        vbox.Add(sizer)
        ix = 0
        iy = 1
        sizer.Add(wx.StaticText(self, -1, explanation), (iy, ix),
                 (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        model1_box.Add(wx.StaticText(self,-1, model_string% (1, 1)), -1, 0)
        model1_box.Add((_BOX_WIDTH-35,10))
        model1_box.Add(wx.StaticText(self, -1, model_string% (2, 2)), -1, 0)
        model2_box.Add(self.model1, -1, 0)
        model2_box.Add((20,10))
        model2_box.Add(self.model2, -1, 0)
        model_vbox.Add(model1_box, -1, 0)
        model_vbox.Add(model2_box, -1, 0)
        sum_box.Add(model_vbox, -1, 10)
        iy += 1
        ix = 0
        sizer.Add(sum_box, (iy, ix),
                  (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        vbox.Add((10,10))
        vbox.Add(self.static_line_1, 0, wx.EXPAND, 10)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.okButton, 0, 
                         wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.closeButton, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 15)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.SetSizer(vbox)
        self.Centre()
                 
    def _set_model_list(self):
        """
        Set the list of models
        """
        # list of model names
        list = self.model_list
        if len(list) > 1:
            list.sort()
        for idx in range(len(list)):
            self.model1.Append(list[idx],idx) 
            self.model2.Append(list[idx],idx)
        self.model1.SetStringSelection(self.model1_string)
        self.model2.SetStringSelection(self.model2_string)
           
    def on_model1(self, event):
        """
        Set model1
        """
        event.Skip()
        self.model1_name = str(self.model1.GetValue())
        self.model1_string = self.model1_name
            
    def on_model2(self, event):
        """
        Set model2
        """
        event.Skip()
        self.model2_name = str(self.model2.GetValue())
        self.model2_string = self.model2_name
 
    def getText(self):
        """
        Returns model name string as list
        """
        return [self.model1_name, self.model2_name]
    
    def write_string(self, fname, name1, name2):
        """
        Write and Save file
        """
        try:
            out_f =  open(fname,'w')
        except :
            raise
        lines = SUM_TEMPLATE.split('\n')
        for line in lines:
            if line.count("import %s as P1"):
                out_f.write(line % (name1, name1) + "\n")
            elif line.count("import %s as P2"):
                out_f.write(line % (name2, name2) + "\n")
            else:
                out_f.write(line + "\n")
        out_f.close() 
        
    def compile_file(self, path):
        """
        Compile the file in the path
        """
        try:
            import py_compile
            py_compile.compile(file=path, doraise=True)
        except:
            type, value, traceback = sys.exc_info()
            return value
        
    def delete_file(self, path):
        """
        Delete file in the path
        """
        try:
            os.remove(path)
        except:
            raise
        
        
SUM_TEMPLATE = """
# A sample of an experimental model function for Sum(Pmodel1,Pmodel2)
import copy
from sans.models.pluginmodel import Model1DPlugin
# User can change the name of the model (only with single functional model)
#P1_model: 
from sans.models.%s import %s as P1

#P2_model: 
from sans.models.%s import %s as P2

class Model(Model1DPlugin):
    name = ""
    def __init__(self):
        Model1DPlugin.__init__(self, name='')
        p_model1 = P1()
        p_model2 = P2()
        ## Setting  model name model description
        self.description=""
        self.name = self._get_name(p_model1.name, p_model2.name)
        self.description = p_model1.name
        self.description += p_model2.name
        self.fill_description(p_model1, p_model2)

        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        
        # non-fittable parameters
        self.non_fittable = p_model1.non_fittable  
        self.non_fittable += p_model2.non_fittable  
            
        ##models 
        self.p_model1= p_model1
        self.p_model2= p_model2
        
       
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## New parameter:Scaling factor
        self.params['scale_factor'] = 1
        
        ## Parameter details [units, min, max]
        self._set_details()
        self.details['scale_factor'] = ['', None, None]

        
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.p_model1.orientation_params:
            new_item = "p1_" + item
            if not new_item in self.orientation_params:
                self.orientation_params.append(new_item)
            
        for item in self.p_model2.orientation_params:
            new_item = "p2_" + item
            if not new_item in self.orientation_params:
                self.orientation_params.append(new_item)
        # get multiplicity if model provide it, else 1.
        try:
            multiplicity1 = p_model1.multiplicity
            try:
                multiplicity2 = p_model2.multiplicity
            except:
                multiplicity2 = 1
        except:
            multiplicity1 = 1
            multiplicity2 = 1
        ## functional multiplicity of the model
        self.multiplicity1 = multiplicity1  
        self.multiplicity2 = multiplicity2    
        self.multiplicity_info = []   
        
    def _clone(self, obj):
        obj.params     = copy.deepcopy(self.params)
        obj.description     = copy.deepcopy(self.description)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.p_model1  = self.p_model1.clone()
        obj.p_model2  = self.p_model2.clone()
        #obj = copy.deepcopy(self)
        return obj
    
    def _get_name(self, name1, name2):
        name = self._get_upper_name(name1)
        name += "+"
        name += self._get_upper_name(name2)
        return name
    
    def _get_upper_name(self, name=None):
        if name == None:
            return ""
        upper_name = ""
        str_name = str(name)
        for index in range(len(str_name)):
            if str_name[index].isupper():
                upper_name += str_name[index]
        return upper_name
        
    def _set_dispersion(self):
        ##set dispersion only from p_model 
        for name , value in self.p_model1.dispersion.iteritems():
            #if name.lower() not in self.p_model1.orientation_params:
            new_name = "p1_" + name
            self.dispersion[new_name]= value 
        for name , value in self.p_model2.dispersion.iteritems():
            #if name.lower() not in self.p_model2.orientation_params:
            new_name = "p2_" + name
            self.dispersion[new_name]= value 
            
    def function(self, x=0.0): 
        return 0
                               
    def getProfile(self):
        try:
            x,y = self.p_model1.getProfile()
        except:
            x = None
            y = None
            
        return x, y
    
    def _set_params(self):
        for name , value in self.p_model1.params.iteritems():
            # No 2D-supported
            #if name not in self.p_model1.orientation_params:
            new_name = "p1_" + name
            self.params[new_name]= value
            
        for name , value in self.p_model2.params.iteritems():
            # No 2D-supported
            #if name not in self.p_model2.orientation_params:
            new_name = "p2_" + name
            self.params[new_name]= value
                
        # Set "scale" as initializing
        self._set_scale_factor()
      
            
    def _set_details(self):
        for name ,detail in self.p_model1.details.iteritems():
            new_name = "p1_" + name
            #if new_name not in self.orientation_params:
            self.details[new_name]= detail
            
        for name ,detail in self.p_model2.details.iteritems():
            new_name = "p2_" + name
            #if new_name not in self.orientation_params:
            self.details[new_name]= detail
    
    def _set_scale_factor(self):
        pass
        
                
    def setParam(self, name, value):
        # set param to p1+p2 model
        self._setParamHelper(name, value)
        
        ## setParam to p model 
        model_pre = name.split('_', 1)[0]
        new_name = name.split('_', 1)[1]
        if model_pre == "p1":
            if new_name in self.p_model1.getParamList():
                self.p_model1.setParam(new_name, value)
        elif model_pre == "p2":
             if new_name in self.p_model2.getParamList():
                self.p_model2.setParam(new_name, value)
        elif name.lower() == 'scale_factor':
            self.params['scale_factor'] = value
        else:
            raise ValueError, "Model does not contain parameter %s" % name
            
    def getParam(self, name):
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                # 2D not supported
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            return self.dispersion[item][par]
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():
                    return self.params[item]
        return  
        #raise ValueError, "Model does not contain parameter %s" % name
       
    def _setParamHelper(self, name, value):
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)== 2:
            for item in self.dispersion.keys():
                if item.lower()== toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            self.dispersion[item][par] = value
                            return
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()== name.lower():
                    self.params[item] = value
                    return
            
        raise ValueError, "Model does not contain parameter %s" % name
             
   
    def _set_fixed_params(self):
        for item in self.p_model1.fixed:
            new_item = "p1" + item
            self.fixed.append(new_item)
        for item in self.p_model2.fixed:
            new_item = "p2" + item
            self.fixed.append(new_item)

        self.fixed.sort()
                
                    
    def run(self, x = 0.0):
        self._set_scale_factor()
        return self.params['scale_factor'] * \
(self.p_model1.run(x) + self.p_model2.run(x))
    
    def runXY(self, x = 0.0):
        self._set_scale_factor()
        return self.params['scale_factor'] * \
(self.p_model1.runXY(x) + self.p_model2.runXY(x))
    
    ## Now (May27,10) directly uses the model eval function 
    ## instead of the for-loop in Base Component.
    def evalDistribution(self, x = []):
        self._set_scale_factor()
        return self.params['scale_factor'] * \
(self.p_model1.evalDistribution(x) + \
self.p_model2.evalDistribution(x))

    def set_dispersion(self, parameter, dispersion):
        value= None
        new_pre = parameter.split("_", 1)[0]
        new_parameter = parameter.split("_", 1)[1]
        try:
            if new_pre == 'p1' and \
new_parameter in self.p_model1.dispersion.keys():
                value= self.p_model1.set_dispersion(new_parameter, dispersion)
            if new_pre == 'p2' and \
new_parameter in self.p_model2.dispersion.keys():
                value= self.p_model2.set_dispersion(new_parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 

    def fill_description(self, p_model1, p_model2):
        description = ""
        description +="This model gives the summation of  %s and %s. "% \
( p_model1.name, p_model2.name )
        self.description += description
        
if __name__ == "__main__": 
    m1= Model() 
    #m1.setParam("p1_scale", 25)  
    #m1.setParam("p1_length", 1000)
    #m1.setParam("p2_scale", 100) 
    #m1.setParam("p2_rg", 100) 
    out1 = m1.runXY(0.01)

    m2= Model()
    #m2.p_model1.setParam("scale", 25) 
    #m2.p_model1.setParam("length", 1000) 
    #m2.p_model2.setParam("scale", 100)
    #m2.p_model2.setParam("rg", 100)
    out2 = m2.p_model1.runXY(0.01) + m2.p_model2.runXY(0.01)
    print out1, " = ", out2
    if out1 == out2:
        print "===> Simple Test: Passed!"
    else:
        print "===> Simple Test: Failed!"
"""
        
if __name__ == "__main__": 
    app = wx.PySimpleApp()
    frame = TextDialog(id=1, model_list=["SphereModel", "CylinderModel"])   
    frame.Show(True)
    app.MainLoop()             

          
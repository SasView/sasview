"""
Calculator Module
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################

import wx
from sans.guiframe.plugin_base import PluginBase
from sans.perspectives.calculator.data_operator import DataOperatorWindow
from sans.perspectives.calculator.data_editor import DataEditorWindow
from sans.perspectives.calculator.kiessig_calculator_panel import KiessigWindow
from sans.perspectives.calculator.sld_panel import SldWindow
from sans.perspectives.calculator.density_panel import DensityWindow
from sans.perspectives.calculator.slit_length_calculator_panel \
            import SlitLengthCalculatorWindow
from sans.perspectives.calculator.resolution_calculator_panel \
            import ResolutionWindow
from sans.perspectives.calculator.gen_scatter_panel import SasGenWindow
from sans.perspectives.calculator.image_viewer import ImageView
from sans.perspectives.calculator.pyconsole import PyConsole
import logging

class Plugin(PluginBase):
    """
    This class defines the interface for a Plugin class
    for calculator perspective
    """
    def __init__(self, standalone=True):
        PluginBase.__init__(self, name="Calculator", standalone=standalone)
        # Log startup
        logging.info("Calculator plug-in started")   
        self.sub_menu = "Tool" 
        self.data_edit_frame = None
        # data operator use one frame all the time
        self.data_operator_frame = None
        self.kiessig_frame = None
        self.sld_frame = None
        self.cal_md_frame = None
        self.cal_slit_frame = None
        self.cal_res_frame = None
        self.gen_frame = None
        self.image_view = None
        self.py_frame = None
        
        
    def help(self, evt):
        """
        Show a general help dialog. 
        
        :TODO: replace the text with a nice image
            provide more hint on the SLD calculator
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1) 
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass  
        frame.Show(True)

    def get_tools(self):
        """
        Returns a set of menu entries for tools
        """
        data_oper_help = "Perform arithmetic data operation (+...) "
        data_oper_help += "and combination (|)"
        kiessig_help = "Approximately computes the "
        kiessig_help += "thickness of a shell or the size of "
        kiessig_help += "particles \n from the width of a Kiessig fringe."
        sld_help = "Computes the Scattering Length Density."
        slit_length_help = "Computes the slit length from the beam profile."
        resolution_help = "Approximately estimates the "
        resolution_help += "resolution of Q in 2D based on the SANS "
        resolution_help += "instrumental parameter values."
        mass_volume_help = "Based on the chemical formula, "
        mass_volume_help += "compute the mass density or the molar volume."
        gensans_help = "Generic SANS"
        pyconsole_help = "Python Console."
        imageviewer_help = "Load an image file and display the image."
        #data_editor_help = "Meta Data Editor"
        return [("Data Operation", 
                        data_oper_help, self.on_data_operation),
                ("SLD Calculator", sld_help, self.on_calculate_sld),
                ("Density/Volume Calculator", mass_volume_help, 
                                            self.on_calculate_dv),
                ("Slit Size Calculator", slit_length_help,
                        self.on_calculate_slit_size),
                ("Kiessig Thickness Calculator", 
                        kiessig_help, self.on_calculate_kiessig),
                          ("SANS Resolution Estimator", 
                        resolution_help, self.on_calculate_resoltuion),
                ("Generic Scattering Calculator", 
                        gensans_help, self.on_gen_model),
                ("Python Shell/Editor", pyconsole_help, self.on_python_console),
                ("Image Viewer", imageviewer_help, self.on_image_viewer),]
              
    def on_edit_data(self, event):
        """
        Edit meta data 
        """
        if self.data_edit_frame == None:
            self.data_edit_frame = DataEditorWindow(parent=self.parent, 
                                                    manager=self, data=[],
                                                    title="Data Editor")
            self.put_icon(self.data_edit_frame)
        self.data_edit_frame.Show(False)    
        self.data_edit_frame.Show(True)
              
    def on_data_operation(self, event):
        """
        Data operation
        """
        if self.data_operator_frame == None:
            # Use one frame all the time
            self.data_operator_frame = DataOperatorWindow(parent=self.parent, 
                                                manager=self, 
                                                title="Data Operation")
            self.put_icon(self.data_operator_frame)
        self.data_operator_frame.Show(False)
        self.data_operator_frame.panel.set_panel_on_focus(None)
        self.data_operator_frame.Show(True)
        
    def on_calculate_kiessig(self, event):
        """
        Compute the Kiessig thickness
        """
        if self.kiessig_frame == None:
            frame = KiessigWindow(parent=self.parent, manager=self)
            self.put_icon(frame)
            self.kiessig_frame = frame
        self.kiessig_frame.Show(False)
        self.kiessig_frame.Show(True) 
        
    def on_calculate_sld(self, event):
        """
        Compute the scattering length density of molecula
        """
        if self.sld_frame == None:
            frame = SldWindow(base=self.parent, manager=self)
            self.put_icon(frame)
            self.sld_frame = frame
        self.sld_frame.Show(False)
        self.sld_frame.Show(True) 
    
    def on_calculate_dv(self, event):
        """
        Compute the mass density or molar voulme
        """
        if self.cal_md_frame == None:
            frame = DensityWindow(base=self.parent, manager=self)
            self.put_icon(frame)
            self.cal_md_frame = frame
        self.cal_md_frame.Show(False)
        self.cal_md_frame.Show(True) 
              
    def on_calculate_slit_size(self, event):
        """
        Compute the slit size a given data
        """
        if self.cal_slit_frame == None:
            frame = SlitLengthCalculatorWindow(parent=self.parent, manager=self)  
            self.put_icon(frame)
            self.cal_slit_frame = frame 
        self.cal_slit_frame.Show(False)     
        self.cal_slit_frame.Show(True)
        
    def on_calculate_resoltuion(self, event):
        """
        Estimate the instrumental resolution
        """
        if self.cal_res_frame == None:
            frame = ResolutionWindow(parent=self.parent, manager=self)
            self.put_icon(frame)
            self.cal_res_frame = frame
        self.cal_res_frame.Show(False)
        self.cal_res_frame.Show(True) 
        
    def on_gen_model(self, event):
        """
        On Generic model menu event
        """
        if self.gen_frame == None:
            frame = SasGenWindow(parent=self.parent, manager=self)
            self.put_icon(frame)
            self.gen_frame = frame
        self.gen_frame.Show(False)
        self.gen_frame.Show(True) 

    def on_image_viewer(self, event):
        """
        Get choose an image file dialog
        
        :param event: menu event
        """
        self.image_view = ImageView(parent=self.parent)
        self.image_view.load()
        
    def on_python_console(self, event):
        """
        Open Python Console
        
        :param event: menu event
        """
        self.get_python_panel(filename=None)
        
    def get_python_panel(self, filename=None):
        """
        Get the python shell panel
        
        :param filename: file name to open in editor
        """
        if self.py_frame == None:
            frame = PyConsole(parent=self.parent, base=self, 
                              filename=filename)
            self.put_icon(frame)
            self.py_frame = frame
        self.py_frame.Show(False)
        self.py_frame.Show(True) 
        
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
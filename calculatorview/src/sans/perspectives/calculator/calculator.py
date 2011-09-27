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


from sans.guiframe.plugin_base import PluginBase
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
  
    def help(self, evt):
        """
        Show a general help dialog. 
        
        :TODO: replace the text with a nice image
            provide more hint on the SLD calculator
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1)    
        frame.Show(True)

    def get_tools(self):
        """
        Returns a set of menu entries for tools
        """
        kiessig_help = "Approximately computes the "
        kiessig_help += "thickness of a shell or the size of "
        kiessig_help += "particles \n from the width of a Kiessig fringe."
        sld_help = "Computes the Scattering Length Density."
        slit_length_help = "Computes the slit length from the beam profile."
        resolution_help = "Approximately estimates the "
        resolution_help += "resolution of Q in 2D based on the SANS "
        resolution_help += "instrumental parameter values."
        pyconsole_help = "Python Console from a third party (PyCrust)."
        #data_editor_help = "Meta Data Editor"
        return [("SLD Calculator", sld_help, self.on_calculate_sld),
                ("Slit Size Calculator", slit_length_help,
                        self.on_calculate_slit_size),
                ("Kiessig Thickness Calculator", 
                        kiessig_help, self.on_calculate_kiessig),
                          ("SANS Resolution Estimator", 
                        resolution_help, self.on_calculate_resoltuion),
                ("Python Console", pyconsole_help, self.on_python_console)]
              
    def on_edit_data(self, event):
        """
        Edit meta data 
        """
        from data_editor import DataEditorWindow
        frame = DataEditorWindow(parent=self.parent, data=[],
                                  title="Data Editor")
        frame.Show(True)
        event.Skip()

    def on_calculate_kiessig(self, event):
        """
        Compute the Kiessig thickness
        """
        from kiessig_calculator_panel import KiessigWindow
        frame = KiessigWindow()
        frame.Show(True) 
    
    def on_calculate_sld(self, event):
        """
        Compute the scattering length density of molecula
        """
        from sld_panel import SldWindow
        frame = SldWindow(base=self.parent)
        frame.Show(True) 
       
    def on_calculate_slit_size(self, event):
        """
        Compute the slit size a given data
        """
        from slit_length_calculator_panel import SlitLengthCalculatorWindow
        frame = SlitLengthCalculatorWindow(parent=self.parent)    
        frame.Show(True)
        
    def on_calculate_resoltuion(self, event):
        """
        Estimate the instrumental resolution
        """
        from resolution_calculator_panel import ResolutionWindow
        frame = ResolutionWindow(parent=self.parent)
        frame.Show(True) 
  
        #def on_perspective(self, event):
        """
        Call back function for the perspective menu item.
        We notify the parent window that the perspective
        has changed.
        
        :param event: menu event
        
        """
        #self.parent.set_perspective(self.perspective)
        #if event != None:
        #    event.Skip()
    def on_python_console(self, event):
        """
        Open Python Console
        
        :param event: menu event
        """
        from pyconsole import PyConsole
        frame = PyConsole(parent=self.parent)
        frame.Show(True) 
    
    
  
    

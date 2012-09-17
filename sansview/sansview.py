
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import os
import logging
from shutil import copy
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=os.path.join(os.path.expanduser("~"),'sasview.log'))

import wx
import sys
# The below will make sure that sasview application uses the matplotlib font 
# bundled with sasview. 
if hasattr(sys, 'frozen'):
    mplconfigdir = os.path.join(os.path.expanduser("~"), '.matplotlib')
    if not os.path.exists(mplconfigdir):
        os.mkdir(mplconfigdir)
    os.environ['MPLCONFIGDIR'] = mplconfigdir
    if sys.version_info < (2, 7):
        reload(sys)
    sys.setdefaultencoding("iso-8859-1")
from sans.guiframe import gui_manager
from sans.guiframe.gui_style import GUIFRAME
from welcome_panel import WelcomePanel
# For py2exe, import config here
import local_config
PLUGIN_MODEL_DIR = 'plugin_models'
APP_NAME = 'SasView'
def run():
    sys.path.append(os.path.join("..","..",".."))
    from multiprocessing import freeze_support
    freeze_support()
    sasview = SasView()
        
class SasViewApp(gui_manager.ViewApp):
    """
    """
  

class SasView():
    """
    """
    def __init__(self):
        """
        """
        #from gui_manager import ViewApp
        self.gui = SasViewApp(0) 
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        # Add perspectives to the basic application
        # Additional perspectives can still be loaded
        # dynamically
        # Note: py2exe can't find dynamically loaded
        # modules. We load the fitting module here
        # to ensure a complete Windows executable build.
        
        # Fitting perspective
        try:
            import sans.perspectives.fitting as module    
            fitting_plug = module.Plugin()
            self.gui.add_perspective(fitting_plug)
        except Exception as inst:
            logging.error("Fitting problems: " + str(inst))
            logging.error("%s: could not find Fitting plug-in module"% APP_NAME) 
            logging.error(sys.exc_value)  
            
        # P(r) perspective
        try:
            import sans.perspectives.pr as module    
            pr_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(pr_plug)
        except:
            logging.error("%s: could not find P(r) plug-in module"% APP_NAME)
            logging.error(sys.exc_value)  
        
        #Invariant perspective
        try:
            import sans.perspectives.invariant as module    
            invariant_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(invariant_plug)
        except:
            raise
            logging.error("%s: could not find Invariant plug-in module"% \
                          APP_NAME)
            logging.error(sys.exc_value)  
        
        #Calculator perspective   
        try:
            import sans.perspectives.calculator as module    
            calculator_plug = module.Plugin(standalone=False)
            self.gui.add_perspective(calculator_plug)
        except:
            logging.error("%s: could not find Calculator plug-in module"% \
                                                        APP_NAME)
            logging.error(sys.exc_value)  

        # initialize category stuff
        user_file = os.path.join(os.path.expanduser("~"),
                                 'serialized_categories.p')
        
        if not os.path.isfile(user_file): 
            # either first time starting sansview or the
            # user has deleted their category file
            my_dir = os.path.dirname(os.path.abspath(__file__))
            default_file = os.path.join(my_dir, '..',
                                        'sansmodels',
                                        'default_categories.p' )
            copy(default_file, user_file)

            
        # Add welcome page
        self.gui.set_welcome_panel(WelcomePanel)
      
        # Build the GUI
        self.gui.build_gui()
        # delete unused model folder    
        self.gui.clean_plugin_models(PLUGIN_MODEL_DIR)
        # Start the main loop
        self.gui.MainLoop()  
       


if __name__ == "__main__": 
    from multiprocessing import freeze_support
    freeze_support()
    #Process(target=SasView).start()
    sasview = SasView()

   

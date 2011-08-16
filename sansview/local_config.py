"""
    Application settings
"""
import time
import os
from sans.guiframe.gui_style import GUIFRAME
# Version of the application
__appname__ = "SansView"
__version__ = '1.9.2dev_AUG'
__download_page__ = 'http://danse.chem.utk.edu'
__update_URL__ = 'http://danse.chem.utk.edu/sansview_version.php'


# Debug message flag
__EVT_DEBUG__ = False

# Flag for automated testing
__TEST__ = False

# Debug message should be written to a file?
__EVT_DEBUG_2_FILE__   = False
__EVT_DEBUG_FILENAME__ = "debug.log"

# About box info
_do_aboutbox = True
_do_tutorial = True
_acknowledgement =  \
'''This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

'''
_homepage = "http://danse.chem.utk.edu"
_download = "http://danse.chem.utk.edu/sansview.html"
_authors = []
_paper = "http://danse.us/trac/sans/newticket"
_license = "mailto:sansdanse@gmail.com"


icon_path = "images"
media_path = "media"
test_path =  "test"

_nsf_logo = os.path.join(icon_path, "nsf_logo.png")
_danse_logo = os.path.join(icon_path, "danse_logo.png")
_inst_logo = os.path.join(icon_path, "utlogo.gif")
_nsf_url = "http://www.nsf.gov"
_danse_url = "http://www.cacr.caltech.edu/projects/danse/release/index.html"
_inst_url = "http://www.utk.edu"
_corner_image = os.path.join(icon_path, "angles_flat.png")
_welcome_image = os.path.join(icon_path, "SVwelcome.png")
_copyright = "(c) 2009, University of Tennessee"


#edit the list of file state your plugin can read
APPLICATION_WLIST = 'SansView files (*.svs)|*.svs'
APPLICATION_STATE_EXTENSION = '.svs'
GUIFRAME_WIDTH = 1150
GUIFRAME_HEIGHT = 840
PLUGIN_STATE_EXTENSIONS = ['.fitv', '.inv', '.prv']
PLUGINS_WLIST = ['Fitting files (*.fitv)|*.fitv',
                  'Invariant files (*.inv)|*.inv',
                  'P(r) files (*.prv)|*.prv']
PLOPANEL_WIDTH = 415
PLOPANEL_HEIGTH = 370
DATAPANEL_WIDTH = 235
DATAPANEL_HEIGHT = 700
SPLASH_SCREEN_PATH = os.path.join(icon_path,"SVwelcome_mini.png")
TUTORIAL_PATH = os.path.join(media_path,"Tutorial.pdf")
DEFAULT_STYLE = GUIFRAME.MULTIPLE_APPLICATIONS|GUIFRAME.MANAGER_ON\
                    |GUIFRAME.CALCULATOR_ON|GUIFRAME.TOOLBAR_ON
SPLASH_SCREEN_WIDTH = 512
SPLASH_SCREEN_HEIGHT = 366
SS_MAX_DISPLAY_TIME = 6000 #6 sec
WELCOME_PANEL_ON  = True
WELCOME_PANEL_SHOW = False
CLEANUP_PLOT = False
# OPEN and SAVE project menu
OPEN_SAVE_PROJECT_MENU = True
#VIEW MENU
VIEW_MENU = True
#EDIT MENU
EDIT_MENU = True

SetupIconFile_win = os.path.join(icon_path, "ball.ico")
SetupIconFile_mac = os.path.join(icon_path, "ball.icns")
DefaultGroupName = "DANSE"
OutputBaseFilename = "setupSansView"
DATAPANEL_WIDTH = 235
FIXED_PANEL = True
DATALOADER_SHOW = True
CLEANUP_PLOT = False
WELCOME_PANEL_SHOW = False
#Show or hide toolbar at the start up
TOOLBAR_SHOW = True
# set a default perspective
DEFAULT_PERSPECTIVE = 'None'

def printEVT(message):
    if __EVT_DEBUG__:
        print "%g:  %s" % (time.clock(), message)
        
        if __EVT_DEBUG_2_FILE__:
            out = open(__EVT_DEBUG_FILENAME__, 'a')
            out.write("%10g:  %s\n" % (time.clock(), message))
            out.close()
            
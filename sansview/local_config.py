"""
    Application settings
"""
import time
import os
from sans.guiframe.gui_style import GUIFRAME
import sans.sansview
import logging

# Version of the application
__appname__ = "SasView"
__version__ = sans.sansview.__version__
__build__ = sans.sansview.__build__
__download_page__ = 'https://sourceforge.net/projects/sansviewproject/files/'
__update_URL__ = 'http://sansviewproject.svn.sourceforge.net/viewvc/sansviewproject/trunk/sansview.latestversion'


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
'''This work originally developed as part of the DANSE project funded by the NSF
under grant DMR-0520547, and currently maintained by NIST, UMD, ORNL, ISIS, ESS 
and ILL.

'''
_homepage = "http://danse.chem.utk.edu"
_download = "https://sourceforge.net/projects/sansviewproject/"
_authors = []
_paper = "http://sourceforge.net/apps/trac/sansviewproject/report"
_license = "mailto:sansviewproject-developers@lists.sourceforge.net"


icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "images"))
logging.info("icon path: %s" % icon_path)
media_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "media"))
test_path =  os.path.abspath(os.path.join(os.path.dirname(__file__), "test"))

_nist_logo = "images/nist_logo.png"
_umd_logo = "images/umd_logo.png"
_sns_logo = "images/sns_logo.png"
_nsf_logo = os.path.join(icon_path, "nsf_logo.png")
_danse_logo = os.path.join(icon_path, "danse_logo.png")
_inst_logo = os.path.join(icon_path, "utlogo.gif")
_nist_url = "http://www.nist.gov/"
_umd_url = "http://www.umd.edu/"
_sns_url = "http://neutrons.ornl.gov/"
_nsf_url = "http://www.nsf.gov"
_danse_url = "http://www.cacr.caltech.edu/projects/danse/release/index.html"
_inst_url = "http://www.utk.edu"
_corner_image = os.path.join(icon_path, "angles_flat.png")
_welcome_image = os.path.join(icon_path, "SVwelcome.png")
_copyright = "(c) 2009 - 2011, University of Tennessee \n"
_copyright += "(c) 2012, UMD, NIST, ORNL, ISIS, ESS and ILL"


#edit the list of file state your plugin can read
APPLICATION_WLIST = 'SasView files (*.svs)|*.svs'
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
DefaultGroupName = "."
OutputBaseFilename = "setupSasView"

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
            
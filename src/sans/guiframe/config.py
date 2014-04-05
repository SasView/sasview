"""
Application settings
"""
import os
import time
from sans.guiframe.gui_style import GUIFRAME
# Version of the application
__appname__ = "DummyView"
__version__ = '0.0.0'
__build__ = '1'
__download_page__ = 'http://sourceforge.net/projects/sasview/files/'
__update_URL__ = ['svn.code.sf.net', 
                  '/p/sasview/code/trunk/sansview.latestversion']


# Debug message flag
__EVT_DEBUG__ = True

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
_homepage = "http://www.sasview.org"
_download = "http://sourceforge.net/projects/sasview/files/"
_authors = []
_paper = "http://sourceforge.net/p/sasview/tickets/"
_license = "mailto:help@sasview.org"
_nsf_logo = "images/nsf_logo.png"
_danse_logo = "images/danse_logo.png"
_inst_logo = "images/utlogo.gif"
_nist_logo = "images/nist_logo.png"
_umd_logo = "images/umd_logo.png"
_sns_logo = "images/sns_logo.png"
_isis_logo = "images/isis_logo.png"
_ess_logo = "images/ess_logo.png"
_ill_logo = "images/ill_logo.png"
_nist_url = "http://www.nist.gov/"
_umd_url = "http://www.umd.edu/"
_sns_url = "http://neutrons.ornl.gov/"
_nsf_url = "http://www.nsf.gov"
_danse_url = "http://www.cacr.caltech.edu/projects/danse/release/index.html"
_inst_url = "http://www.utk.edu"
_isis_url = "http://www.isis.stfc.ac.uk/"
_ess_url = "http://ess-scandinavia.eu/"
_ill_url = "http://www.ill.eu/"
_corner_image = "images/angles_flat.png"
_welcome_image = "images/SVwelcome.png"
_copyright = "(c) 2008, University of Tennessee"
#edit the lists below of file state your plugin can read
#for sansview this how you can edit these lists
#PLUGIN_STATE_EXTENSIONS = ['.prv','.fitv', '.inv']
#APPLICATION_STATE_EXTENSION = '.svs'
#PLUGINS_WLIST = ['P(r) files (*.prv)|*.prv',
#                  'Fitting files (*.fitv)|*.fitv',
#                  'Invariant files (*.inv)|*.inv']
#APPLICATION_WLIST = 'SansView files (*.svs)|*.svs'
APPLICATION_WLIST = ''
APPLICATION_STATE_EXTENSION = None
PLUGINS_WLIST = []
PLUGIN_STATE_EXTENSIONS = []
SPLASH_SCREEN_PATH = "images/danse_logo.png"     
DEFAULT_STYLE = GUIFRAME.SINGLE_APPLICATION
SPLASH_SCREEN_WIDTH = 500
SPLASH_SCREEN_HEIGHT = 300
WELCOME_PANEL_ON  = False
TUTORIAL_PATH = None
SS_MAX_DISPLAY_TIME = 1500
PLOPANEL_WIDTH = 350
PLOPANEL_HEIGTH = 350
GUIFRAME_WIDTH = 1000
GUIFRAME_HEIGHT = 800
CONTROL_WIDTH = -1
CONTROL_HEIGHT = -1
SetupIconFile_win = os.path.join("images", "ball.ico")
SetupIconFile_mac = os.path.join("images", "ball.icns")
DefaultGroupName = "DANSE"
OutputBaseFilename = "setupGuiFrame"
DATAPANEL_WIDTH = 235
DATAPANEL_HEIGHT = 700
FIXED_PANEL = True
DATALOADER_SHOW = True
CLEANUP_PLOT = False
WELCOME_PANEL_SHOW = False
#Show or hide toolbar at the start up
TOOLBAR_SHOW = True
# set a default perspective
DEFAULT_PERSPECTIVE = 'None'
# OPEN and SAVE project menu
OPEN_SAVE_PROJECT_MENU = True
CLEANUP_PLOT = False
# OPEN and SAVE project menu
OPEN_SAVE_PROJECT_MENU = False
#VIEW MENU
VIEW_MENU = False
#EDIT MENU
EDIT_MENU = False
import wx.lib.newevent
(StatusBarEvent, EVT_STATUS) = wx.lib.newevent.NewEvent()

def printEVT(message):
    if __EVT_DEBUG__:
        print "%g:  %s" % (time.clock(), message)
        
        if __EVT_DEBUG_2_FILE__:
            out = open(__EVT_DEBUG_FILENAME__, 'a')
            out.write("%10g:  %s\n" % (time.clock(), message))
            out.close()
            
"""
Application settings
"""
import time
from sans.guiframe.gui_style import GUIFRAME
# Version of the application
__appname__ = "DummyView"
__version__ = '0.1.0'
__download_page__ = 'http://danse.chem.utk.edu'


# Debug message flag
__EVT_DEBUG__ = True

# Flag for automated testing
__TEST__ = False

# Debug message should be written to a file?
__EVT_DEBUG_2_FILE__   = False
__EVT_DEBUG_FILENAME__ = "debug.log"

# About box info
_do_aboutbox = True
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
_nsf_logo = "images/nsf_logo.png"
_danse_logo = "images/danse_logo.png"
_inst_logo = "images/utlogo.gif"
_nsf_url = "http://www.nsf.gov"
_danse_url = "http://www.cacr.caltech.edu/projects/danse/release/index.html"
_inst_url = "http://www.utk.edu"
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
SS_MAX_DISPLAY_TIME = 3000 #3 sec
PLOPANEL_WIDTH = 400
PLOPANEL_HEIGTH = 400
GUIFRAME_WIDTH = 1000
GUIFRAME_HEIGHT = 800
SetupIconFile = os.path.join("images", "ball.ico")
DefaultGroupName = "DANSE"
OutputBaseFilename = "setupGuiFrame"

import wx.lib.newevent
(StatusBarEvent, EVT_STATUS) = wx.lib.newevent.NewEvent()

def printEVT(message):
    if __EVT_DEBUG__:
        print "%g:  %s" % (time.clock(), message)
        
        if __EVT_DEBUG_2_FILE__:
            out = open(__EVT_DEBUG_FILENAME__, 'a')
            out.write("%10g:  %s\n" % (time.clock(), message))
            out.close()
            
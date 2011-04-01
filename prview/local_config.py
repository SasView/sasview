"""
Application settings
"""
import time
import os
from sans.guiframe.gui_style import GUIFRAME

# Version of the application
__appname__ = "PrView"
__version__ = '0.3.0'
__download_page__ = 'http://danse.chem.utk.edu'
__update_URL__ = 'http://danse.chem.utk.edu/prview_version.php'


# Debug message flag
__EVT_DEBUG__ = False

# Flag for automated testing
__TEST__ = False

# Debug message should be written to a file?
__EVT_DEBUG_2_FILE__   = False
__EVT_DEBUG_FILENAME__ = "debug.log"

# About box info
_do_aboutbox=True
_acknowledgement =  \
'''This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

If you use DANSE applications to do scientific research that leads to publication, 
we ask that you acknowledge the use of the software with the following sentence:

"This work benefited from DANSE software developed under NSF award DMR-0520547." 
'''
_homepage = "http://danse.chem.utk.edu"
_download = "http://danse.chem.utk.edu/prview.html"
_authors = []
_paper = "http://danse.us/trac/sans/newticket"
_license = "mailto:sansdanse@gmail.com"

_nsf_logo = "images/nsf_logo.png"
_danse_logo = "images/danse_logo.png"
_inst_logo = "images/utlogo.gif"
_nsf_url = "http://www.nsf.gov"
_danse_url = "http://www.cacr.caltech.edu/projects/danse/release/index.html"
_inst_url = "http://www.utk.edu"
_corner_image = "images/prview.jpg"
_copyright = "(c) 2008, University of Tennessee"
#edit the list of file state your plugin can read

APPLICATION_STATE_EXTENSION = '.prv'
APPLICATION_WLIST = 'P(r) files (*.prv)|*.prv'
DEFAULT_STYLE = GUIFRAME.DEFAULT_STYLE
GUIFRAME_WIDTH = 850
GUIFRAME_HEIGHT = 780
PLUGIN_STATE_EXTENSIONS = ['.prv']
PLUGINS_WLIST = ['P(r) files (*.prv)|*.prv']
PLOPANEL_WIDTH = 400
PLOPANEL_HEIGTH = 400
SPLASH_SCREEN_PATH = "images/danse_logo.png"
SPLASH_SCREEN_WIDTH = 500
SPLASH_SCREEN_HEIGHT = 300
SS_MAX_DISPLAY_TIME = 3000 #3 sec
SetupIconFile = os.path.join("images", "ball.ico")
DefaultGroupName = "DANSE"
OutputBaseFilename = "setupPrView"

import wx.lib.newevent
(StatusBarEvent, EVT_STATUS) = wx.lib.newevent.NewEvent()

def printEVT(message):
    if __EVT_DEBUG__:
        print "%g:  %s" % (time.clock(), message)
        
        if __EVT_DEBUG_2_FILE__:
            out = open(__EVT_DEBUG_FILENAME__, 'a')
            out.write("%10g:  %s\n" % (time.clock(), message))
            out.close()
            
"""
Base module for loading and running the main SasView application.
"""
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
import sys
import logging
import traceback

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=os.path.join(os.path.expanduser("~"),
                                          'sasview.log'))
logging.captureWarnings(True)

class StreamToLogger(object):
    """
        File-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        """
        Main logging method
        """
        # Write the message to stdout so we can see it when running interactively
        sys.stdout.write(buf)
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

stderr_logger = logging.getLogger('STDERR')
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl

# Log the start of the session
logging.info(" --- SasView session started ---")

# Log the python version
logging.info("Python: %s" % sys.version)

# Allow the dynamic selection of wxPython via an environment variable, when devs
# who have multiple versions of the module installed want to pick between them.
# This variable does not have to be set of course, and through normal usage will
# probably not be, but this can make things a little easier when upgrading to a
# new version of wx.
WX_ENV_VAR = "SASVIEW_WX_VERSION"
if WX_ENV_VAR in os.environ:
    logging.info("You have set the %s environment variable to %s." % \
                 (WX_ENV_VAR, os.environ[WX_ENV_VAR]))
    import wxversion
    if wxversion.checkInstalled(os.environ[WX_ENV_VAR]):
        logging.info("Version %s of wxPython is installed, so using that version." % os.environ[WX_ENV_VAR])
        wxversion.select(os.environ[WX_ENV_VAR])
    else:
        logging.error("Version %s of wxPython is not installed, so using default version." % os.environ[WX_ENV_VAR])
else:
    logging.info("You have not set the %s environment variable, so using default version of wxPython." % WX_ENV_VAR)

import wx

try:
    logging.info("Wx version: %s" % wx.__version__)
except:
    logging.error("Wx version: error reading version")

import wxcruft
wxcruft.call_later_fix()
#wxcruft.trace_new_id()

# The below will make sure that sasview application uses the matplotlib font
# bundled with sasview.
if hasattr(sys, 'frozen'):
    mplconfigdir = os.path.join(os.path.expanduser("~"), '.matplotlib')
    if not os.path.exists(mplconfigdir):
        os.mkdir(mplconfigdir)
    os.environ['MPLCONFIGDIR'] = mplconfigdir
    reload(sys)
    sys.setdefaultencoding("iso-8859-1")
from sas.guiframe import gui_manager
from sas.guiframe.gui_style import GUIFRAME
from welcome_panel import WelcomePanel
# For py2exe, import config here
import local_config
PLUGIN_MODEL_DIR = 'plugin_models'
APP_NAME = 'SasView'

class SasView():
    """
    Main class for running the SasView application
    """
    def __init__(self):
        """
        """
        #from gui_manager import ViewApp
        self.gui = gui_manager.SasViewApp(0)
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
            import sas.perspectives.fitting as module    
            fitting_plug = module.Plugin()
            self.gui.add_perspective(fitting_plug)
        except Exception:
            logging.error("%s: could not find Fitting plug-in module"% APP_NAME)
            logging.error(traceback.format_exc())

        # P(r) perspective
        try:
            import sas.perspectives.pr as module
            pr_plug = module.Plugin()
            self.gui.add_perspective(pr_plug)
        except:
            logging.error("%s: could not find P(r) plug-in module"% APP_NAME)
            logging.error(traceback.format_exc())

        #Invariant perspective
        try:
            import sas.perspectives.invariant as module
            invariant_plug = module.Plugin()
            self.gui.add_perspective(invariant_plug)
        except:
            logging.error("%s: could not find Invariant plug-in module"% \
                          APP_NAME)
            logging.error(traceback.format_exc())

        #Calculator perspective   
        try:
            import sas.perspectives.calculator as module
            calculator_plug = module.Plugin()
            self.gui.add_perspective(calculator_plug)
        except:
            logging.error("%s: could not find Calculator plug-in module"% \
                                                        APP_NAME)
            logging.error(traceback.format_exc())


        # Add welcome page
        self.gui.set_welcome_panel(WelcomePanel)

        # Build the GUI
        self.gui.build_gui()
        # delete unused model folder
        self.gui.clean_plugin_models(PLUGIN_MODEL_DIR)
        # Start the main loop
        self.gui.MainLoop()


def run():
    """
    __main__ method for loading and running SasView
    """
    from multiprocessing import freeze_support
    freeze_support()
    if len(sys.argv) > 1:
        ## Run sasview as an interactive python interpreter
        #if sys.argv[1] == "-i":
        #    sys.argv = ["ipython", "--pylab"]
        #    from IPython import start_ipython
        #    sys.exit(start_ipython())
        thing_to_run = sys.argv[1]
        sys.argv = sys.argv[1:]
        import runpy
        if os.path.exists(thing_to_run):
            runpy.run_path(thing_to_run, run_name="__main__")
        else:
            runpy.run_module(thing_to_run, run_name="__main__")
    else:
        SasView()

if __name__ == "__main__":
    run()


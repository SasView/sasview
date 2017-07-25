# -*- coding: utf-8 -*-
"""
Base module for loading and running the main SasView application.
"""
################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# See the license text in license.txt
#
# copyright 2009, University of Tennessee
################################################################################
import sys

from sas.sasview.logger_config import SetupLogger

logger = SetupLogger(__name__).config_production()


# Log the start of the session
logger.info(" --- SasView session started ---")
# Log the python version
logger.info("Python: %s" % sys.version)


reload(sys)
sys.setdefaultencoding("iso-8859-1")

PLUGIN_MODEL_DIR = 'plugin_models'
APP_NAME = 'SasView'

def runSasView():
    """
    __main__ method for loading and running SasView
    """
    from multiprocessing import freeze_support
    freeze_support()
    from sas.qtgui.MainWindow.MainWindow import run
    run()


if __name__ == "__main__":
    runSasView()

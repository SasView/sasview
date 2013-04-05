################################################################################
#SasView was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE) project 
#funded by the US National Science Foundation.
#copyright 2008, University of Tennessee
################################################################################
#The set of routines that comprise this CORFUNC module were originally written 
#in 1994 at the behest of Anthony (Tony) Ryan by Thomas (Tom) Nye whilst an 
#undergraduate in Applied Mathematics at the University of Cambridge, and are 
#based on the earlier work of Gert Strobl (Universitat Freiburg) and co-workers 
#in the 1980's. The polydispersity analysis was proposed later by Guy Eeckhaut 
#(ICI).
#
#The original UNIX source was ported to the Windows environment (and given 
#a Java GUI) as part of Collaborative Computational Project #13, funded by the 
#UK Biotechnology & Biological Sciences Research Council and Engineering & 
#Physical Sciences Research Council, by CCP13 Post-Doctoral workers Richard 
#Denny and Mark Shotton in 1999.
#
#The alternative Hilbert transform (volume fraction profile) analysis of 
#Trevor Crowley (Salford University) and co-workers was suggested by Stephen 
#(Steve) King (ISIS Facility). Its incorporation was started by CCP13 Post-
#Doctoral worker Matthew Rodman and finally implemented in 2004 by Steve King 
#and Damian Flannery (ISIS Facility), with help from Richard Heenan (ISIS 
#Facility).
#
#Copyright 2013, UK Science & Technology Facilities Council
################################################################################

"""
This module implements correlation function analysis or calculates volume 
fraction profiles.

:author: Steve King/ISIS

"""
import sys
import wx
import copy
import logging

from sans.guiframe.dataFitting import Data1D
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import StatusEvent
from sans.guiframe.gui_style import GUIFRAME_ID
from sans.dataloader.loader import Loader
from sans.guiframe.plugin_base import PluginBase

class Plugin(PluginBase):
    """
    This class defines the interface for Corfunc Plugin class
    that can be used by the gui_manager.       
    """
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Corfunc", standalone=standalone)
        
        #dictionary containing data name and error on dy of that data 
#        self.err_dy = {}
       
        #default state objects
        self.state_reader = None 
        self._extensions = None
        self.temp_state = None 
        self.__data = None 
       
        # Log startup
        logging.info("Corfunc plug-in started")

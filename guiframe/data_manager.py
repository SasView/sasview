################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################
"""
This module manages all data loaded into the application. Data_manager makes 
available all data loaded  for the current perspective. 

All modules "creating Data" posts their data to data_manager . 
Data_manager  make these new data available for all other perspectives.
"""
import logging
from sans.guiframe.data_state import DataState
  
class DataManager(object):
    """
    Manage a list of data
    """
    def __init__(self):
        """
        Store opened path and data object created at the loading time
        :param auto_plot: if True the datamanager sends data to plotting 
                            plugin. 
        :param auto_set_data: if True the datamanager sends to the current
        perspective
        """
        self._selected_data = {}
        self.stored_data = {}
        self.message = ""
      
    def add_data(self, data_list):
        """
        receive a list of 
        """
        self._selected_data = {}
        for data in data_list:
            if data.id  in self.stored_data:
                msg = "Data manager already stores %s" % str(data.name)
                msg += ""
                logging.info(msg)
            data_state = DataState(data)
            self._selected_data[data.id] = data_state
            self.stored_data[data.id] = data_state
      
    def set_auto_plot(self, flag=False):
        """
        When flag is true the data is plotted automatically
        """
        self._auto_set_data = flag
        
    def set_auto_set_data(self, flag=False):
        """
        When flag is true the data is send to the current perspective
        automatically
        """
        self._auto_set_data = flag
        
    def get_message(self):
        """
        return message
        """
        return self.message
    
    def get_by_id(self, id_list=None):
        """
        get a list of data given a list of id
        """
        self._selected_data = {}
        for id in id_list:
            if id in self.stored_data:
                self._selected_data[id] = self.stored_data[id]
        return self._selected_data
    
    def append_theory(self, data_id, theory):
        """
        """
        print "append theory", self.stored_data, data_id
        if data_id in self.stored_data:
            data_state = self.stored_data[data_id]
            data_state.set_theory(theory)
            
    def delete_data(self, data_id, theory_id, delete_all):
        """
        """
        if data_id in self.stored_data:
            del self.stored_data[data_id]
        if data_id in self._selected_data:
            del self._selected_data
            
    def delete_by_id(self, id_list=None):
        """
        save data and path
        """
        for id in id_list:
            if id in self.stored_data:
                del self.stored_data[id]
            if id  in self._selected_data:
                del self._selected_data[id]
    
    def get_by_name(self, name_list=None):
        """
        return a list of data given a list of data names
        """
        self._selected_data = {}
        for selected_name in name_list:
            for id, data_state in self.stored_data.iteritems():
                if data_state.data.name == selected_name:
                    self._selected_data[id] = data_state
        return self._selected_data
    
    def delete_by_name(self, name_list=None):
        """
        save data and path
        """
        for selected_name in name_list:
            for id, data_state in self.stored_data.iteritems():
                if data_state.data.name == selected_name:
                    del self._selected_data[id]
                    del self.stored_data[data.id]

    def get_selected_data(self):
        """
        Send list of selected data
        """
        return self._selected_data
    
    def get_all_data(self):
        """
        return list of all available data
        """
        return self.stored_data
    

        
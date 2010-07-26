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

All modules creating
fake Data posts their data to data_manager . Data_manager  make these new data 
available for all other perspectives.
"""

class DataManager(object):
    """
     Manage a list of data
    """
    def __init__(self, parent):
        """
        Store opened path and data object created at the loading time
        """
        self.loaded_data_list = []
        self.created_data_list = []
        self.list_of_data = []
        self.message = ""
        
    def get_message(self):
        """
        return message
        """
        return self.message
    
    def set_loaded_data(self, data_list=[]):
        """
        save data and path
        """
        if not data_list:
            return
        else:
            for data, path in data_list:
                if data.name not in self.list_of_data:
                    self.loaded_data_list.append((data, path))
                    self.list_of_data.append(data.name)
                else:
                    self.message += " %s already loaded"%str(data.name)
        
    def set_created_data(self, data_list=[]):
        """
        return 
        """
        for data, path in data_list:
            for created_data, created_path in self.created_data_list:
                if data.name == created_data.name:
                    self.message += " %s already created"%str(data.name)
                else:
                    self.created_data_list.append((data, path))
    
    def get_data(self):
        """
        Send list of available data
        """
        return   self.loaded_data_list + self.created_data_list
        
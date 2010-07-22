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
        Initialize the class. This class is binded with event sent by 
        sans.guiframe.data_loader, sans.perspective.theoryview.theory 
        to collected data created and loaded data.
        
         
        attribute::  available_data  is dictionary of data
        attribute::  data_to_plot  dictionary  of data to plot automatically
        attribute:: sorted_data is a list of tuples containing  data's name,
                data's type(Data1D, Data2, Theory1D, Theory2D), data of
                 modification etc. 
        :param parent: is the class that instantiates this object.
         for sansview :parent is gui_manager
        """
        self.available_data = {}
        self.sorted_data = {}
        self.selected_data_list = []
        #gui manager 
        self.parent = parent
     
    def get_data(self, data_list={}):
        """
        return 
        """
        if not data_list:
            return self.available_data.values()
        for data, path in data_list:
            if data.name not in self.available_data.keys():
                self.available_data[data.name] = (data, path)
        return self.available_data.values()
    
    def on_get_data(self, data_list, plot=False):
        """
        This method is a handler to an event sent by data_loader or theory
        perspective. It gets a list of data object through that event
        and stores that list into available_data dictionary. Only new data are 
        stored.
        
        param event: contains a list of data. The size of the list is >= 1
        """
        for data, path in data_list:
            if data.name not in self.available_data.keys():
                self.available_data[data.name] = (data, path)
                if plot:
                    self.data_to_plot[data.name] = (data, path)
          
        return self.get_sorted_list()
    
    def sort_data(self):
        """
        Get the dictionary of data and created a list of turple of data's name,
                data's type(Data1D, Data2, Theory1D, Theory2D), data of
                 modification etc. 
        In other words extra data from available_data dictionary and create 
        sorted_data_list.
        """
        self.sorted_data = {}
        index = 1
        for data, path in self.available_data.values():
            self.sorted_data[index]= (data.name, data.__class__.__name__,
                                      "created on...", path)
            index += 1
        return self.sorted_data.values()  
    
    def get_sorted_list(self):
        """
        Return a list of turple of data sorted
        return: sorted_data_list .
        """
        return self.sort_data()
        
    def remove_data(self, data_name_list):
        """
        Remove data which names are in data_name_list from available_data and
        sorted_data_list. Post an event to all perspectives(including plotting
         perspective) to remove all reference of these data from themselves .
        
        param data_name_list: a list containing names of data to remove from 
        the whole application.
        """
        for data_name in data_name_list:
            del self.available_data[data_name]
            del self.data_to_plot[data_name]
        return self.get_sorted_list()
        
    def post_data(self, data_name_list, perspective=None,plot=False):
        """
        Set data from available_data for with the name is in data_name_list
        and post these data to the current active perspective
        """
        self.selected_data_list = []
        for data_name in data_name_list:
            self.selected_data_list.append(self.available_data[data_name])
        self.parent.post_data(list_of_data=self.selected_data_list, 
                              perspective=perspective,plot=plot)
        
    def get_selected_data(self):
        """
        """
        return self.selected_data_list
        
        
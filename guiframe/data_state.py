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
"""

class DataState(object):
    """
     Store information about data
    """
    def __init__(self, data, parent=None):
        """
        
        """
        self.parent = parent
        self._data = data
        self._name = ""
        self._path = None
        self._theory_list = []
        self._state_list = []
        self._message = ""
        
    def set_name(self, name):
        self._name = name
    def get_name(self):
        return self._name
    def set_data(self, data):
        self._data = data
        
    def get_data(self):
        return self._data
    
    def set_path(self, path):
        """
        Set the path of the loaded data
        """
        self._path = path
        
    def get_path(self):
        """
        return the path of the loaded data
        """
        return self._path
    
    def set_theory(self, theory):
        """
        """
        self._theory_list.append(theory)
        
    def get_theory(self):
        return self._theory_list
    
    def set_state(self, state):
        """
        """
        #self._theory_list.append(state)
        return
        
    def get_state(self):
        return self._state_list
    
    def get_message(self):
        """
        return message
        """
        return self._message
    
  
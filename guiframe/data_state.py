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
        self.data = data
        self.name = ""
        self.path = None
        self.theory_list = {}
        self.state_list = []
        self.message = ""
        
    def set_name(self, name):
        self.name = name
    def get_name(self):
        return self.name
    def set_data(self, data):
        self.data = data
        
    def get_data(self):
        return self.data
    
    def set_path(self, path):
        """
        Set the path of the loaded data
        """
        self.path = path
        
    def get_path(self):
        """
        return the path of the loaded data
        """
        return self.path
    
    def set_theory(self, theory):
        """
        """
        self.theory_list[theory.id] = theory
        
    def get_theory(self):
        return self.theory_list
    
    def set_state(self, state):
        """
        """
        #self.theory_list.append(state)
        return
        
    def get_state(self):
        return self.state_list
    
    def get_message(self):
        """
        return message
        """
        return self.message
    
  
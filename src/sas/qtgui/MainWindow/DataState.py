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
import copy


class DataState(object):
    """
     Store information about data
    """
    def __init__(self, data=None, parent=None):
        """
        
        """
        self.parent = parent
        self.data = data
        self.name = ""
        self.path = None
        self.theory_list = {}
        self.message = ""
        self.id = None
        
    def __str__(self):
        _str  = ""
        _str += "State with ID : %s \n" % str(self.id)
        if self.data is not None:
            _str += "Data name : %s \n" % str(self.data.name)
            _str += "Data ID : %s \n" % str(self.data.id)
        _str += "Theories available: %s \n" % len(self.theory_list)
        if self.theory_list:
            for id, item in self.theory_list.items():
                theory_data, theory_state = item
                _str += "Theory name : %s \n" % str(theory_data.name)
                _str += "Theory ID : %s \n" % str(id)
                _str += "Theory info: \n"
                _str += str(theory_data)
               
        return _str
        
    def clone(self):
        obj = DataState(copy.deepcopy(self.data))
        obj.parent = self.parent
        obj.name = self.name 
        obj.path = self.path 
        obj.message = self.message
        obj.id = self.id
        for id, item in self.theory_list.items():
            theory_data, theory_state = item
            state = None
            if theory_state is not None:
                state = theory_state.clone()
            obj.theory_list[id] = [copy.deepcopy(theory_data), 
                                   state]
        return obj
        
    def set_name(self, name):
        self.name = name
        
    def get_name(self):
        return self.name
    
    def set_data(self, data):
        """
        """
        self.data = data
  
   
    def get_data(self):
        """
        """
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
    
    def set_theory(self, theory_data, theory_state=None):
        """
        """
        self.theory_list[theory_data.id] = [theory_data, theory_state]
        data, state = list(self.theory_list.values())[0]
       
    def get_theory(self):
        return self.theory_list
    
    def get_message(self):
        """
        return message
        """
        return self.message
    
  

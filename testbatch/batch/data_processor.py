"""
This module implement a class that generates values given some inputs. The User apply a function to a sequence 
of inputs and outputs are generated.
"""
import numpy


class DataTable(object):
    """
    This class is store inputs as a dictionary of key (string) and values list of python objects.
    It generates outputs given some function and its current inputs.
    if an output object has an attribute "extract"   function returning attributes names and values 
    relevant to this output then DataTable will map them  accordingly.
    """
    def __init__(self, inputs):
        """
        """
        #array of inputs
        self.__inputs_data = None
        #array of outputs 
        self.__outputs_data = None
        #contains combinations of inputs and outputs
        self__data = None
        #the selected map function
        self.__function = map
        #the number of row in the array
        self.length = 0
        
    def set_inputs(self, inputs):
        """
        Checks that inputs is a dictionary.
        Checks that all values are list of same length.
        Creates an array of dimension n x m and stores into self.__inputs_data
        :param inputs: a dictionary of string as keys and values (list)  of same length
        :example: inputs= {"data":[1, 2], "temperature":[30, 40]}
                    result = self.set_value(inputs)
                    assert result == [   ["data" "temperature"]
                                        [1         30        ]
                                        [2          40       ]]
        """
        
    def get_inputs(self):
        """
        return array of inputs
        """
    def get_outputs(self):
        """
        return array of output value
        """
    def get_value(self):
        """
        Return current saved inputs and outputs
        """
        return self.__data
    
    def _mapply(self, arguments):
        """
        Receive a list of arguments where the fist item in the list is a function pointer
        and the rest of items are argument to the function
        :param arguments: arguments[0] is a function pointer
                            arguments[1:] is possible parameters of that function
        """
        return apply(arguments[0], arguments[1:])
    
    def _compute(self, instance, func_name, *args):
        """
        Receive an instance of a class , a function name  and some possible arguments for the function
        Generate result from that function
        """
        return getattr(instance, func)(*args)
    
    def compute(self,instances, func_names):
        """
        compute a series of values , the set the value of self.__outputs_data and self.__data
        :param instances: list of instance of object
        :param func_names: name of the function to use for mapping
        
        """
        
    def _extract_output(self, output):
        """
        receive an output which is a python object request extract_output function
        in order to extract additional information about the output. If the output does
        not have extract_output has attribute, the output is return as it is else
        a dictionary of output attribute names is return as well as their corresponding
        values 
        :example:  class OutPut:
                        a = 2
                        b = 3
                        out = OutPut()
                    result = self.extract_output(out)
                    assert result == {"a":2, "b":3}
        """
        
    def select_map_function(self, mapper="default"):
        """
        given a key word defined [mapper] a map function is used to map object
        available map functions are: built-in python map , processing map etc...
        """
  
class DataProcessor(object):
    """
    Implement a singleton of DataTable
    """
    __data_table = DataTable()
    
    def set_inputs(self, inputs):
        self.__data_table.set_inputs(inputs)
        
    def select_map_function(self, mapper="default"):
        self.__data_table.select_map_function(mapper)
        
    def compute(self,instance, func_name):
        return self.__data_table.compute(instance, func_name)
        
    def get_inputs(self):
        """
        return array of inputs
        """
        return self.__data_table.get_inputs()
    
    def get_outputs(self):
        """
        return array of output value
        """
        return self.__data_table.get_outputs()
    
    def get_value(self):
        """
        Return current saved inputs and outputs
        """
        return self.__data_table.get_value()
    
      
  
  
if __name__ == "__main__":
    a = numpy.array([['c','d']])  
    c = numpy.array([2,3]) 
    d = numpy.array([4,5])  
    m = numpy.column_stack([c, d])
    print numpy.concatenate((a, m))
    # the way set_value will work
    my_dict = {"c":[2,3], "d":[4, 5]}
    if my_dict:
        length = len(my_dict.values()[0])
        index = []
        for item in my_dict.values():
            assert len(item) == length 
        data = numpy.concatenate((numpy.array([my_dict.keys()]), numpy.column_stack( my_dict.values())))
        print "Data"
        print data
        print data[1:]
        print zip(data[1:1].T)
        
        
        
        
    
    
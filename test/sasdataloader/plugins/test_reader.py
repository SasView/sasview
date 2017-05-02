"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""
from __future__ import print_function

import os
import numpy as np
from sas.sascalc.dataloader.data_info import Data1D


class Reader:
    """
        Test reader to check plugin functionality
    """
    ## File type
    type = ["ASCII files (*.test)|*.test"]
    ## List of allowed extensions
    ext=['.test']  
    
    def read(self, path):
        """ 
            Load data file
            
            @param path: file path
            @return: Data1D object, or None
            @raise RuntimeError: when the file can't be opened
            @raise ValueError: when the length of the data vectors are inconsistent
        """
        if os.path.isfile(path):
            basename  = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if extension.lower() in self.ext:
                try:
                    input_f =  open(path,'r')
                except :
                    raise  RuntimeError, "ascii_reader: cannot open %s" % path
                buff = input_f.read()
                lines = buff.split('\n')
                x  = np.zeros(0)
                y  = np.zeros(0)
                dy = np.zeros(0)
                output = Data1D(x, y, dy=dy)
                self.filename = output.filename = basename
           
                for line in lines:
                    x  = np.append(x,  float(line))
                    
                output.x = x
                return output
        else:
            raise RuntimeError, "%s is not a file" % path
        return None
    
if __name__ == "__main__": 
    reader = Reader()
    output = reader.read("../test/test_data.test")
    print(output.x)
    
    
                        

"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""

import numpy
import os
from DataLoader.data_info import Data1D

class Reader:
    """
        Class to load ascii files (2 or 3 columns)
    """
    ## File type
    type = ["ASCII files (*.txt)|*.txt",
            "ASCII files (*.dat)|*.dat"]
    ## List of allowed extensions
    ext=['.txt', '.TXT', '.dat', '.DAT']  
    
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
                x  = numpy.zeros(0)
                y  = numpy.zeros(0)
                dy = numpy.zeros(0)
                output = Data1D(x, y, dy=dy)
                self.filename = output.filename = basename
                
                # The first good line of data will define whether
                # we have 2-column or 3-column ascii
                has_error = None
                
                for line in lines:
                    toks = line.split()
                    try:
                        _x = float(toks[0])
                        _y = float(toks[1])
                        
                        # If we have an extra token, check
                        # whether it can be interpreted as a
                        # third column.
                        _dy = None
                        if len(toks)>2:
                            try:
                                _dy = float(toks[2])
                            except:
                                # The third column is not a float, skip it.
                                pass
                            
                        # If we haven't set the 3rd column
                        # flag, set it now.
                        if has_error == None:
                            has_error = False if _dy == None else True

                        x  = numpy.append(x,   _x) 
                        y  = numpy.append(y,   _y)
                        if has_error == True:
                            dy = numpy.append(dy, _dy)
                        
                    except:
                        # Couldn't parse this line, skip it 
                        pass
                         
                     
                # Sanity check
                if has_error == True and not len(y) == len(dy):
                    raise ValueError, "ascii_reader: y and dy have different length"

                # If the data length is zero, consider this as
                # though we were not able to read the file.
                if len(x)==0:
                    raise ValueError, "ascii_reader: could not load file"
               
                output.x = x
                output.y = y
                output.dy = dy
                output.xaxis("\\rm{Q}", 'A^{-1}')
                output.yaxis("\\rm{I(Q)}","cm^{-1}")
                
                
                return output
        else:
            raise RuntimeError, "%s is not a file" % path
        return None
    
if __name__ == "__main__": 
    reader = Reader()
    #print reader.read("../test/test_3_columns.txt")
    print reader.read("../test/empty.txt")
    
    
                        
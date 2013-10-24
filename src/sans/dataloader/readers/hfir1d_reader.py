"""
    HFIR 1D 4-column data reader
"""
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2008, University of Tennessee
######################################################################
import numpy
import os
from sans.dataloader.data_info import Data1D

# Check whether we have a converter available
has_converter = True
try:
    from sans.data_util.nxsunit import Converter
except:
    has_converter = False

class Reader(object):
    """
    Class to load HFIR 1D 4-column files
    """
    ## File type
    type_name = "HFIR 1D"
    ## Wildcards
    type = ["HFIR 1D files (*.d1d)|*.d1d"]
    ## List of allowed extensions
    ext = ['.d1d']
    
    def read(self, path):
        """ 
        Load data file
        
        :param path: file path
        
        :return: Data1D object, or None
        
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if extension.lower() in self.ext:
                try:
                    input_f = open(path,'r')
                except:
                    raise  RuntimeError, "hfir1d_reader: cannot open %s" % path
                buff = input_f.read()
                lines = buff.split('\n')
                x = numpy.zeros(0)
                y = numpy.zeros(0)
                dx = numpy.zeros(0)
                dy = numpy.zeros(0)
                output = Data1D(x, y, dx=dx, dy=dy)
                self.filename = output.filename = basename
           
                data_conv_q = None
                data_conv_i = None
                
                if has_converter == True and output.x_unit != '1/A':
                    data_conv_q = Converter('1/A')
                    # Test it
                    data_conv_q(1.0, output.x_unit)
                    
                if has_converter == True and output.y_unit != '1/cm':
                    data_conv_i = Converter('1/cm')
                    # Test it
                    data_conv_i(1.0, output.y_unit)
                           
                for line in lines:
                    toks = line.split()
                    try:
                        _x = float(toks[0])
                        _y = float(toks[1])
                        _dx = float(toks[3])
                        _dy = float(toks[2])
                        
                        if data_conv_q is not None:
                            _x = data_conv_q(_x, units=output.x_unit)
                            _dx = data_conv_q(_dx, units=output.x_unit)
                            
                        if data_conv_i is not None:
                            _y = data_conv_i(_y, units=output.y_unit)
                            _dy = data_conv_i(_dy, units=output.y_unit)
                                                    
                        x = numpy.append(x, _x)
                        y = numpy.append(y, _y)
                        dx = numpy.append(dx, _dx)
                        dy = numpy.append(dy, _dy)
                    except:
                        # Couldn't parse this line, skip it 
                        pass
                         
                # Sanity check
                if not len(y) == len(dy):
                    msg = "hfir1d_reader: y and dy have different length"
                    raise RuntimeError, msg
                if not len(x) == len(dx):
                    msg = "hfir1d_reader: x and dx have different length"
                    raise RuntimeError, msg

                # If the data length is zero, consider this as
                # though we were not able to read the file.
                if len(x) == 0:
                    raise RuntimeError, "hfir1d_reader: could not load file"
               
                output.x = x
                output.y = y
                output.dy = dy
                output.dx = dx
                if data_conv_q is not None:
                    output.xaxis("\\rm{Q}", output.x_unit)
                else:
                    output.xaxis("\\rm{Q}", 'A^{-1}')
                if data_conv_i is not None:
                    output.yaxis("\\rm{Intensity}", output.y_unit)
                else:
                    output.yaxis("\\rm{Intensity}", "cm^{-1}")
                
                # Store loading process information
                output.meta_data['loader'] = self.type_name
                return output
        else:
            raise RuntimeError, "%s is not a file" % path
        return None

"""
    ASCII reader
"""
############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547.
#copyright 2008, University of Tennessee
#############################################################################


import numpy
import os
from sans.dataloader.data_info import Data1D

# Check whether we have a converter available
has_converter = True
try:
    from sans.data_util.nxsunit import Converter
except:
    has_converter = False
_ZERO = 1e-16


class Reader:
    """
    Class to load ascii files (2, 3 or 4 columns).
    """
    ## File type
    type_name = "ASCII"
    
    ## Wildcards
    type = ["ASCII files (*.txt)|*.txt",
            "ASCII files (*.dat)|*.dat",
            "ASCII files (*.abs)|*.abs",
            "CSV files (*.csv)|*.csv"]
    ## List of allowed extensions
    ext = ['.txt', '.TXT', '.dat', '.DAT', '.abs', '.ABS', 'csv', 'CSV']
    
    ## Flag to bypass extension check
    allow_all = True
    
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
            _, extension = os.path.splitext(basename)
            if self.allow_all or extension.lower() in self.ext:
                try:
                    # Read in binary mode since GRASP frequently has no-ascii
                    # characters that brakes the open operation
                    input_f = open(path,'rb')
                except:
                    raise  RuntimeError, "ascii_reader: cannot open %s" % path
                buff = input_f.read()
                lines = buff.split('\n')
                
                #Jae could not find python universal line spliter:
                #keep the below for now
                # some ascii data has \r line separator,
                # try it when the data is on only one long line
                if len(lines) < 2 :
                    lines = buff.split('\r')
                 
                x  = numpy.zeros(0)
                y  = numpy.zeros(0)
                dy = numpy.zeros(0)
                dx = numpy.zeros(0)
                
               #temp. space to sort data
                tx  = numpy.zeros(0)
                ty  = numpy.zeros(0)
                tdy = numpy.zeros(0)
                tdx = numpy.zeros(0)
                
                output = Data1D(x, y, dy=dy, dx=dx)
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
           
                # The first good line of data will define whether
                # we have 2-column or 3-column ascii
                has_error_dx = None
                has_error_dy = None
                
                #Initialize counters for data lines and header lines.
                is_data = False  # Has more than 5 lines
                # More than "5" lines of data is considered as actual
                # data unless that is the only data
                mum_data_lines = 5
                # To count # of current data candidate lines
                i = -1
                # To count total # of previous data candidate lines
                i1 = -1
                # To count # of header lines
                j = -1
                # Helps to count # of header lines
                j1 = -1
                #minimum required number of columns of data; ( <= 4).
                lentoks = 2
                for line in lines:
                    toks = line.split(',')
                    if len(toks) < 2:
                        toks = line.split()
                    try:
                        #Make sure that all columns are numbers.
                        for colnum in range(len(toks)):
                            float(toks[colnum])
                            
                        _x = float(toks[0])
                        _y = float(toks[1])
                        
                        #Reset the header line counters
                        if j == j1:
                            j = 0
                            j1 = 0
                            
                        if i > 1:
                            is_data = True
                        
                        if data_conv_q is not None:
                            _x = data_conv_q(_x, units=output.x_unit)
                            
                        if data_conv_i is not None:
                            _y = data_conv_i(_y, units=output.y_unit)
                        
                        # If we have an extra token, check
                        # whether it can be interpreted as a
                        # third column.
                        _dy = None
                        if len(toks) > 2:
                            try:
                                _dy = float(toks[2])
                                
                                if data_conv_i is not None:
                                    _dy = data_conv_i(_dy, units=output.y_unit)
                                
                            except:
                                # The third column is not a float, skip it.
                                pass
                            
                        # If we haven't set the 3rd column
                        # flag, set it now.
                        if has_error_dy == None:
                            has_error_dy = False if _dy == None else True
                            
                        #Check for dx
                        _dx = None
                        if len(toks) > 3:
                            try:
                                _dx = float(toks[3])
                                
                                if data_conv_i is not None:
                                    _dx = data_conv_i(_dx, units=output.x_unit)
                                
                            except:
                                # The 4th column is not a float, skip it.
                                pass
                            
                        # If we haven't set the 3rd column
                        # flag, set it now.
                        if has_error_dx == None:
                            has_error_dx = False if _dx == None else True
                        
                        #After talked with PB, we decided to take care of only
                        # 4 columns of data for now.
                        #number of columns in the current line
                        #To remember the # of columns in the current
                        #line of data
                        new_lentoks = len(toks)
                        
                        #If the previous columns not equal to the current,
                        #mark the previous as non-data and reset the dependents.
                        if lentoks != new_lentoks:
                            if is_data == True:
                                break
                            else:
                                i = -1
                                i1 = 0
                                j = -1
                                j1 = -1
                            
                        #Delete the previously stored lines of data candidates
                        # if is not data.
                        if i < 0 and -1 < i1 < mum_data_lines and \
                            is_data == False:
                            try:
                                x = numpy.zeros(0)
                                y = numpy.zeros(0)
                            except:
                                pass
                            
                        x = numpy.append(x, _x) 
                        y = numpy.append(y, _y)
                        
                        if has_error_dy == True:
                            #Delete the previously stored lines of
                            # data candidates if is not data.
                            if i < 0 and -1 < i1 < mum_data_lines and \
                                is_data == False:
                                try:
                                    dy = numpy.zeros(0)
                                except:
                                    pass
                            dy = numpy.append(dy, _dy)
                            
                        if has_error_dx == True:
                            #Delete the previously stored lines of
                            # data candidates if is not data.
                            if i < 0 and -1 < i1 < mum_data_lines and \
                                is_data == False:
                                try:
                                    dx = numpy.zeros(0)
                                except:
                                    pass
                            dx = numpy.append(dx, _dx)
                            
                        #Same for temp.
                        #Delete the previously stored lines of data candidates
                        # if is not data.
                        if i < 0 and -1 < i1 < mum_data_lines and\
                            is_data == False:
                            try:
                                tx = numpy.zeros(0)
                                ty = numpy.zeros(0)
                            except:
                                pass

                        tx = numpy.append(tx, _x)
                        ty = numpy.append(ty, _y)
                        
                        if has_error_dy == True:
                            #Delete the previously stored lines of
                            # data candidates if is not data.
                            if i < 0 and -1 < i1 < mum_data_lines and \
                                is_data == False:
                                try:
                                    tdy = numpy.zeros(0)
                                except:
                                    pass
                            tdy = numpy.append(tdy, _dy)
                        if has_error_dx == True:
                            #Delete the previously stored lines of
                            # data candidates if is not data.
                            if i < 0 and -1 < i1 < mum_data_lines and \
                                is_data == False:
                                try:
                                    tdx = numpy.zeros(0)
                                except:
                                    pass
                            tdx = numpy.append(tdx, _dx)

                        #reset i1 and flag lentoks for the next
                        if lentoks < new_lentoks:
                            if is_data == False:
                                i1 = -1
                        #To remember the # of columns on the current line
                        # for the next line of data
                        lentoks = len(toks)
                        
                        #Reset # of header lines and counts #
                        # of data candidate lines
                        if j == 0 and j1 == 0:
                            i1 = i + 1
                        i += 1
                    except:

                        # It is data and meet non - number, then stop reading
                        if is_data == True:
                            break
                        lentoks = 2
                        #Counting # of header lines
                        j += 1
                        if j == j1 + 1:
                            j1 = j
                        else:
                            j = -1
                        #Reset # of lines of data candidates
                        i = -1
                        
                        # Couldn't parse this line, skip it
                        pass
                    
                input_f.close()
                # Sanity check
                if has_error_dy == True and not len(y) == len(dy):
                    msg = "ascii_reader: y and dy have different length"
                    raise RuntimeError, msg
                if has_error_dx == True and not len(x) == len(dx):
                    msg = "ascii_reader: y and dy have different length"
                    raise RuntimeError, msg
                # If the data length is zero, consider this as
                # though we were not able to read the file.
                if len(x) == 0:
                    raise RuntimeError, "ascii_reader: could not load file"
                
                #Let's re-order the data to make cal.
                # curve look better some cases
                ind = numpy.lexsort((ty, tx))
                for i in ind:
                    x[i] = tx[ind[i]]
                    y[i] = ty[ind[i]]
                    if has_error_dy == True:
                        dy[i] = tdy[ind[i]]
                    if has_error_dx == True:
                        dx[i] = tdx[ind[i]]
                # Zeros in dx, dy
                if has_error_dx:
                    dx[dx == 0] = _ZERO
                if has_error_dy:
                    dy[dy == 0] = _ZERO
                #Data
                output.x = x[x != 0]
                output.y = y[x != 0]
                output.dy = dy[x != 0] if has_error_dy == True\
                    else numpy.zeros(len(output.y))
                output.dx = dx[x != 0] if has_error_dx == True\
                    else numpy.zeros(len(output.x))
                                
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
                if len(output.x) < 1:
                    raise RuntimeError, "%s is empty" % path
                return output
            
        else:
            raise RuntimeError, "%s is not a file" % path
        return None

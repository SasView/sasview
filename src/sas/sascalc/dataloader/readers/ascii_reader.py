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


import numpy as np
import os
from sas.sascalc.dataloader.data_info import Data1D

# Check whether we have a converter available
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
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
                    # characters that breaks the open operation
                    input_f = open(path,'rb')
                except:
                    raise  RuntimeError("ascii_reader: cannot open %s" % path)
                buff = input_f.read()
                lines = buff.splitlines()

                # Arrays for data storage
                tx = np.zeros(0)
                ty = np.zeros(0)
                tdy = np.zeros(0)
                tdx = np.zeros(0)

                # The first good line of data will define whether
                # we have 2-column or 3-column ascii
                has_error_dx = None
                has_error_dy = None

                #Initialize counters for data lines and header lines.
                is_data = False
                # More than "5" lines of data is considered as actual
                # data unless that is the only data
                min_data_pts = 5
                # To count # of current data candidate lines
                candidate_lines = 0
                # To count total # of previous data candidate lines
                candidate_lines_previous = 0
                #minimum required number of columns of data
                lentoks = 2
                for line in lines:
                    toks = self.splitline(line)
                    # To remember the # of columns in the current line of data
                    new_lentoks = len(toks)
                    try:
                        if new_lentoks == 1 and not is_data:
                            ## If only one item in list, no longer data
                            raise ValueError
                        elif new_lentoks == 0:
                            ## If the line is blank, skip and continue on
                            ## In case of breaks within data sets.
                            continue
                        elif new_lentoks != lentoks and is_data:
                            ## If a footer is found, break the loop and save the data
                            break
                        elif new_lentoks != lentoks and not is_data:
                            ## If header lines are numerical
                            candidate_lines = 0
                            candidate_lines_previous = 0

                        #Make sure that all columns are numbers.
                        for colnum in range(len(toks)):
                            # Any non-floating point values throw ValueError
                            float(toks[colnum])

                        candidate_lines += 1
                        _x = float(toks[0])
                        _y = float(toks[1])
                        _dx = None
                        _dy = None

                        #If 5 or more lines, this is considering the set data
                        if candidate_lines >= min_data_pts:
                            is_data = True

                        # If a 3rd row is present, consider it dy
                        if new_lentoks > 2:
                            _dy = float(toks[2])
                        has_error_dy = False if _dy is None else True

                        # If a 4th row is present, consider it dx
                        if new_lentoks > 3:
                            _dx = float(toks[3])
                        has_error_dx = False if _dx is None else True

                        # Delete the previously stored lines of data candidates if
                        # the list is not data
                        if candidate_lines == 1 and -1 < candidate_lines_previous < min_data_pts and \
                            is_data == False:
                            try:
                                tx = np.zeros(0)
                                ty = np.zeros(0)
                                tdy = np.zeros(0)
                                tdx = np.zeros(0)
                            except:
                                pass

                        if has_error_dy == True:
                            tdy = np.append(tdy, _dy)
                        if has_error_dx == True:
                            tdx = np.append(tdx, _dx)
                        tx = np.append(tx, _x)
                        ty = np.append(ty, _y)

                        #To remember the # of columns on the current line
                        # for the next line of data
                        lentoks = new_lentoks
                        candidate_lines_previous = candidate_lines
                    except ValueError:
                        # It is data and meet non - number, then stop reading
                        if is_data == True:
                            break
                        lentoks = 2
                        has_error_dx = None
                        has_error_dy = None
                        #Reset # of lines of data candidates
                        candidate_lines = 0
                    except:
                        pass

                input_f.close()
                if not is_data:
                    msg = "ascii_reader: x has no data"
                    raise RuntimeError(msg)
                # Sanity check
                if has_error_dy == True and not len(ty) == len(tdy):
                    msg = "ascii_reader: y and dy have different length"
                    raise RuntimeError(msg)
                if has_error_dx == True and not len(tx) == len(tdx):
                    msg = "ascii_reader: y and dy have different length"
                    raise RuntimeError(msg)
                # If the data length is zero, consider this as
                # though we were not able to read the file.
                if len(tx) == 0:
                    raise RuntimeError("ascii_reader: could not load file")

                #Let's re-order the data to make cal.
                # curve look better some cases
                ind = np.lexsort((ty, tx))
                x = np.zeros(len(tx))
                y = np.zeros(len(ty))
                dy = np.zeros(len(tdy))
                dx = np.zeros(len(tdx))
                output = Data1D(x, y, dy=dy, dx=dx)
                self.filename = output.filename = basename

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
                    else np.zeros(len(output.y))
                output.dx = dx[x != 0] if has_error_dx == True\
                    else np.zeros(len(output.x))

                output.xaxis("\\rm{Q}", 'A^{-1}')
                output.yaxis("\\rm{Intensity}", "cm^{-1}")

                # Store loading process information
                output.meta_data['loader'] = self.type_name
                if len(output.x) < 1:
                    raise RuntimeError("%s is empty" % path)
                return output

        else:
            raise RuntimeError("%s is not a file" % path)
        return None

    def splitline(self, line):
        """
        Splits a line into pieces based on common delimeters
        :param line: A single line of text
        :return: list of values
        """
        # Initial try for CSV (split on ,)
        toks = line.split(',')
        # Now try SCSV (split on ;)
        if len(toks) < 2:
            toks = line.split(';')
        # Now go for whitespace
        if len(toks) < 2:
            toks = line.split()
        return toks
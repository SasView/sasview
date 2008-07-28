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
        Class to load IGOR reduced .ABS files
    """
    ## List of allowed extensions
    ext=['.abs', '.ABS']  
    
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
                    raise  RuntimeError, "abs_reader: cannot open %s" % path
                buff = input_f.read()
                lines = buff.split('\n')
                x  = numpy.zeros(0)
                y  = numpy.zeros(0)
                dy = numpy.zeros(0)
                output = Data1D(x, y, dy=dy)
                self.filename = output.filename = basename
                
                is_info = False
                is_center = False
                is_data_started = False
                
                for line in lines:
                    
                    # Information line 1
                    if is_info==True:
                        is_info = False
                        line_toks = line.split()
                        
                        # Wavelength in Angstrom
                        try:
                            output.source.wavelength = float(line_toks[1])
                        except:
                            raise ValueError,"IgorReader: can't read this file, missing wavelength"
                        
                        # Distance in meters
                        try:
                            output.detector.distance = float(line_toks[3])*1000.0
                        except:
                            raise ValueError,"IgorReader: can't read this file, missing distance"
                        
                        # Transmission
                        try:
                            output.sample.transmission = float(line_toks[4])
                        except:
                            # Transmission is not a mandatory entry
                            pass
                    
                        # Thickness
                        try:
                            output.sample.thickness = float(line_toks[5])
                        except:
                            # Thickness is not a mandatory entry
                            pass
                    
                    #MON CNT   LAMBDA   DET ANG   DET DIST   TRANS   THICK   AVE   STEP
                    if line.count("LAMBDA")>0:
                        is_info = True
                        
                    # Find center info line
                    if is_center==True:
                        is_center = False                
                        line_toks = line.split()
                        # Center in bin number
                        center_x = float(line_toks[0])
                        center_y = float(line_toks[1])
                        output.detector.beam_center.x = center_x
                        output.detector.beam_center.y = center_y
                        
                        # Detector type
                        try:
                            output.detector.name = line_toks[7]
                        except:
                            # Detector name is not a mandatory entry
                            pass
                    
                    #BCENT(X,Y)   A1(mm)   A2(mm)   A1A2DIST(m)   DL/L   BSTOP(mm)   DET_TYP 
                    if line.count("BCENT")>0:
                        is_center = True
                        
                    # Parse the data
                    if is_data_started==True:
                        toks = line.split()
                        try:  
                            _x  = float(toks[0])
                            _y  = float(toks[1]) 
                            _dy = float(toks[2])
                           
                            x  = numpy.append(x,   _x) 
                            y  = numpy.append(y,   _y)
                            dy = numpy.append(dy, _dy)
                        except:
                            # Could not read this data line. If we are here
                            # it is because we are in the data section. Just
                            # skip it.
                            pass
                        
                    #The 6 columns are | Q (1/A) | I(Q) (1/cm) | std. dev. I(Q) (1/cm) | sigmaQ | meanQ | ShadowFactor|
                    if line.count("The 6 columns")>0:
                        is_data_started = True
            
                # Sanity check
                if not len(y) == len(dy):
                    raise ValueError, "abs_reader: y and dy have different length"

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
    print reader.read("../test/jan08002.ABS")
    
    
            
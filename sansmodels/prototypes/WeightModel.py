#!/usr/bin/env python
""" 
    Wrapper for the Disperser class extension

    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

import math
import os, string, sys
from sans.models.BaseComponent import BaseComponent
from sans.models.CylinderModel import CylinderModel
    
class WeightModel(CylinderModel):
    """ 
    """
        
    def __init__(self):
        """ Initialization 
            @param model: Model to disperse [BaseComponent]
            @param param: Parameter to disperse [string]
        """
        
        # Initialize BaseComponent first, then sphere
        CylinderModel.__init__(self)
        self.params['datafile'] = '' 
        
        self.d = None
        ## Name of the model
        self.name = 'WeightModel'
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q, or [q,phi]
            @return: scattering function P(q)
        """
        if len(self.d.x)==0:
            return 0.0
        try:
            total = 0
            norma = 0
            for i in range(len(self.d.x)):
                self.params['cyl_phi'] = self.d.x[i]*math.pi/180.0
                total += CylinderModel.run(self, x) * self.d.y[i]
                
                
                self.params['cyl_phi'] = -self.d.x[i]*math.pi/180.0
                total += CylinderModel.run(self, x) * self.d.y[i]
                
                norma += 2.0*self.d.y[i]
            return total/norma
        except:
            print sys.exc_value
            
        return 0.0
           
    def readData(self):
                self.d = DataReader(self.params['datafile'])
                self.d.read()

   
class DataReader:
    """ Simple data reader for Igor data files """
    
    def __init__(self, filename):
        """ Init
            @param filename: Name of Igor data file to read
        """
        self.file = filename
        self.x = []
        self.y = []
        
    def read(self):
        """ Read file """
        # Check if the file is there
        if not os.path.isfile(self.file):
            raise ValueError, \
            "Specified file %s is not a regular file" % self.file
        
        # Read file
        f = open(self.file,'r')
        buf = f.read()
        
        # Get content
        dataStarted = False
        
        
        lines = string.split(buf,'\n')
        itot = 0
        self.x = []
        self.y = []
        for line in lines:
            if line.count("Angle")>0:
                dataStarted = True
                continue
                
            if dataStarted == True:
                
                try:
                    toks = line.split()
                except:
                    print sys.exc_value
                
                self.x.append(float(toks[0]))
                
                self.y.append(float(toks[1]))
                
                
                itot += 1
                    
        print "Read %g points from file %s" % (len(self.image), self.file)
                
       
if __name__ == '__main__':
    app = WeightModel()
    cyl = CylinderModel()
    print "%s: f(1) = %g" % (app.name, app.run(1))
   
# End of file

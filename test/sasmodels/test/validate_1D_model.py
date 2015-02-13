#!/usr/bin/env python
""" 
    Class to validate a given model by reading a test data set
    generated from the IGOR SAS analysis tool from the NCNR
"""
import sys, math


class Validate1D:
    """ 
        Class to validate a given model by reading a test data set
        generated from the IGOR SAS analysis tool from the NCNR
    """
    
    def __init__(self):
        """ Initialization """
        # Precision for the result comparison
        self.precision = 0.0001
        # Flag for end result
        self.passed = True
                
    def __call__(self, filename):
        """ 
            Perform test on a data file
            @param filename: name of the test data set
        """
        from sas.models.CylinderModel import CylinderModel
        
        # Read the data file
        file_obj = open(filename,'r')
        content = file_obj.read()
        
        # Flag to determine whether we are in the DATA section
        started_data = False
        # Model to test
        model_object = None
        
        # Process each line of the file
        for line in content.split('\n'):
            if len(line)==0:
                continue
            try:
                # Catch class name
                if line.count("pythonclass")>0 and model_object==None:
                    toks = line.split('=')
                    print "Found class", toks[1]
                    classname = toks[1].lstrip().rstrip()
                    exec "from sas.models.%s import %s" % (classname, classname)
                    exec "model_object = %s()" % classname
                
                    # Output file for plotting
                    file_out = open("%s_out.txt" % classname, 'w')
                    file_out.write("<q>  <I_danse>  <I_igor>\n")
                
                # Process data
                elif started_data:
                    toks = line.split()
                    q = float(toks[0])
                    iq = float(toks[1])
                    
                    value = model_object.run(q)
                    
                    file_out.write("%g %g %g\n" % (q, value, iq))
                    
                    if math.fabs( (value - iq)/iq )>self.precision:
                        self.passed = False
                        print "ERROR q=%g: %g <> %g" % (q, model_object.run(q), iq)
                        
                # Catch DATA tag
                elif line.count("DATA")>0:
                    started_data = True
                                
                # Process parameters
                elif started_data == False and not model_object==None:
                    toks = line.split('=')
                    if len(toks)==2:
                        print "Setting parameter", line
                        model_object.setParam(toks[0].lstrip().rstrip(), 
                                              float(toks[1]))
            except:
                print "Could not parse line:\n %s" % line
                print sys.exc_value
            
        file_obj.close()
        file_out.close()
        
        print "Test passed = ", self.passed
        return self.passed
            
if __name__ == '__main__':
    validator = Validate1D()
    all_pass = True
    all_pass = all_pass and validator("sphere_testdata.txt")
    print '\n'
    all_pass = all_pass and validator("cylinder_testdata.txt")
    print '\n'
    all_pass = all_pass and validator("core_shell_cyl_testdata.txt")
    print '\n'
    all_pass = all_pass and validator("core_shell_testdata.txt")
    print '\n'
    all_pass = all_pass and validator("ellipsoid_testdata.txt")
    print '\n'
    all_pass = all_pass and validator("elliptical_cylinder_testdata.txt")

    print '\nOverall result:', all_pass
        
        
        
  
    
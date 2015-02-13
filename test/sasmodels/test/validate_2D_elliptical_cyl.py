#!/usr/bin/env python
""" 
    Test for Elliptical Cylinder model.
    Class to validate a given 2D model by averaging it
    and comparing to 1D prediction.
    
"""
import sys, math
from sas.models.EllipticalCylinderModel import EllipticalCylinderModel


class Validate2D:
    """ 
        Class to validate a given 2D model by averaging it
        and comparing to 1D prediction.
    """
    
    def __init__(self):
        """ Initialization """
        # Precision for the result comparison
        self.precision = 0.000001
        # Flag for end result
        self.passed = True
        # Verbose flag
        self.verbose = True
                
    def __call__(self, npts = 101):
        """ 
            Perform test and produce output file
            @param npts: number of points to average over
            @return: True if the test passed, otherwise False
        """
        passed = True
        
        model = EllipticalCylinderModel()
        
        theta_label = 'cyl_theta'
        if not model.params.has_key(theta_label):
            theta_label = 'axis_theta'
            
        phi_label = 'cyl_phi'
        if not model.params.has_key(phi_label):
            phi_label = 'axis_phi'
        
        output_f = open("average_func.txt",'w')    
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 15):
            q = 0.3/15.0*i_q
            value = self.average_point_3D(model, q, npts)
            ana = model.run(q)
            if q<0.3 and (value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            if self.verbose:
                print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
    
    def average_point_3D(self, model, q, npts):
        """
            Average intensity over all orientations
            of the main cylinder axis and the 
            rotation around that axis
            
            @param model: model to test
            @param q: q-value
            @param npts: number of points to average over
            @return: average intensity
        """
        sum = 0.0
        for i_theta in range(npts):
            theta = math.pi/npts*i_theta
            
            model.setParam('cyl_theta', theta)
            
            for j in range(npts):
                model.setParam('cyl_phi', math.pi * 2.0 / npts * j)
                     
                for k in range(npts):
                    model.setParam("cyl_psi", math.pi * 2.0 / npts * k)
                    
                    if str(model.run([q, 0])).count("IN")>0:                        
                        if self.verbose:
                            #print "ERROR", q, theta, math.pi * 2.0 / npts * j
                            pass
                    else:
                        sum += math.fabs(math.cos(theta))*model.run([q, 0])
         
        value = sum/npts/npts/npts
        return value

    def checkCylinder2D(self, phi):
        """ 
            Check that the 2D scattering intensity reduces
            to a cylinder when r_ratio = 1.0
            @param phi: angle of the vector q on the detector
            @return: True if the test passed, otherwise False
        """
        from sas.models.CylinderModel import CylinderModel
        
        cyl = CylinderModel()
        cyl.setParam("cyl_theta", 90)
        cyl.setParam("cyl_phi", 0.0)
        cyl.setParam("radius", 20)
        cyl.setParam("length", 400)
        cyl.setParam("sldCyl", 2.0e-6)
        cyl.setParam("sldSolv", 1.0e-6)

        ell = EllipticalCylinderModel()
        ell.setParam("r_ratio", 1.0)
        ell.setParam("r_minor", 20)
        ell.setParam("cyl_theta", 90)
        ell.setParam("cyl_phi", 0.0)
        ell.setParam("length", 400)
        ell.setParam("sldCyl", 2.0e-6)
        ell.setParam("sldSolv", 1.0e-6)
        
        passed = True
        for i_q in range(1, 30):
            q = 0.025*i_q
            ell_val = ell.run([q, phi])
            cyl_val = cyl.run([q, phi])
            if self.verbose:
                print "Q=%g    Ell=%g    Cyl=%g   R=%g" %(q, ell_val, cyl_val, ell_val/cyl_val)
            if math.fabs(ell_val-cyl_val)/cyl_val>0.05:
                passed= False
                
        return passed

        
    def checkCylinder(self, points):
        """
            Compare the average over all orientations
            of the main cylinder axis for a cylinder
            and the elliptical cylinder with r_ratio = 1
            
            @param points: number of points to average over
            @return: True if the test passed, otherwise False
        """
        from sas.models.CylinderModel import CylinderModel
        
        passed = True
        
        npts =points
        model = EllipticalCylinderModel()
        model.setParam('r_ratio', 1.0)
        model.setParam("r_minor", 20)
        model.setParam("cyl_theta", 90)
        model.setParam("cyl_phi", 0.0)
        model.setParam("length", 400)
        model.setParam("sldEll", 2.0e-6)
        model.setParam("sldSolv", 1.0e-6)
        
        cyl = CylinderModel()
        cyl.setParam("cyl_theta", 90)
        cyl.setParam("cyl_phi", 0.0)
        cyl.setParam("radius", 20)
        cyl.setParam("length", 400)
        cyl.setParam("sldCyl", 2.0e-6)
        cyl.setParam("sldSolv", 1.0e-6)

        
        output_f = open("average_func.txt",'w')    
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 15):
            q = 0.3/15.0*i_q
            value = self.average_point_2D(model, q, npts)
            
            ana = cyl.run(q)
            if q<0.3 and math.fabs(value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            if self.verbose:
                print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
        
        

    def average_point_2D(self, model, q, npts):
        """
            Average intensity over all orientations
            of the main cylinder axis
            
            @param model: model to test
            @param q: q-value
            @param npts: number of points to average over
            @return: average intensity
        """
        sum = 0.0
        
        for i_theta in range(npts):
            theta = math.pi/npts*i_theta            
            model.setParam('cyl_theta', theta * 180 / math.pi)
            
            for j in range(npts):
                model.setParam('cyl_phi', 180 * 2.0 / npts * j)
                     
                if str(model.run([q, 0])).count("IN")>0:                        
                    if self.verbose:
                        print "ERROR", q, theta, 180 * 2.0 / npts * j
                else:
                    sum += math.fabs(math.cos(theta))*model.run([q, 0])
        
        value = sum/npts/npts*math.pi/2.0
        return value

    
if __name__ == '__main__':
    select = 0

    validator = Validate2D()
    validator.verbose = True
    
    print "Testing Elliptical cylinder to 5%\n"
    
    if select == 0 or select == 1:
        # Check that the scat intensity reduces to a cylinder
        # for r_ratio = 1
        print "Comparing to Cyl I(q,theta):", validator.checkCylinder2D(1.5)
    elif select == 0 or select == 2:
        print "Comparing average to Cyl I(q):", validator.checkCylinder(100)
    elif select == 0 or select == 3:
        ellcyl_passed = validator(100)
    
        
        
        
  
    

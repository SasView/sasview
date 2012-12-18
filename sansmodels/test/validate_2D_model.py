#!/usr/bin/env python
""" 
    Class to validate a given 2D model by averaging it
    and comparing to 1D prediction.
    
    The equation used for averaging is:
    
        (integral dphi from 0 to 2pi)(integral dtheta from 0 to pi)
             p(theta, phi) I(q) sin(theta) dtheta
             
        = (1/N_phi) (1/N_theta) (pi/2) (sum over N_phi) (sum over N_theta)
             p(theta_i, phi_i) I(q) sin(theta_i)
             
    where p(theta, phi) is the probability distribution normalized to 4pi.
    In the current case, we put p(theta, phi) = 1.
    
    The normalization factor results from:
          2pi/N_phi      for the phi sum
        x pi/N_theta     for the theta sum
        x 1/(4pi)        because p is normalized to 4pi
        --------------
        = (1/N_phi) (1/N_theta) (pi/2)
    
    Note: Ellipsoid
        Averaging the 2D ellipsoid scattering intensity give a slightly
        different output than the 1D function from the IGOR library 
        at hight Q (Q>0.3). This is due to the way the IGOR library 
        averages, taking only 76 points in alpha, the angle between
        the axis of the ellipsoid and the q vector.
        
    Note: Core-shell and sphere models are symmetric around
        all axes and don't need to be tested in the following way.
"""
import sys, math
from sans.models.SphereModel import SphereModel
from sans.models.CylinderModel import CylinderModel
from sans.models.EllipsoidModel import EllipsoidModel
from sans.models.CoreShellCylinderModel import CoreShellCylinderModel


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
                
    def __call__(self, model_class=CylinderModel, points = 101):
        """ 
            Perform test and produce output file
            @param model_class: python class of the model to test
        """
        print "Averaging %s" % model_class.__name__
        passed = True
        
        npts =points
        model = model_class()
        #model.setParam('scale', 1.0)
        #model.setParam('contrast', 1.0)
        
        theta_label = 'cyl_theta'
        if not model.params.has_key(theta_label):
            theta_label = 'axis_theta'
            
        phi_label = 'cyl_phi'
        if not model.params.has_key(phi_label):
            phi_label = 'axis_phi'
        
        output_f = open("%s_avg.txt" % model.__class__.__name__,'w')    
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 30):
            q = 0.025 *i_q
            sum = 0.0
            for i_theta in range(npts):
                theta = 180.0 / npts * i_theta
                
                model.setParam(theta_label, theta)
                
                for j in range(npts):
                    model.setParam(phi_label, 180.0 * 2.0 / npts * j)
                    if str(model.run([q, 0])).count("INF")>0:                        
                        print "ERROR", q, theta, 180.0 * 2.0 / npts * j
                    sum += math.fabs(math.cos(theta*math.pi/180.0))*model.run([q, 0])
                    #sum += model.run([q, 0])
            
            value = sum/npts/npts*math.pi/2.0
            ana = model.run(q)
            if q<0.25 and (value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
    
    def average(self, model_class=CylinderModel, points = 101):
        """ 
            Perform test and produce output file
            @param model_class: python class of the model to test
        """
        print "Averaging %s" % model_class.__name__
        passed = True
        
        npts =points
        model = model_class()
        model.setParam('scale', 1.0)
        #model.setParam('contrast', 1.0)
        
        theta_label = 'cyl_theta'
        if not model.params.has_key(theta_label):
            theta_label = 'axis_theta'
            
        phi_label = 'cyl_phi'
        if not model.params.has_key(phi_label):
            phi_label = 'axis_phi'
        
        output_f = open("%s_avg.txt" % model.__class__.__name__,'w')    
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 30):
            q = 0.025*i_q
            sum = 0.0
            theta = 90.0
            
            model.setParam(theta_label, theta)
            
            for j in range(npts):
                model.setParam(phi_label, 180.0 / 2.0 / npts * j)
                if str(model.run([q, 0])).count("INF")>0:                        
                    print "ERROR", q, theta, 180.0 * 2.0 / npts * j
                #sum += math.sin(theta*math.pi/180.0)*model.run([q, 0])
                sum += math.sin(math.pi / 2.0 / npts * j)*model.run([q, 0])
                #sum += model.run([q, 0])
            
            value = sum/npts
            ana = model.run(q)
            if q<0.25 and (value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
        
    def test_non_oriented(self, model_class=SphereModel, points = 101):
        """ 
            Perform test and produce output file
            @param model_class: python class of the model to test
        """
        print "Averaging %s" % model_class.__name__
        passed = True
        
        npts =points
        model = model_class()
        #model.setParam('scale', 1.0)
        #model.setParam('contrast', 1.0)
        
        output_f = open("%s_avg.txt" % model.__class__.__name__,'w')    
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 30):
            q = 0.025*i_q
            sum = 0.0
            for i_theta in range(npts):
                theta = 180.0/npts*i_theta
                
                for j in range(npts):
                    if str(model.run([q, 0])).count("INF")>0:                        
                        print "ERROR", q, theta, 180.0 * 2.0 / npts * j
                    sum += math.sin(theta*math.pi/180.0)*model.run([q, 0])
            
            value = sum/npts/npts*math.pi/2.0
            ana = model.run(q)
            if q<0.25 and (value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
            
        
if __name__ == '__main__':
    validator = Validate2D()
    cyl_passed = validator(CylinderModel, points=201)
    ell_passed = validator(EllipsoidModel, points=501)
    cylcorehsell_passed = validator(CoreShellCylinderModel, points=201) 
    sph_passed = validator.test_non_oriented(SphereModel, points=211) 
        
    print ""
    print "Model             Passed"
    print "Cylinder          %s" % cyl_passed
    print "Ellipsoid         %s" % ell_passed
    print "Core-shell cyl    %s" % cylcorehsell_passed
    print "Sphere            %s" % sph_passed
        
        
  
    
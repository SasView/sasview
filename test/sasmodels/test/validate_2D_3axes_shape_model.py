#!/usr/bin/env python
""" 
    Class to validate a given 2D model w/ 3 axes by averaging it
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
    
    Note: 
        Averaging the 3-axes 2D scattering intensity give a slightly
        different output than the 1D function  
        at hight Q (Q>~0.2). This is due to the way the IGOR library 
        averages(?), taking only 76 points in alpha, the angle between
        the axis of the ellipsoid and the q vector.
        
    Note: Core-shell and sphere models are symmetric around
        all axes and don't need to be tested in the following way.
"""
import sys, math
from sas.models.EllipticalCylinderModel import EllipticalCylinderModel
from sas.models.ParallelepipedModel import ParallelepipedModel
from sas.models.TriaxialEllipsoidModel import TriaxialEllipsoidModel

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
                
    def __call__(self, model_class=EllipticalCylinderModel, points = 101):
        """ 
            Perform test and produce output file
            @param model_class: python class of the model to test
        """
        print "Averaging %s: Note; takes loooong time." % model_class.__name__
        passed = True
        
        npts =points
        #The average values are very sensitive to npts of phi so npts_alpha should be large enough.
        npts_alpha =180 #npts of phi
        model = model_class()
        #model.setParam('scale', 1.0)
        #model.setParam('contrast', 1.0)
        
        theta_label = 'cyl_theta'
        if not model.params.has_key(theta_label):
            theta_label = 'parallel_theta'
        if not model.params.has_key(theta_label):
            theta_label = 'axis_theta'
            
        phi_label = 'cyl_phi'
        if not model.params.has_key(phi_label):
            phi_label = 'parallel_phi'
        if not model.params.has_key(phi_label):
            phi_label = 'axis_phi'
            
        psi_label = 'cyl_psi'
        if not model.params.has_key(psi_label):
            psi_label = 'parallel_psi'
        if not model.params.has_key(psi_label):
            psi_label = 'axis_psi'
            
        output_f = open("%s_avg.txt" % model.__class__.__name__,'w')
        output_f.write("<q_average> <2d_average> <1d_average>\n")
            
        for i_q in range(1, 23):
            q = 0.01*i_q
            sum = 0.0
            weight = 0.0
            for i_theta in range(npts):
                theta = 180.0/npts*(i_theta+1)
                
                model.setParam(theta_label, theta)
                
                for j in range(npts_alpha):
                    model.setParam(phi_label, 180.0 * 2.0 / npts_alpha * j)
                    for k in range(npts):
                        model.setParam(psi_label, 180.0 * 2.0 / npts * k)
                        if str(model.run([q, 0])).count("INF")>0:                        
                            print "ERROR", q, theta, 180.0 * 2.0 / npts * k
                            
                        # sin() is due to having not uniform bin number density wrt the q plane.
                        sum += model.run([q, 0])*math.fabs(math.cos(theta*math.pi/180.0))
                        weight += math.fabs(math.cos(theta*math.pi/180.0) )

            value = sum/weight #*math.pi/2.0
            ana = model.run(q)
            if q<0.3 and (value-ana)/ana>0.05:
                passed = False
            output_f.write("%10g %10g %10g\n" % (q, value, ana))
            print "Q=%g: %10g %10g %10g %10g" % (q, value, ana, value-ana, value/ana)
        
        output_f.close()
        return passed
    
        
        
if __name__ == '__main__':
    validator = Validate2D()
    
    #Note: Test one model by one model, otherwise it could crash depending on the memory.
    
    te_passed =validator(TriaxialEllipsoidModel, points=76)
    #pp_passed = validator(ParallelepipedModel, points=76)
    #ell_passed = validator(EllipticalCylinderModel, points=76)
        
    print ""
    print "Model             Passed"
    print "TriaxialEllipsoid         %s" % te_passed
    #print "ParallelepipedModel    %s" % pp_passed
    #print "EllipticalCylinder        %s" % ell_passed
 
        
        
  
    

"""
    Module to perform P(r) inversion.
    The module contains the Invertor class.
"""
from sans.pr.core.pr_inversion import Cinvertor
import numpy
import sys

def help():
    """
        Provide general online help text
        Future work: extend this function to allow topic selection
    """
    info_txt  = "The inversion approach is based on Moore, J. Appl. Cryst. (1980) 13, 168-175.\n\n"
    info_txt += "P(r) is set to be equal to an expansion of base functions of the type "
    info_txt += "phi_n(r) = 2*r*sin(pi*n*r/D_max). The coefficient of each base functions "
    info_txt += "in the expansion is found by performing a least square fit with the "
    info_txt += "following fit function:\n\n"
    info_txt += "chi**2 = sum_i[ I_meas(q_i) - I_th(q_i) ]**2/error**2 + Reg_term\n\n"
    info_txt += "where I_meas(q) is the measured scattering intensity and I_th(q) is "
    info_txt += "the prediction from the Fourier transform of the P(r) expansion. "
    info_txt += "The Reg_term term is a regularization term set to the second derivative "
    info_txt += "d**2P(r)/dr**2 integrated over r. It is used to produce a smooth P(r) output.\n\n"
    info_txt += "The following are user inputs:\n\n"
    info_txt += "   - Number of terms: the number of base functions in the P(r) expansion.\n\n"
    info_txt += "   - Regularization constant: a multiplicative constant to set the size of "
    info_txt += "the regularization term.\n\n"
    info_txt += "   - Maximum distance: the maximum distance between any two points in the system.\n"
     
    return info_txt
    

class Invertor(Cinvertor):
    """
        Invertor class to perform P(r) inversion
        
        TODO: explain the maths
        
        
        Methods inherited from Cinvertor:
        - get_peaks(pars): returns the number of P(r) peaks
        - oscillations(pars): returns the oscillation parameters for the output P(r)
        - get_positive(pars): returns the fraction of P(r) that is above zero
        - get_pos_err(pars): returns the fraction of P(r) that is 1-sigma above zero
    """
    ## Chisqr of the last computation
    chi2  = 0
    ## Time elapsed for last computation
    elapsed = 0
    ## Alpha to get the reg term the same size as the signal
    suggested_alpha = 0
    ## Last number of base functions used
    nfunc = 0
    ## Last output values
    out = None
    ## Last errors on output values
    cov = None
    
    def __init__(self):
        Cinvertor.__init__(self)
        
    def __setattr__(self, name, value):
        """
            Set the value of an attribute.
            Access the parent class methods for
            x, y, err, d_max, q_min, q_max and alpha
        """
        if   name=='x':
            if 0.0 in value:
                raise ValueError, "Invertor: one of your q-values is zero. Delete that entry before proceeding"
            return self.set_x(value)
        elif name=='y':
            return self.set_y(value)
        elif name=='err':
            return self.set_err(value)
        elif name=='d_max':
            return self.set_dmax(value)
        elif name=='q_min':
            if value==None:
                return self.set_qmin(-1.0)
            return self.set_qmin(value)
        elif name=='q_max':
            if value==None:
                return self.set_qmax(-1.0)
            return self.set_qmax(value)
        elif name=='alpha':
            return self.set_alpha(value)
            
        return Cinvertor.__setattr__(self, name, value)
    
    def __getattr__(self, name):
        """
           Return the value of an attribute
           For the moment x, y, err and d_max are write-only
           TODO: change that!
        """
        import numpy
        if   name=='x':
            out = numpy.ones(self.get_nx())
            self.get_x(out)
            return out
        elif name=='y':
            out = numpy.ones(self.get_ny())
            self.get_y(out)
            return out
        elif name=='err':
            out = numpy.ones(self.get_nerr())
            self.get_err(out)
            return out
        elif name=='d_max':
            return self.get_dmax()
        elif name=='q_min':
            qmin = self.get_qmin()
            if qmin<0:
                return None
            return qmin
        elif name=='q_max':
            qmax = self.get_qmax()
            if qmax<0:
                return None
            return qmax
        elif name=='alpha':
            return self.get_alpha()
        elif name in self.__dict__:
            return self.__dict__[name]
        return None
    
    def clone(self):
        """
            Return a clone of this instance
        """
        invertor = Invertor()
        invertor.chi2    = self.chi2 
        invertor.elapsed = self.elapsed 
        invertor.alpha   = self.alpha
        invertor.d_max   = self.d_max
        invertor.q_min   = self.q_min
        invertor.q_max   = self.q_max
        
        invertor.x = self.x
        invertor.y = self.y
        invertor.err = self.err
        
        return invertor
    
    def invert(self, nfunc=5):
        """
            Perform inversion to P(r)
        """
        from scipy import optimize
        import time
        
        self.nfunc = nfunc
        # First, check that the current data is valid
        if self.is_valid()<=0:
            raise RuntimeError, "Invertor.invert: Data array are of different length"
        
        p = numpy.ones(nfunc)
        t_0 = time.time()
        out, cov_x, info, mesg, success = optimize.leastsq(self.residuals, p, full_output=1, warning=True)
        
        # Compute chi^2
        res = self.residuals(out)
        chisqr = 0
        for i in range(len(res)):
            chisqr += res[i]
        
        self.chi2 = chisqr

        # Store computation time
        self.elapsed = time.time() - t_0
        
        return out, cov_x
    
    def pr_fit(self, nfunc=5):
        """
            Perform inversion to P(r)
        """
        from scipy import optimize
        
        # First, check that the current data is valid
        if self.is_valid()<=0:
            raise RuntimeError, "Invertor.invert: Data arrays are of different length"
        
        p = numpy.ones(nfunc)
        t_0 = time.time()
        out, cov_x, info, mesg, success = optimize.leastsq(self.pr_residuals, p, full_output=1, warning=True)
        
        # Compute chi^2
        res = self.pr_residuals(out)
        chisqr = 0
        for i in range(len(res)):
            chisqr += res[i]
        
        self.chisqr = chisqr
        
        # Store computation time
        self.elapsed = time.time() - t_0

        return out, cov_x
    
    def pr_err(self, c, c_cov, r):
        """    
            Returns the value of P(r) for a given r, and base function
            coefficients, with error.
            
            @param c: base function coefficients
            @param c_cov: covariance matrice of the base function coefficients
            @param r: r-value to evaluate P(r) at
            @return: P(r)
            
        """
        return self.get_pr_err(c, c_cov, r)
       
    def _accept_q(self, q):
        """
            Check q-value against user-defined range
        """
        if not self.q_min==None and q<self.q_min:
            return False
        if not self.q_max==None and q>self.q_max:
            return False
        return True
       
    def lstsq(self, nfunc=5):
        #TODO: do this on the C side
        #
        # To make sure an array is contiguous:
        # blah = numpy.ascontiguousarray(blah_original)
        # ... before passing it to C
        """
            TODO: Document this
        """
        import math
        from scipy.linalg.basic import lstsq
        
        self.nfunc = nfunc
        # a -- An M x N matrix.
        # b -- An M x nrhs matrix or M vector.
        npts = len(self.x)
        nq   = 20
        sqrt_alpha = math.sqrt(self.alpha)
        
        a = numpy.zeros([npts+nq, nfunc])
        b = numpy.zeros(npts+nq)
        err = numpy.zeros(nfunc)
        
        for j in range(nfunc):
            for i in range(npts):
                if self._accept_q(self.x[i]):
                    a[i][j] = self.basefunc_ft(self.d_max, j+1, self.x[i])/self.err[i]
            for i_q in range(nq):
                r = self.d_max/nq*i_q
                #a[i_q+npts][j] = sqrt_alpha * 1.0/nq*self.d_max*2.0*math.fabs(math.sin(math.pi*(j+1)*r/self.d_max) + math.pi*(j+1)*r/self.d_max * math.cos(math.pi*(j+1)*r/self.d_max))     
                a[i_q+npts][j] = sqrt_alpha * 1.0/nq*self.d_max*2.0*(2.0*math.pi*(j+1)/self.d_max*math.cos(math.pi*(j+1)*r/self.d_max) + math.pi**2*(j+1)**2*r/self.d_max**2 * math.sin(math.pi*(j+1)*r/self.d_max))     
        
        for i in range(npts):
            if self._accept_q(self.x[i]):
                b[i] = self.y[i]/self.err[i]
            
        c, chi2, rank, n = lstsq(a, b)
        self.chi2 = chi2
                
        at = numpy.transpose(a)
        inv_cov = numpy.zeros([nfunc,nfunc])
        for i in range(nfunc):
            for j in range(nfunc):
                inv_cov[i][j] = 0.0
                for k in range(npts):
                    if self._accept_q(self.x[i]):
                        inv_cov[i][j] = at[i][k]*a[k][j]
                    
        # Compute the reg term size for the output
        sum_sig = 0.0
        sum_reg = 0.0
        for j in range(nfunc):
            for i in range(npts):
                if self._accept_q(self.x[i]):
                    sum_sig += (a[i][j])**2
            for i in range(nq):
                sum_reg += (a[i+npts][j])**2
                    
        if math.fabs(self.alpha)>0:
            new_alpha = sum_sig/(sum_reg/self.alpha)
        else:
            new_alpha = 0.0
        self.suggested_alpha = new_alpha
        
        try:
            err = math.fabs(chi2/(npts-nfunc))* inv_cov
        except:
            print "Error estimating uncertainties"
            
        # Keep a copy of the last output
        self.out = c
        self.cov = err
        
        return c, err
        
    def svd(self, nfunc=5):
        import math, time
        # Ac - b = 0
        
        A = numpy.zeros([nfunc, nfunc])
        y = numpy.zeros(nfunc)
        
        t_0 = time.time()
        for i in range(nfunc):
            # A
            for j in range(nfunc):
                A[i][j] = 0.0
                for k in range(len(self.x)):
                    err = self.err[k]
                    A[i][j] += 1.0/err/err*self.basefunc_ft(self.d_max, j+1, self.x[k]) \
                            *self.basefunc_ft(self.d_max, i+1, self.x[k]);
                #print A[i][j]
                #A[i][j] -= self.alpha*(math.cos(math.pi*(i+j)) - math.cos(math.pi*(i-j)));
                if i==j:
                    A[i][j] += -1.0*self.alpha
                elif i-j==1 or i-j==-1:
                    A[i][j] += 1.0*self.alpha
                #print "   ",A[i][j]
            # y
            y[i] = 0.0
            for k in range(len(self.x)):
                y[i] = self.y[k]/self.err[k]/self.err[k]*self.basefunc_ft(self.d_max, i+1, self.x[k])
            
        print time.time()-t_0, 'secs'
        
        # use numpy.pinv(A)
        #inv_A = numpy.linalg.inv(A)
        #c = y*inv_A
        print y
        c = numpy.linalg.solve(A, y)
        
        
        print c
        
        err = numpy.zeros(len(c))
        return c, err
        
    def estimate_alpha(self, nfunc):
        """
            Returns a reasonable guess for the
            regularization constant alpha
            
            @return: alpha, message, elapsed
            
            where alpha is the estimate for alpha,
            message is a message for the user,
            elapsed is the computation time
        """
        import time
        try:            
            pr = self.clone()
            
            # T_0 for computation time
            starttime = time.time()
            
            # If the current alpha is zero, try
            # another value
            if pr.alpha<=0:
                pr.alpha = 0.0001
                 
            # Perform inversion to find the largest alpha
            out, cov = pr.lstsq(nfunc)
            elapsed = time.time()-starttime
            initial_alpha = pr.alpha
            initial_peaks = pr.get_peaks(out)
    
            # Try the inversion with the estimated alpha
            pr.alpha = pr.suggested_alpha
            out, cov = pr.lstsq(nfunc)
    
            npeaks = pr.get_peaks(out)
            # if more than one peak to start with
            # just return the estimate
            if npeaks>1:
                message = "Your P(r) is not smooth, please check your inversion parameters"
                return pr.suggested_alpha, message, elapsed
            else:
                
                # Look at smaller values
                # We assume that for the suggested alpha, we have 1 peak
                # if not, send a message to change parameters
                alpha = pr.suggested_alpha
                best_alpha = pr.suggested_alpha
                found = False
                for i in range(10):
                    pr.alpha = (0.33)**(i+1)*alpha
                    out, cov = pr.lstsq(nfunc)
                    
                    peaks = pr.get_peaks(out)
                    print pr.alpha, peaks
                    if peaks>1:
                        found = True
                        break
                    best_alpha = pr.alpha
                    
                # If we didn't find a turning point for alpha and
                # the initial alpha already had only one peak,
                # just return that
                if not found and initial_peaks==1 and initial_alpha<best_alpha:
                    best_alpha = initial_alpha
                    
                # Check whether the size makes sense
                message=''
                
                if not found:
                    message = "None"
                elif best_alpha>=0.5*pr.suggested_alpha:
                    # best alpha is too big, return a 
                    # reasonable value
                    message  = "The estimated alpha for your system is too large. "
                    message += "Try increasing your maximum distance."
                
                return best_alpha, message, elapsed
    
        except:
            message = "Invertor.estimate_alpha: %s" % sys.exc_value
            return 0, message, elapsed
    
        
    def to_file(self, path, npts=100):
        """
            Save the state to a file that will be readable
            by SliceView.
            @param path: path of the file to write
            @param npts: number of P(r) points to be written
        """
        import pylab
        
        file = open(path, 'w')
        file.write("#d_max=%g\n" % self.d_max)
        file.write("#nfunc=%g\n" % self.nfunc)
        file.write("#alpha=%g\n" % self.alpha)
        file.write("#chi2=%g\n" % self.chi2)
        file.write("#elapsed=%g\n" % self.elapsed)
        file.write("#alpha_estimate=%g\n" % self.suggested_alpha)
        if not self.out==None:
            if len(self.out)==len(self.cov):
                for i in range(len(self.out)):
                    file.write("#C_%i=%s+-%s\n" % (i, str(self.out[i]), str(self.cov[i][i])))
        file.write("<r>  <Pr>  <dPr>\n")
        r = pylab.arange(0.0, self.d_max, self.d_max/npts)
        
        for r_i in r:
            (value, err) = self.pr_err(self.out, self.cov, r_i)
            file.write("%g  %g  %g\n" % (r_i, value, err))
    
        file.close()
     
        
    def from_file(self, path):
        """
            Load the state of the Invertor from a file,
            to be able to generate P(r) from a set of
            parameters.
            @param path: path of the file to load
        """
        import os
        import re
        if os.path.isfile(path):
            try:
                fd = open(path, 'r')
                
                buff    = fd.read()
                lines   = buff.split('\n')
                for line in lines:
                    if line.startswith('#d_max='):
                        toks = line.split('=')
                        self.d_max = float(toks[1])
                    elif line.startswith('#nfunc='):
                        toks = line.split('=')
                        self.nfunc = int(toks[1])
                        self.out = numpy.zeros(self.nfunc)
                        self.cov = numpy.zeros([self.nfunc, self.nfunc])
                    elif line.startswith('#alpha='):
                        toks = line.split('=')
                        self.alpha = float(toks[1])
                    elif line.startswith('#chi2='):
                        toks = line.split('=')
                        self.chi2 = float(toks[1])
                    elif line.startswith('#elapsed='):
                        toks = line.split('=')
                        self.elapsed = float(toks[1])
                    elif line.startswith('#alpha_estimate='):
                        toks = line.split('=')
                        self.suggested_alpha = float(toks[1])
            
                    # Now read in the parameters
                    elif line.startswith('#C_'):
                        toks = line.split('=')
                        p = re.compile('#C_([0-9]+)')
                        m = p.search(toks[0])
                        toks2 = toks[1].split('+-')
                        i = int(m.group(1))
                        self.out[i] = float(toks2[0])
                        
                        self.cov[i][i] = float(toks2[1])                        
            
            except:
                raise RuntimeError, "Invertor.from_file: corrupted file\n%s" % sys.exc_value
        else:
            raise RuntimeError, "Invertor.from_file: '%s' is not a file" % str(path) 
        
        
    
    
if __name__ == "__main__":
    o = Invertor()

    
    
    
    

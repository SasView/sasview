from sans.pr.core.pr_inversion import Cinvertor
import numpy

class Invertor(Cinvertor):
    
    ## Chisqr of the last computation
    chi2  = 0
    ## Time elapsed for last computation
    elapsed = 0
    
    def __init__(self):
        Cinvertor.__init__(self)
        
    def __setattr__(self, name, value):
        """
            Set the value of an attribute.
            Access the parent class methods for
            x, y, err and d_max.
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
        import math
        c_err = numpy.zeros(len(c))
        for i in range(len(c)):
            try:
                c_err[i] = math.sqrt(math.fabs(c_cov[i][i]))
            except:
                import sys
                print sys.exc_value
                print "oups", c_cov[i][i]
                c_err[i] = c[i]

        return self.get_pr_err(c, c_err, r)
       
    def lstsq(self, nfunc=5):
        import math
        from scipy.linalg.basic import lstsq
        
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
                a[i][j] = self.basefunc_ft(self.d_max, j+1, self.x[i])/self.err[i]
            for i_q in range(nq):
                r = self.d_max/nq*i_q
                #a[i_q+npts][j] = sqrt_alpha * 1.0/nq*self.d_max*2.0*math.fabs(math.sin(math.pi*(j+1)*r/self.d_max) + math.pi*(j+1)*r/self.d_max * math.cos(math.pi*(j+1)*r/self.d_max))     
                a[i_q+npts][j] = sqrt_alpha * 1.0/nq*self.d_max*2.0*(2.0*math.pi*(j+1)/self.d_max*math.cos(math.pi*(j+1)*r/self.d_max) + math.pi**2*(j+1)**2*r/self.d_max**2 * math.sin(math.pi*(j+1)*r/self.d_max))     
        
        for i in range(npts):
            b[i] = self.y[i]/self.err[i]
            
        c, chi2, rank, n = lstsq(a, b)
        self.chi2 = chi2
                
        at = numpy.transpose(a)
        inv_cov = numpy.zeros([nfunc,nfunc])
        for i in range(nfunc):
            for j in range(nfunc):
                inv_cov[i][j] = 0.0
                for k in range(npts):
                    inv_cov[i][j] = at[i][k]*a[k][j]
                    
        # Compute the reg term size for the output
        sum_sig = 0.0
        sum_reg = 0.0
        for j in range(nfunc):
            for i in range(npts):
                sum_sig += (a[i][j])**2
            for i in range(nq):
                sum_reg += (a[i_q+npts][j])**2
                    
        new_alpha = sum_sig/(sum_reg/self.alpha)
        print "Suggested alpha =", 0.1*new_alpha
        
        try:
            err = math.fabs(chi2/(npts-nfunc))* inv_cov
        except:
            print "Error estimating uncertainties"
            
        
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
        
        
        
        
    
if __name__ == "__main__":
    o = Invertor()

    
    
    
    

import math
import pylab, numpy

class PrInverse:
    
    D = 70.0
    #alpha = 0.0001
    alpha = 0.0
    
    data_x   = []
    data_y   = []
    data_err = []
    
    r = []
    pr = []
    pr_err = []
    
    xmult = []
    
    c = None
    
    def __init__(self, D=60.0):
        ## Max distance
        self.D = D
        self.xmult = pylab.arange(0.001, self.D, self.D/21.0)

    def l_multiplier(self, c):
        return self.alpha * self._lmult2(c)
        
    def _lmult1(self, c):
        sum = 0
        for i in range(len(c)-1):
            sum += (c[i+1]-c[i])**2
        return sum
    
    def _lmult2(self, c):
        sum = 0
        for i in range(len(self.xmult)):
            dp = 0
            for j in range(len(c)):
                dp += c[j] * self._ortho_derived(j+1, self.xmult[i])
            sum += (dp**2)
        return sum * self.D/len(self.xmult)
    
    def _ortho_transformed(self, n, q):
        """
            Fourier transform of the nth orthogonal function
        """
        return 8.0*math.pi**2/q * self.D * n * (-1)**(n+1) * \
            math.sin(q*self.D) / ( (math.pi*n)**2 - (q*self.D)**2)
            
    def _ortho_derived(self, n, r):
        
        return 2.0*math.sin(math.pi*n*r/self.D) + 2.0*r*math.cos(math.pi*n*r/self.D)  
    
    def iq(self, c, q):
        sum = 0.0
        N = len(c)
        #str =  ''
        for i in range(N):
            # n goes from 1 to N in the formulas
            sum += c[i] * self._ortho_transformed(i+1, q)
            #str += "c%i=%g  " % (i, c[i]);
        #print str
        #import time
        #time.sleep(10)
        return sum
    
    def residuals(self, params):
        """
            Calculates the vector of residuals for each point 
            in y for a given set of input parameters.
            @param params: list of parameter values
            @return: vector of residuals
        """
        residuals = []
        M = len(self.data_x)
        #lmult = self.l_multiplier(params)
        lmult = 0
        for j in range(M):
            if self.data_x[j]>0.0:
                #print j
                value = (self.data_y[j] - self.iq(params, self.data_x[j]))**2 / self.data_err[j]**2
                #print self.data_x[j], value, lmult/float(M)
                value += lmult/float(M)
                residuals.append( value )
            
        return residuals
    
    def convert_res(self, res):
        v = numpy.asarray(res)
        if not v.flags.contiguous:
            print "not contiguous" 
            v = numpy.array(res)
        
        print v
        res = self.c.residuals(v)
        print res
        #return self.c.residuals(v)
        return res
    
    def new_fit(self):
        from sans.pr.invertor import Invertor
        from scipy import optimize
        
        c = Invertor()
        c.set_dmax(self.D)
        c.set_x(self.data_x)
        c.set_y(self.data_y)
        c.set_err(self.data_err)
        
        out, cov_x = c.invert()
        
        return out, cov_x

    def new_fit_0(self):
        from sans.pr.core.pr_inversion import Cinvertor
        from scipy import optimize
        
        self.c = Cinvertor()
        self.c.set_dmax(self.D)
        self.c.set_x(self.data_x)
        self.c.set_y(self.data_y)
        self.c.set_err(self.data_err)
        print "Valid", self.c.is_valid()
        M=10
        p = numpy.ones(M)
        
        p[0] = 10.0
        
        out, cov_x, info, mesg, success = optimize.leastsq(self.c.residuals, p, full_output=1, warning=True)
        #out, cov_x, info, mesg, success = optimize.leastsq(self.convert_res, p, full_output=1, warning=True)
        
        
        return out, cov_x
    
    def fit(self):
        return self.new_fit()
        
        import numpy
        from scipy import optimize


        M = len(self.data_x)-3
        M=3
        print "Number of functions: ", M
        p = numpy.zeros(M)
        p[0] = 1000.0
        
        out, cov_x, info, mesg, success = optimize.leastsq(self.residuals, p, full_output=1, warning=True)
        
        
        return out, cov_x

    def pr_theory(self, r, R):
        """
           
        """
        if r<=2*R:
            return 12.0* ((0.5*r/R)**2) * ((1.0-0.5*r/R)**2) * ( 2.0 + 0.5*r/R )
        else:
            return 0.0


    def residuals_pr(self, params):
        import pylab
        
        residuals = []
        M = len(self.r)
        
        
        for j in range(M):
            
            if self.r[j]>0:
                err2 = (self.pr_err[j])**2
                if j>0:
                    err2 += 0.25*(self.pr[j-1]-self.pr[j-1])**2
                value = (self.pr[j]-self.pr_calc(params, self.r[j]))**2/err2
                residuals.append( value )
            
        return residuals        

    def pr_calc(self, c, r):
        sum = 0
        N = len(c)
        for i in range(N):
            sum += c[i]*2.0*r*math.sin(math.pi*(i+1)*r/self.D)
            
        return sum

    def fill_sphere(self, radius=60):
        import pylab
        import numpy
        self.r = pylab.arange(0.0, radius, radius/50.0)
        M = len(self.r)
        self.pr = numpy.zeros(M)
        self.pr_err = numpy.zeros(M)
        
        for j in range(M):
            self.pr[j] = self.pr_theory(self.r[j], radius)
            self.pr_err[j] = math.sqrt(self.pr[j])
        

    def fit_pr(self):
        import numpy
        from scipy import optimize
        
        
        M = len(self.r)-3
        M=2
        print "Number of functions: ", M
        p = numpy.ones(M)
        #p = numpy.ones(15)
        
        out, cov_x, info, mesg, success = optimize.leastsq(self.residuals_pr, p, full_output=1, warning=True)
      
        return out, cov_x
        
        

    def load(self, path = "sphere_test_data.txt"):
        # Read the data from the data file
        self.data_x = numpy.zeros(0)
        self.data_y = numpy.zeros(0)
        self.data_err = numpy.zeros(0)
        if not path == None:
            input_f = open(path,'r')
            buff = input_f.read()
            lines = buff.split('\n')
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    self.data_x = numpy.append(self.data_x, x)
                    self.data_y = numpy.append(self.data_y, y)
                    self.data_err = numpy.append(self.data_err, math.sqrt(y)+1000.0)
                except:
                    print "Error reading line: ", line
                   
        print "Lines read:", len(self.data_x)
        

if __name__ == "__main__": 
    from sans.pr.core.pr_inversion import Cinvertor
    pr = PrInverse()
    pr.load("sphere_80.txt")
    out, cov = pr.fit()
    
    print "output:"
    print out
    
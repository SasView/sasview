from sans.pr.core.pr_inversion import Cinvertor
import numpy

class Invertor(Cinvertor):
    
    def __init__(self):
        Cinvertor.__init__(self)
        
    def __setattr__(self, name, value):
        """
            Set the value of an attribute.
            Access the parent class methods for
            x, y, err and d_max.
        """
        if   name=='x':
            return self.set_x(value)
        elif name=='y':
            return self.set_y(value)
        elif name=='err':
            return self.set_err(value)
        elif name=='d_max':
            return self.set_dmax(value)
            
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
        elif name in self.__dict__:
            return self.__dict__[name]
        return None
    
    def invert(self, nfunc=5):
        """
            Perform inversion to P(r)
        """
        from scipy import optimize
        
        # First, check that the current data is valid
        if self.is_valid()<=0:
            raise RuntimeError, "Invertor.invert: Data array are of different length"
        
        p = numpy.ones(nfunc)
        out, cov_x, info, mesg, success = optimize.leastsq(self.residuals, p, full_output=1, warning=True)
        
        return out, cov_x
    
if __name__ == "__main__":
    o = Invertor()

    
    
    
    

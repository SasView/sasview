from __future__ import print_function

"""
    Generate two correlated sets of data
        1- A line: y = ax + b
        2- A constant equal to a of set #1
        
"""

def get_x(x, y=0, dx=0, dy=0):
    return x

def get_err_x(x, y=0, dx=0, dy=0):
    return dx


class Generator:
    ## Parameter A
    constant_a = 2.5
    ## Parameter B
    constant_b = 4.0
    ## Randomness factor
    randomness = 0.07
    
    def __init__(self):
        pass
    
    def create(self, filename, xmin=0.01, xmax=10.0, npts=50, 
               xfunc=get_x, yfunc=get_x, errfunc=get_err_x):
        """
            Create files with the generate data
            The file names will be:
                - Set #1: [filename]_line.txt
                - Set #2: [filename]_cst.txt
                
            @param filename: string to prepend to the file name
            @param xmin: minimum x-value
            @param xmax: maximum x-value
            @param npts: number of points to generate
        """
        import random, time
        random.seed(time.time())
        
        # Write line data set
        fd = open(filename, 'w')
        print("Creating ", filename)
        fd.write("#y=A*x+B\n#A=%g\n#B=%g\n" % (self.constant_a, self.constant_b))
        
        for i in range(npts):
            x = xmin+(xmax-xmin)/(npts-1)*i
            mu = self.constant_a*x+self.constant_b
            err = self.randomness*mu
            y = random.gauss(mu, err)
            fd.write("%g  %g  %g\n" % (xfunc(x, y), yfunc(y, xfunc(x, 0)), errfunc(y, xfunc(x,y), err, 0)))
            
        fd.close()
        
        
        

if __name__ == "__main__": 
    from test_transfo import *
    gen = Generator()
    
    # Linear x series
    gen.create("linear.txt")
    gen.create("x_y2.txt", yfunc=from_x2, errfunc=err_x2)
    gen.create("x_inv_y.txt", yfunc=from_inv_x, errfunc=err_inv_x)
    gen.create("x_inv_sqrty.txt", yfunc=from_inv_sqrtx, errfunc=err_inv_sqrtx)
    gen.create("x_lny.txt", xmin=0.0001, xmax=3.0, yfunc=from_lnx, errfunc=err_lnx)
    gen.create("x_logy.txt", xmin=0.0001, xmax=3.0, yfunc=from_log10, errfunc=err_log10)
    gen.create("x_lnxy.txt", yfunc=from_lnxy, errfunc=err_lnxy)
    gen.create("x_lnyx2.txt", xmin=0.0001, xmax=10.0, yfunc=from_lnx2y, errfunc=err_lnx2y)
    gen.create("x_lnyx4.txt", xmin=0.0001, xmax=10.0, yfunc=from_lnx4y, errfunc=err_lnx4y)
    
    # Log10(x)
    gen.create("logx_y.txt", xmax=3.0, xfunc=from_log10)
    gen.create("logx_y2.txt", xmax=3.0, xfunc=from_log10, yfunc=from_x2, errfunc=err_x2)
    gen.create("logx_inv_y.txt", xmax=3.0, xfunc=from_log10, yfunc=from_inv_x, errfunc=err_inv_x)
    gen.create("logx_inv_sqrty.txt", xmax=3.0, xfunc=from_log10, yfunc=from_inv_sqrtx, errfunc=err_inv_sqrtx)
    gen.create("logx_lny.txt", xfunc=from_log10, xmin=0.0001, xmax=3.0, yfunc=from_lnx, errfunc=err_lnx)
    gen.create("logx_logy.txt", xfunc=from_log10, xmin=0.0001, xmax=3.0, yfunc=from_log10, errfunc=err_log10)
    gen.create("logx_lnxy.txt", xfunc=from_log10, yfunc=from_lnxy, errfunc=err_lnxy)
    gen.create("logx_lnyx2.txt", xfunc=from_log10, xmin=0.0001, xmax=10.0, yfunc=from_lnx2y, errfunc=err_lnx2y)
    gen.create("logx_lnyx4.txt", xfunc=from_log10, xmin=0.0001, xmax=10.0, yfunc=from_lnx4y, errfunc=err_lnx4y)
    
    # x^2
    gen.create("x2_y.txt", xfunc=from_x2)
    gen.create("x2_y2.txt", xfunc=from_x2, yfunc=from_x2, errfunc=err_x2)
    gen.create("x2_inv_y.txt", xfunc=from_x2, yfunc=from_inv_x, errfunc=err_inv_x)
    gen.create("x2_inv_sqrty.txt", xfunc=from_x2, yfunc=from_inv_sqrtx, errfunc=err_inv_sqrtx)
    gen.create("x2_lny.txt", xfunc=from_x2, xmin=0.0001, xmax=3.0, yfunc=from_lnx, errfunc=err_lnx)
    gen.create("x2_logy.txt", xfunc=from_x2, xmin=0.0001, xmax=3.0, yfunc=from_log10, errfunc=err_log10)
    gen.create("x2_lnxy.txt", xfunc=from_x2, yfunc=from_lnxy, errfunc=err_lnxy)
    gen.create("x2_lnyx2.txt", xfunc=from_x2, xmin=0.0001, xmax=10.0, yfunc=from_lnx2y, errfunc=err_lnx2y)
    gen.create("x2_lnyx4.txt", xfunc=from_x2, xmin=0.0001, xmax=10.0, yfunc=from_lnx4y, errfunc=err_lnx4y)

            
            
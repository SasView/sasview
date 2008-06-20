"""
    Generate two correlated sets of data
        1- A line: y = ax + b
        2- A constant equal to a of set #1
        
"""

class Generator:
    ## Parameter A
    constant_a = 2.5
    ## Parameter B
    constant_b = 4.0
    ## Randomness factor
    randomness = 0.15
    
    def __init__(self):
        pass
    
    def create(self, filename, xmin=0.0, xmax=10.0, npts=50):
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
        fd = open(filename+'_line.txt', 'w')
        fd.write("#y=A*x+B\n#A=%g\n#B=%g\n" % (self.constant_a, self.constant_b))
        
        for i in range(npts):
            x = xmin+(xmax-xmin)/(npts-1)*i
            mu = self.constant_a*x+self.constant_b
            err = self.randomness*mu
            y = random.gauss(mu, err)
            fd.write("%g  %g  %g\n" % (x,y,err))
            
        fd.close()
        
        # Write constant data set
        fd = open(filename+'_cst.txt', 'w')
        fd.write("#y=A\n#A=%g\n" % self.constant_a)
        
        for i in range(npts):
            x = xmin+(xmax-xmin)/(npts-1)*i
            err = self.randomness*self.constant_a
            y = random.gauss(self.constant_a, err)
            fd.write("%g  %g  %g\n" % (x,y,err))
            
        fd.close()
        
        

if __name__ == "__main__": 
    gen = Generator()
    gen.create("testdata")
    print "Files created"

            
            
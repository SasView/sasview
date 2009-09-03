"""
    This module is responsible to compute invariant related computation.
    @author: Gervaise B. Alina/UTK
"""
import numpy
class InvariantCalculator(object):
    """
        Compute invariant 
    """
    def __init__(self):
        """
            Initialize variables
        """
        self.x =[]
        self.y =[]
        self.dxl = None
        
    def setData(self, x=[], y=[], dxl=None):
        """
            set the data 
        """
        tempx = numpy.array(x)
        tempy = numpy.array(y)
        #Make sure data is order before computing
        ind = numpy.lexsort((tempy,tempx))
        self.x = tempx[ind]
        self.y = tempy[ind]
        if dxl !=None:
            tempdxl= numpy.array(dxl)
            self.dxl= tempdxl[ind]
        else:
            self.dxl=dxl
      
    
    def computeInvariant(self):
        """
            Compute invariant
        """
        if len(self.x)<=1 or len(self.y)<=1 or len(self.x)!=len(self.y):
            msg=  "Length x and y must be equal"
            msg +=" and greater than 1; got x=%s, y=%s"%(len(self.x),len(self.y))
            raise ValueError,msg
        elif len(self.x)==1 and len(self.y)==1:
            return 0
    
        else:
            n= len(self.x)-1
            #compute the first delta
            dx0= self.x[1]- self.x[0]
            #compute the last delta
            dxn= self.x[n]- self.x[n-1]
            sum = 0
            sum += self.x[0]* self.x[0]* self.y[0]*dx0
            sum += self.x[n]* self.x[n]* self.y[n]*dxn
            if len(self.x)==2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (self.x[i+1] - self.x[i-1])/2
                    sum += self.x[i]*self.x[i]* self.y[i]* dxi
                return sum
            
               
    def computeSmearInvariant(self):
        """
            Compute invariant with smearing info
        """
        if self.dxl ==None:
            msg = "Cannot compute Smear invariant dxl "
            msg +="must be a list, got dx= %s"%str(self.dxl)
            raise ValueError,msg

        if len(self.x)<=1 or len(self.y)<=1 or len(self.x)!=len(self.y)\
                or len(self.x)!= len(self.dxl):
            msg=  "Length x and y must be equal"
            msg +=" and greater than 1; got x=%s, y=%s"%(len(self.x),len(self.y))
            raise ValueError,msg
        else:
            n= len(self.x)-1
            #compute the first delta
            dx0= self.x[1]- self.x[0]
            #compute the last delta
            dxn= self.x[n]- self.x[n-1]
            sum = 0
            sum += self.x[0]* self.dxl[0]* self.y[0]*dx0
            sum += self.x[n]* self.dxl[n]* self.y[n]*dxn
            if len(self.x)==2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (self.x[i+1] - self.x[i-1])/2
                    sum += self.x[i]*self.dxl[i]* self.y[i]* dxi
                return sum
            
if __name__=="__main__":
    # test the module
    x=[1,2,3,4,10]
    y=[2,3,4,5,6]
   
    I= InvariantCalculator()
    I.setData(x=x, y=y)
    invariant = I.computeInvariant()
    print "1-Invariant : ", invariant
    
    x=[0,1]
    y=[0,2]
    I.setData(x=x, y=y)
    invariant = I.computeInvariant()
    print "2-Invariant : ", invariant
    
    x=[1,3,4,10,2]
    y=[2,4,5,6,3]
    I.setData(x=x, y=y)
    invariant = I.computeInvariant()
    print "3-Invariant : ", invariant
    
    # compute invariant with smear information
    from sans.guiframe.dataFitting import Data1D
    data1= Data1D(x=x,y=y )
    data1.dxl =[0.1,0.1,0.1,0.1,0.1]
   
    I.setData(x= data1.x, y= data1.y, dxl=data1.dxl)
    invariant = I.computeSmearInvariant()
    print "4-Smear Invariant:", invariant
    I.setData(x= data1.x, y= data1.y)
    try:
        invariant = I.computeSmearInvariant()
    except:
        print "5-Smear Invariant error for dxl=None"
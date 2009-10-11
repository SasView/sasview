"""
    This module is responsible to compute invariant related computation.
    @author: Gervaise B. Alina/UTK
"""

import math 
from DataLoader.data_info import Data1D as LoaderData1D
class InvariantCalculator(object):
    """
        Compute invariant if data is given.
        Can provide volume fraction and surface area if the user provides
        Porod constant  and contrast values.
        @precondition:  the user must send a data of type DataLoader.Data1D
        @note: The data boundaries are assumed as infinite range. 
    """
    def __init__(self, data,contrast=None, pConst=None):
        """
            Initialize variables
            @param data: data must be of type DataLoader.Data1D
            @param contrast: contrast value of type float
            @param pConst: Porod Constant of type float
        """
        self.q_star = self.getQstar(data= data)
        self.volume = self._getVolFrac(contrast= contrast)
        self.surface= self._getSurface(pConst= pConst)
        
    def __call__(self, contrast, pConst):
        """
            @precondition: self.q_star has already been computed
        """
        self.volume = self._getVolFrac(contrast= contrast)
        self.surface = self._getSurface(pConst= pConst)
        
        return self
        
    def getQstar(self, data):
        """
            @param data: data of type Data1D
            @return invariant value
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError,"Data must be of type DataLoader.Data1D"
        if data.dxl == None:
            return self._getQStarUnsmear(data= data)
        else:
            return self._getQStarSmear(data= data)
    
            
            
    def _getQStarUnsmear(self, data):
        """
            @param data: data of type Data1D
            Compute invariant given by
            q_star= x0**2 *y0 *dx0 +x1**2 *y1 *dx1 + ..+ xn**2 *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x1 - x0
            dxn = xn - xn-1
        """
        if len(data.x)<=1 or len(data.y)<=1 or len(data.x)!=len(data.y):
            msg=  "Length x and y must be equal"
            msg +=" and greater than 1; got x=%s, y=%s"%(len(data.x),
                                                         len(data.y))
            raise ValueError,msg
        elif len(data.x)==1 and len(data.y)==1:
            return 0
    
        else:
            n= len(data.x)-1
            #compute the first delta
            dx0= data.x[1]- data.x[0]
            #compute the last delta
            dxn= data.x[n]- data.x[n-1]
            sum = 0
            sum += data.x[0]* data.x[0]* data.y[0]*dx0
            sum += data.x[n]* data.x[n]* data.y[n]*dxn
            if len(data.x)==2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += data.x[i]*data.x[i]* data.y[i]* dxi
                return sum
            
               
    def _getQStarSmear(self, data):
        """
            @param data: data of type Data1D
            Compute invariant with smearing info
            q_star= x0*dxl *y0 *dx0 + x1*dxl *y1 *dx1 + ..+ xn*dxl *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x1 - x0
            dxn = xn - xn-1
            dxl: slit smearing value
        """
        if data.dxl ==None:
            msg = "Cannot compute Smear invariant dxl "
            msg +="must be a list, got dx= %s"%str(data.dxl)
            raise ValueError,msg

        if len(data.x)<=1 or len(data.y)<=1 or len(data.x)!=len(data.y)\
                or len(data.x)!= len(data.dxl):
           
            msg = "x, dxl, and y must be have the same length and greater than 1"
            raise ValueError,msg
        else:
            n= len(data.x)-1
            #compute the first delta
            dx0= data.x[1]- data.x[0]
            #compute the last delta
            dxn= data.x[n]- data.x[n-1]
            sum = 0
            sum += data.x[0]* data.dxl[0]* data.y[0]*dx0
            sum += data.x[n]* data.dxl[n]* data.y[n]*dxn
            if len(data.x)==2:
                return sum
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += data.x[i]* data.dxl[i]* data.y[i]* dxi
                return sum
        
    def _getVolFrac(self,contrast):
        """
            Compute volume fraction is given by:
            
                q_star= 2*(pi*contrast)**2* volume( 1- volume)
                for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
                we get 2 values of volume:
                     volume1 = (1- sqrt(1- 4*k))/2
                     volume2 = (1+ sqrt(1- 4*k))/2
                contrast unit is 1/A^(2)= 10^(16)cm^(2)
                q_star unit  1/A^(3)*1/cm
                
            the result returned will be 0<= volume <= 1 or None
            
            @param contrast: contrast value provides by the user of type float
            @return None : if the invariant Calculator does not a computed
            q_star already  stored
            @note: volume fraction must have no unit
        """
        if contrast ==None:
            #No contrast value is provided for calculation then no calculation
            return 
        if contrast < 0:
            raise ValueError, "contrast must be greater than zero"  
        
        if self.q_star ==None:
            return  
        
        if self.q_star < 0:
            raise ValueError, "invariant must be greater than zero"
       
        #compute intermediate constant
        k =  1.e-8*self.q_star /(2*(math.pi* math.fabs(float(contrast)))**2)
        #check discriminant value
        discrim= 1 - 4*k
        if discrim < 0:
            return 
        elif discrim ==0:
            volume = 1/2
            return volume
        else:
            # compute the volume
            volume1 = 0.5 *(1 - math.sqrt(discrim))
            volume2 = 0.5 *(1 + math.sqrt(discrim))
            print "volume1",volume1
            print "volume2",volume2
           
            if 0<= volume1 and volume1 <= 1:
                return volume1
            elif 0<= volume2 and volume2<= 1: 
                return volume2 
            return 
    
    def _getSurface(self, pConst, volume=None):
        """
            Compute the surface given by:
                surface = (2*pi *volume(1- volume)*pConst)/ q_star
            @param volume : volume previously calculated
            @return None: if volume used for computation equal None
        """
        #check if the user provides a value for volume
        if volume != None:
            self.volume = float(volume)
        
        #return None if volume or q_star is not computed
        if self.q_star ==None or self.volume == None:
            return 
        if self.q_star ==0:
            raise ZeroDivisionError, "invariant must be greater than zero"
        
        return 2*math.pi*self.volume*(1- self.volume)*float(pConst)/self.q_star
        
        
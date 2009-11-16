"""
    This module is responsible to compute invariant related computation.
    @author: Gervaise B. Alina/UTK
"""
import math 
import numpy
from DataLoader.data_info import Data1D as LoaderData1D
from sans.fit.Fitting import Fit
INFINITY = 10
MIN = 0
STEP= 1000

class InvariantCalculator(object):
    """
        Compute invariant if data is given.
        Can provide volume fraction and surface area if the user provides
        Porod constant  and contrast values.
        @precondition:  the user must send a data of type DataLoader.Data1D
        @note: The data boundaries are assumed as infinite range. 
    """
    def __init__(self, data):
        """
            Initialize variables
            @param data: data must be of type DataLoader.Data1D
        """
        #Initialization of variables containing data's info
        self.data = data
        #Initialization  of the model to use to extrapolate a low q
        self.model_min = None
        #Initialization  of the model to use to extrapolate a high q
        self.model_max = None
        #Initialization of variable that contains invariant extrapolate to low q
        self.q_star_min = 0
        #Initialization of variable that contains invariant extrapolate to low q
        self.q_star_max = 0
        #Initialization of variables containing invariant's info
        self.q_star = self._get_qstar(data= data)
        # Initialization of the invariant total
        self.q_star_total = self.q_star_min + self.q_star + self.q_star_max


    def get_qstar_error(self, data):
        """
            @param data: data of type Data1D
            @return invariant error
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError,"Data must be of type DataLoader.Data1D"
        
        if data.is_slit_smeared():
            return self._getQStarUnsmearError(data= data)
        else:
            return self._getQStarSmearError(data= data)
         
         
    def get_qstar_min(self, data, model, npts):
        """
            Set parameters of the model send by the user to value return by the fit
            engine. Store that model in self.model_min for further use such as plotting.
            
            Extrapolate data to low q with npts number of point.
            This function find the parameters that fit a data  with a given model.
            Then create a new data with its q vector between 0 and the previous data
            first q value. 
            where  the step between the points is the distance data.x[1] - data.x[0]
            The new data has a y defines by model.evalDistrution(new data.x)
            Finally compute the invariant for this new created data.
            
            @param data: data of type Data1D
            @param model: the model uses to extrapolate the data
            @param npts: the number of points used to extrapolate. npts number
            of points will be selected from the last of points of q data to the 
            npts th points of q data.
             
            @return invariant value extrapolated to low q
        """ 
        if model == None or npts== 0:
            return 0
        npts = int(npts)
        x = data.x[0: npts]
        qmin = 0
        qmax = x[len(x)-1]
        dx = None
        dy = None
        dxl = None
        dxw = None
        if data.dx !=None:
            dx = data.dx[0:int(npts)]
        if data.dy !=None:
            dxl = data.dy[0:int(npts)]
        if data.dxl !=None:
            dx = data.dxl[0:int(npts)]
        if data.dxw !=None:
            dxw = data.dxw[0:int(npts)]
            
        # fit the data with a model to get the appropriate parameters
        self.model_min = self._fit( data, model, qmin=qmin, qmax= qmax)
        #Get x between 0 and data.x[0] with step define such as 
        step = math.fabs(x[1]- x[0])
        #create new Data1D to compute the invariant
        new_x = numpy.linspace(start= MIN,
                           stop= x[0],
                           num= npts,
                           endpoint=True
                           )
        new_y = model.evalDistribution(new_x)
        min_data = LoaderData1D(x= new_x,y= new_y)
        min_data.dxl = dxl
        min_data.dxw = dxw
        data.clone_without_data( clone= min_data)
        
        return self._get_qstar(data= min_data)
          
          
    def get_qstar_max(self, data, model, npts):
        """
            Set parameters of the model send by the user to value return by the fit
            engine. Store that model in self.model_max for further use such as plotting.
            
            Extrapolate data to low q with npts number of point
            @param data: data of type Data1D
            @param model: the model uses to extrapolate the data
            @param npts: the number of points used to extrapolate
            @return invariant value extrapolated to low q
        """ 
        if model == None or npts== 0:
            return 0
        
        index_max = len(data.x) -1
        index_min = index_max -int(npts)
        x = data.x[index_min:index_max]
        qmin = x[0]
        qmax = x[len(x)-1]
        dx = None
        dy = None
        dxl = None
        dxw = None
        if data.dx !=None:
            dx = data.dx[qmin:qmax]
        if data.dy !=None:
            dxl = data.dy[qmin:qmax]
        if data.dxl !=None:
            dx = data.dxl[qmin:qmax]
        if data.dxw !=None:
            dxw = data.dxw[0:int(npts)]
            
        # fit the data with a model to get the appropriate parameters
        self.model_max = self._fit( data, model, qmin= qmin, qmax= qmax)
        #Create new Data1D
        new_x = numpy.linspace(start= data.x[qmax],
                           stop= INFINITY,
                           num= npts,
                           endpoint=True
                           )
        new_y = model.evalDistribution(new_x)
        #create a Data1D to compute the invariant
        max_data = LoaderData1D(x= new_x,y= new_y)
        max_data.dxl = dxl
        max_data.dxw = dxw
        data.clone_without_data( clone= max_data)
        
        return self._get_qstar(data= max_data)
          
          
    
    def get_volume_fraction(self, contrast):
        """
            Compute volume fraction is given by:
            
                q_star= 2*(pi*contrast)**2* volume( 1- volume)
                for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
                we get 2 values of volume:
                     volume1 = (1- sqrt(1- 4*k))/2
                     volume2 = (1+ sqrt(1- 4*k))/2
                contrast unit is 1/A^(2)= 10^(16)cm^(2)
                q_star unit  1/A^(3)*1/cm
                
            the result returned will be 0<= volume <= 1
            
            @param contrast: contrast value provides by the user of type float
            @return: volume fraction
            @note: volume fraction must have no unit
        """
        if contrast < 0:
            raise ValueError, "contrast must be greater than zero"  
        if self.q_star ==None:
            raise RuntimeError, "Q_star is not defined"
        
        #Get the total invariant with our without extrapolation
        self.q_star_total = self.q_star + self.q_star_min + self.q_star_max
        
        if self.q_star_total < 0:
            raise ValueError, "invariant must be greater than zero"
       
        #compute intermediate constant
        k =  1.e-8*self.q_star_total /(2*(math.pi* math.fabs(float(contrast)))**2)
        #check discriminant value
        discrim= 1 - 4*k
        if discrim < 0:
            raise RuntimeError, "could not compute the volume fraction: negative discriminant"
        elif discrim ==0:
            volume = 1/2
            return volume
        else:
            # compute the volume
            volume1 = 0.5 *(1 - math.sqrt(discrim))
            volume2 = 0.5 *(1 + math.sqrt(discrim))
            
            if 0<= volume1 and volume1 <= 1:
                return volume1
            elif 0<= volume2 and volume2<= 1: 
                return volume2 
            raise RuntimeError, "could not compute the volume fraction: inconsistent results"
    
    
    def get_surface(self, contrast, porod_const):
        """
            Compute the surface given by:
                surface = (2*pi *volume(1- volume)*pConst)/ q_star
                
            @param contrast: contrast value provides by the user of type float
            @param porod_const: Porod constant 
            @return: specific surface
        """
        # Compute the volume
        volume = self.get_volume_fraction(contrast)
        
        #Check whether we have Q star
        if self.q_star ==None:
            raise RuntimeError, "Q_star is not defined"
        
        #Get the total invariant with our without extrapolation
        self.q_star_total = self.q_star + self.q_star_min + self.q_star_max
        
        if self.q_star_total == 0:
            raise ValueError, "invariant must be greater than zero. Q_star=%g" % self.q_star
        
        return 2*math.pi* volume*(1- volume)*float(porod_const)/self.q_star_total
        
        
        
    def _get_qstar_unsmeared(self, data):
        """
            @param data: data of type Data1D
            Compute invariant given by
            q_star= x0**2 *y0 *dx0 +x1**2 *y1 *dx1 + ..+ xn**2 *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
        """
        if len(data.x)<=1 or len(data.y)<=1 or len(data.x)!=len(data.y):
            msg=  "Length x and y must be equal"
            msg +=" and greater than 1; got x=%s, y=%s"%(len(data.x), len(data.y))
            raise ValueError, msg
        
        elif len(data.x)==1 and len(data.y)==1:
            return 0
    
        else:
            n = len(data.x)-1
            #compute the first delta
            dx0 = data.x[0] + (data.x[1]- data.x[0])/2
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
            
         
    
    def _get_qstar(self, data):
        """
            @param data: data of type Data1D
            @return invariant value
        """
        if not issubclass(data.__class__, LoaderData1D):
            #Process only data that inherited from DataLoader.Data_info.Data1D
            raise ValueError,"Data must be of type DataLoader.Data1D"
        
        # Check whether we have slit smearing information
        if data.is_slit_smeared():
            return self._get_qstar_smeared(data= data)
        else:
            return self._get_qstar_unsmeared(data= data)
        
        
    def _getQStarUnsmearError(self, data):
        """
            @param data: data of type Data1D
            Compute invariant uncertainty on y given by
            q_star = math.sqrt[(x0**2*(dy0)*dx0)**2 +
                    (x1**2 *(dy1)*dx1)**2 + ..+ (xn**2 *(dyn)*dxn)**2 ]
            where n = infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dyn: error on dy
            note: if data doesn't contains dy assume dy= math.sqrt(data.y)
        """
        if len(data.x)<=1 or len(data.y)<=1 or len(data.x)!=len(data.y):
            msg=  "Length x and y must be equal"
            msg +=" and greater than 1; got x=%s, y=%s"%(len(data.x),
                                                         len(data.y))
            raise ValueError,msg
        elif len(data.x)==1 and len(data.y)==1:
            return 0
    
        else:
            #Create error for data without dy error
            if data.dy ==None or data.dy==[]:
                dy=[math.sqrt(y) for y in data.y]
            else:
                dy= data.dy
                
            n = len(data.x)-1
            #compute the first delta
            dx0 = data.x[0] + (data.x[1]- data.x[0])/2
            #compute the last delta
            dxn= data.x[n]- data.x[n-1]
            sum = 0
            sum += (data.x[0]* data.x[0]* dy[0]*dx0)**2
            sum += (data.x[n]* data.x[n]* dy[n]*dxn)**2
            if len(data.x)==2:
                return math.sqrt(sum)
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += (data.x[i]*data.x[i]* dy[i]* dxi)**2
                return math.sqrt(sum)
            
               
    def _get_qstar_smeared(self, data):
        """
            @param data: data of type Data1D
            Compute invariant with slit-smearing info
            q_star= x0*dxl *y0 *dx0 + x1*dxl *y1 *dx1 + ..+ xn*dxl *yn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dxl: slit smearing value
        """
        
        if data.dxl ==None:
            msg = "Cannot compute slit Smear invariant dxl "
            msg +="must be a list, got dxl= %s , dxw= %s"%(str(data.dxl), str(data.dxw))
            raise ValueError,msg

        if len(data.x)<=1 or len(data.y)<=1 or len(data.x)!=len(data.y)\
                or len(data.x)!= len(data.dxl):
           
            msg = "x, dxl, and y must be have the same length and greater than 1"
            raise ValueError,msg
        else:
            n= len(data.x)-1
            #compute the first delta
            dx0= data.x[0] +(data.x[1]- data.x[0])/2
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
        
    def _getQStarSmearError(self, data):
        """
            @param data: data of type Data1D
            Compute invariant with slit smearing info
            q_star= x0*dxl *dy0 *dx0 + x1*dxl *dy1 *dx1 + ..+ xn*dxl *dyn *dxn 
            where n= infinity
            dxi = 1/2*(xi+1 - xi) + (xi - xi-1)
            dx0 = x0+ (x1 - x0)/2
            dxn = xn - xn-1
            dxl: slit smearing value
            dyn : error on dy
            note: if data doesn't contains dy assume dy= math.sqrt(data.y)
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
            #Create error for data without dy error
            if data.dy ==None or data.dy==[]:
                dy= [math.sqrt(y) for y in data.y]
            else:
                dy= data.dy
                
            n= len(data.x)-1
            #compute the first delta
            dx0= data.x[0] +(data.x[1]- data.x[0])/2
            #compute the last delta
            dxn= data.x[n]- data.x[n-1]
            sum = 0
            sum += (data.x[0]* data.dxl[0]* dy[0]*dx0)**2
            sum += (data.x[n]* data.dxl[n]* dy[n]*dxn)**2
            if len(data.x)==2:
                return math.sqrt(sum)
            else:
                #iterate between for element different from the first and the last
                for i in xrange(1, n-1):
                    dxi = (data.x[i+1] - data.x[i-1])/2
                    sum += (data.x[i]* data.dxl[i]* dy[i]* dxi)**2
                return math.sqrt(sum)
        
    def _getVolFracError(self, contrast):
        """
            Compute the error on volume fraction uncertainty where 
            uncertainty is delta volume = 1/2 * (4*k* uncertainty on q_star)
                                 /(2* math.sqrt(1-k* q_star))
                                 
            for k = 10^(8)*q_star/(2*(pi*|contrast|)**2)
            @param contrast: contrast value provides by the user of type float
        """
        if self.q_star_total == None or self.q_star_err == None:
            return  
        
        if self.q_star_total < 0:
            raise ValueError, "invariant must be greater than zero"
        
        k =  1.e-8*self.q_star_total /(2*(math.pi* math.fabs(float(contrast)))**2)
        #check discriminant value
        discrim = 1 - 4*k
        if  1- k*self.q_star <=0:
            raise ValueError, "Cannot compute incertainty on volume"
        
        uncertainty = (0.5 *4*k* self.q_star_err)/(2*math.sqrt(1- k*self.q_star))
        return math.fabs(uncertainty)
    
    
    def _fit(self, data, model, qmin=None, qmax=None):
        """
            perform fit
            @param data: data to fit
            @param model: model to fit
            @return: model with the parameters computed by the fitting engine
        """
        id = 1
        fitter = Fit('scipy')
        fitter.set_data(data,id)
        pars=[]
        
        for param  in model.getParamList() :
            # TODO: Remove the background from computation before fitting?
            if param not in model.getDispParamList():
                pars.append(param)
        fitter.set_model(model,id,pars)
        fitter.select_problem_for_fit(Uid=id,value=1)
        result =  fitter.fit()
        out = result.pvec
        # Set the new parameter back to the model
        if out== None:
            #The fit engine didn't find parameters , the model is returned in
            # the same state
            return model
        # Assigned new parameters values to the model
        if out.__class__== numpy.float64:
            #Only one parameter was fitted
            model.setParam(pars[0], out)
        else:
            for index in xrange(len(pars)):
                model.setParam(pars[index], out[index])
        return model
        
        
        
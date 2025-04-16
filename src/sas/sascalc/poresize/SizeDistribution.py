
import numpy as np
from scipy import stats

from sasdata.dataloader.data_info import Data1D
from sasmodels.data import empty_data1D
from sasmodels.core import load_model
from sasmodels.direct_model import call_kernel
from sasmodels.direct_model import DirectModel
from sasmodels import resolution as rst

from .maxEnt_method import matrix_operation, maxEntMethod
def add_gaussian_noise(x, dx):
    """
    Add Gaussian noise to data based on the sigma of the Guassian uncertainty
    value associated with the data.

    Args:
        x (array-like): Input intensity values
        dx (array-like): sigma of Guassian uncertainties associated with the
        intensities

    Returns:
        array-like: Data with added Gaussian noise
        """
    # Convert inputs to numpy arrays
    data = np.array(x)
    std_dev = np.array(dx)

    # Validate inputs
    if len(data) != len(std_dev):
        raise ValueError("Data and sigmas must have same length")
    if np.any(std_dev <= 0):
        raise ValueError("All sigma values must be positive")

    # Generate and add noise
    noise = np.random.normal(0, std_dev)
    noisy_data = data + noise

    return noisy_data

 def backgroud_fit(self, power=None, qmin=None, qmax=None, type="fixed"):
    """
    THIS IS A WORK IN PROGRESS AND WILL NOT RUN
    Fit data for $y = ax + b$  return $a$ and $b$

    :param power: a fixed, otherwise None
    :param qmin: Minimum Q-value
    :param qmax: Maximum Q-value
    """
    if qmin is None:
        qmin = self.qmin
    if qmax is None:
        qmax = self.qmax

    # Identify the bin range for the fit
    idx = (self.data.x >= qmin) & (self.data.x <= qmax)

    fx = np.zeros(len(self.data.x))

    # Uncertainty
    if type(self.data.dy) == np.ndarray and \
        len(self.data.dy) == len(self.data.x) and \
            np.all(self.data.dy > 0):
        sigma = self.data.dy
    else:
        sigma = np.ones(len(self.data.x))

    # Compute theory data f(x)
    fx[idx] = self.data.y[idx]

    ##Get values of scale and if required power
    if power is not None and power != 0:
        # Linearize the data for a power law fit (log, log)
        linearized_data = Data1D(np.log(self.data.x[idx]), np.log(fx[idx]), dy)
    else:
        linearized_data = Data1D(self.data.x[idx], fx[idx], dy=sigma[idx])

    slope, intercept, _, _, _ = stats.linregress(linearized_data)
    intercept = np.mean(y - slope * x)
    n = len(x)
    residuals = y - (slope * x + intercept)
    sigma = np.sqrt(np.sum(residuals**2) / (n - 1))  # Sample standard deviation
    std_dev_intercept = sigma * np.sqrt(np.sum(x**2) / (n * np.sum((x - np.mean(x))**2)))
    mean_value = np.mean(numbers)
    std_dev = np.std(numbers)


class DistModel(object):
    """
    This class is used to construct the matrix of I(q) curves at each value of
    the dimension whose distribution is being sought. For example the Radius of
    a sphere for the classic pore size distribution calculation. It uses the
    full sasmodels infrastructre including volume and resolution corrections.

    This replaces the following functions:
    def SphereFF
    def SpherVol
    def matrix_operation.G_matrix

    data is the data1D object loaded widt dataloader. In other words the very data
    which we will be fitting.
    model is a string cotaining the name of the model (e.g. 'sphere')
    pars is a dictionary of all parameters and their value for the given model
    dimension is a string containing the name of the parameter that is being
    varied (to find the distribution)
    bins is an array of type float containing the various values of the
    dimension variable that forms the distribution. Only the weights will be
    changed.
    QUESTION: is it required that the values in bins be sorted?

    ..NOTE: this code is not yet ready to be used (clearly) but is meant as
       a base structure
    """
    def __init__(self, data, model, dimension, bins, pars=None):

        self.data=data
        self.model = load_model(model)
        self.params=pars
        self.dim_distr=dimension
        self.bins=bins
        self.intensity()
        self.pars=pars
        self.pars["scale"]=1.0
        self.pars["background"]=0.0


    def base_matrix(self):
        f = DirectModel(self.data, self.model)
        for i in self.bins: self.intensity[i] = f(self.dim_distr = i, **self.pars)
        return np.array(self.intensity)


class sizeDistribution(object):

    def __init__(self, data:Data1D):

        ## Data Manipulation
        self._data = data
        self._qMin = data.x[0]
        self._qMax = data.x[-1]
        self._ndx_qmin = 0
        self._ndx_qmax = -1

        ## MaxEntropy bin parameters
        self._diamMin = 10
        self._diamMax = 100000 
        self._nbins = 2
        self._logbin = True
        self._bins = None

        #sasmodels 
        self._model = "ellipsoid"
        self._aspectRatio = 1.0

        self._contrast = 1.0 ## sld - sld_solvent=0.0
        self._background = 0.0 ## Not For Model ! 
        self._scale = 1.0 ## Fix to 1.0 for models 
        self._resolution = None ## For future implementation. For now, only use data with resolution information. 

        self.model_matrix = None

        #advanced parameters for MaxEnt 
        self._iterMax = 5000
        self._skyBackground = 1e-6
        self._useWeights = False
        self._weightType = 'dI'  
        self._weightFactor = 1.0
        self._weights = self.data.dy

        ## Return Values after the MaxEnt should 
        self.BinMagnitude_maxEnt = np.zeros_like(self.bins)
        self.chiSq_maxEnt = np.inf
        self.Iq_maxEnt = np.zeros_like(self._data.y)

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value:Data1D):
        self._data = value

    @property
    def qMin(self):
        return self._qMin
        
    @qMin.setter
    def qMin(self, value):
        self._qMin = value
        self._ndx_qmin = np.searchsorted(self._data.x, value)

    @property
    def qMax(self):
        return self._qMax
        
    @qMax.setter
    def qMax(self, value):
        self._qMax = value
        self._ndx_qmax = np.searchsorted(self._data.x, value)

    @property
    def ndx_qmin(self):
        return self._ndx_qmin
        
    @ndx_qmin.setter
    def ndx_qmin(self, value:int):
        """set the ndx_qmin value and update q_min variable"""
        self._ndx_qmin = value
        self._qMin = self._data.x[value]

    @property
    def ndx_qmax(self):
        return self._ndx_qmax

    @ndx_qmax.setter
    def ndx_qmax(self, value):
        """set the ndx_qmin value and update q_min variable"""
        self._ndx_qmax = value
        self._qMax = self._data.x[value]

    @property
    def diamMax(self):
        return self._diamMax
        
    @diamMax.setter
    def diamMax(self, value):
        self._diamMax = value

    @property
    def diamMin(self):
        return self._diamMin
        
    @diamMin.setter
    def diamMin(self, value):
        self._diamMin = value

    @property
    def nbins(self):
        return self._nbins
        
    @nbins.setter
    def nbins(self, value:int):
        self._nbins = value
        self.set_bins()

    @property
    def logbin(self):
        return self._logbin
        
    @logbin.setter
    def logbin(self, value:bool):
        self._login=value
        self.set_bins()

    @property 
    def bins(self):
        return self._bins
    
    def set_bins(self):

        ## bins are in radius distances
        if self.logbin:

            self._bins = np.logspace(np.log10(self.diamMin),
                                      np.log10(self.diamMax), 
                                       self.nbins+1, True)/2
        else: 
            self._bins = np.linspace(self.diamMin, self.diamMax, self.nbins+1,True)/2

        self._binDiff = np.diff(self._bins)
        self._bins = self._bins[:-1] + self._binDiff/2  

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value:str):
        self._model = value   
   
    @property
    def aspectRatio(self):
        return self._aspectRatio
        
    @aspectRatio.setter
    def aspectRatio(self, value:float):
        self._aspectRatio = value

    @property
    def contrast(self):
        return self._contrast

    @contrast.setter
    def contrast(self, value):
        self._contrast = value

    @property
    def resolution(self):
        return self._resolution
    
    @resolution.setter
    def resolution(self, value):
        self._resolution = value

    @property
    def background(self):
        return self._background
        
    @background.setter
    def background(self, value):
        self._background = value

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        
    @property
    def iterMax(self):
        return self._iterMax
        
    @iterMax.setter
    def iterMax(self, value):
        self._iterMax = value

    @property
    def skyBackground(self):
        return self._skyBackground
        
    @skyBackground.setter
    def skyBackground(self, value):
        self._skyBackground = value   

    @property
    def useWeights(self):
        return self._useWeights
        
    @useWeights.setter
    def useWeights(self, value:bool):
        self._useWeights = value
        self.update_weights()
    @property
    def weightFactor(self):
        return self._weightFactor
        
    @weightFactor.setter
    def weightFactor(self, value):
        self._weightFactor = value
        
    @property
    def weightType(self):
        return self._weightType
    
    @weightType.setter
    def weightType(self, value):
        self._weightType = value
        self.update_weights()

    @property
    def weights(self):
        return self._weights
    
    def update_weights(self, sigma=None):

        if sigma is None:
            wdata = self.data
        else:
            wdata = sigma
        
        if self._useWeights == False:
            self._weights = np.ones_like(wdata.y)
        else:
            if (self.weightType == 'dI'):
                self._weights = wdata.dy

            elif (self.weightType == 'sqrt(I Data)'):
                self._weights = np.sqrt(wdata.y)

            elif (self.weightType == 'abs(I Data)'):
                self._weights = np.abs(wdata.y)

            elif self.weightType == 'None':
                self._useWeights=False
                self._weights = np.ones_like(wdata.y)
        
        return None

    def calculate_powerlaw(self):
        ## From invariant?
        return None
    
    def calculate_background(self):
        ## From invariant? 
        return None

    def generate_model_matrix(self, moddata:Data1D):
        """
        generate a matrix of intensities from a specific sasmodels model; probably should be generalized to a class to use maxent on
        any parameter of interest w/in the model. For now, the pars are fixed. 
        moddata :: Data1D object that has the data trimmed depending on background subtraction or powerlaw subtracted from the data. Also self.qMin and self.qMax. 

        """
        model = load_model(self.model)

        pars = {'sld':self.contrast, 'sld_solvent':0.0, 'background':0.0, 'scale':1.0,
                }
        
        kernel = DirectModel(moddata, model)
        
        intensities = []
        for bin in self.bins:
            pars['radius_equatorial'] = bin
            pars['radius_polar'] = bin/self.aspectRatio
            intensities.append(kernel(**pars))
        
        self.model_matrix = np.vstack(intensities)

        ## For data with no resolution. Should be defined in moddata
        #if self.resolution == 'Pinhole1D':
        #    kernel.resolution = rst.Pinhole1D(moddata.x, moddata.dx)
        #elif self.resolution == 'Slit1D':
        #    kernel.resolution = rst.Slit1D(moddata.x, moddata.dx)
        #else:
        #    kernel.resolution = rst.Perfect1D(moddata.x)
        

    def prep_maxEnt(self):
        # after setting up the details for the fit run run_maxEnt.
        # Then, if full fit is selected set up loop with a callable number of
        # iterations that calls add_gaussian_noise(x, dx) before
        # running run_maxEnt for iter number of times
        
        pass

    def run_maxEnt(self):
        
        BinsBack = np.ones_like(self._bins)*self.skyBackground*self.scale/self.contrast
        MethodCall = maxEntMethod()
        chisq = None
        BinMag = None
        ICalc = self.Iq_maxEnt
        intensity = self.scale * self.data.y[self.ndx_qmin, self.ndx_qmax] - self.background
        

         ## run MaxEnt
        chisq, BinMag, ICalc = MethodCall.MaxEnt_SB(intensity,
                                                             self.scale/(self.weightFactor*self.weights),
                                                               self.model_matrix,
                                                                 BinsBack,
                                                                   self.iterMax, report=True)
        self.chiSq_maxEnt = chisq
        self.BinMagnitude_maxEnt = BinMag/(2.*self._binDiff)
        self.Iq_maxEnt = ICalc
        
        return None

def sizeDistribution_func(input):
    '''
    This function packages all the inputs that MaxEnt_SB needs (including initial values) into a dictionary and executes the MaxEnt_SB function
    :param dict input:
        input must have the following keys, each corresponding to their specified type of values:
        Key                          | Value
        __________________________________________________________________________________________
        Data                         | list[float[npt],float[npt]]: I and Q. The two arrays should both be length npt
        Limits                       | float[2]: a length-2 array contains Qmin and Qmax
        Scale                        | float:
        DiamRange                    | float[3]: A length-3 array contains minimum and maximum diameters between which the 
                                                 distribution will be constructed, and the thid number is the number of bins 
                                                 (must be an integer) (TODO: maybe restructure that)
        LogBin                       | boolean: Bins will be on a log scale if True; bins will be on a linear scale is False 
        WeightFactors                | float[npt]: Factors on the weights
        Contrast                     | float: The difference in SLD between the two phases
        Sky                          | float: Should be small but non-zero (TODO: Check this statement)
        Weights                      | float[npt]: Provide some sort of uncertainty. Examples include dI and 1/I
        Background                   | float[npt]: Scattering background to be subtracted
        Resolution                   | obj: resolution object
        Model                        | string: model name, currently only supports 'Sphere'
    '''

    ### input data
    ##scat_data = Data1D() ## how to get this data in? ## Sent from the data_loader 
    Q, I = input["Data"]
    

    ### results data
    Ic = np.zeros(len(I))

    ##results_data = Data1D()

    ### GUI Variables  
    ## standard
    Qmin = input["Limits"][0]
    Qmax = input["Limits"][1]

    minDiam = input["DiamRange"][0]
    maxDiam = input["DiamRange"][1]
    Nbins = input["DiamRange"][2]

    contrast = input["Contrast"] 

    ## 
    model = input["Model"]

    ## advanced
    iterMax = input["IterMax"]
    scale = input["Scale"]
    logbin = input["Logbin"] ## Boolean? 
    sky = input["Sky"]
 

    ## Dependent
    if logbin:
        Bins = np.logspace(np.log10(minDiam),np.log10(maxDiam),Nbins+1,True)/2        #make radii
    else:
        Bins = np.linspace(minDiam, maxDiam, Nbins+1,True)/2        #make radii

    Dbins = np.diff(Bins)
    Bins = Bins[:-1]+Dbins/2.
    Ibeg = np.searchsorted(Q,Qmin)
    Ifin = np.searchsorted(Q,Qmax)+1        #include last point
    BinMag = np.zeros_like(Bins)
    wtFactor = input["WeightFactors"][Ibeg:Ifin]
    Back = input["Background"][Ibeg:Ifin]

    res = input["Resolution"] ## dQ 
    wt = input["Weights"][Ibeg:Ifin]
    ## setup MaxEnt
    Gmat = matrix_operation().G_matrix(Q[Ibeg:Ifin],Bins,contrast,model,res)
    BinsBack = np.ones_like(Bins)*sky*scale/contrast
    MethodCall = maxEntMethod()

    ## run MaxEnt
    chisq,BinMag,Ic[Ibeg:Ifin] = MethodCall.MaxEnt_SB(scale*I[Ibeg:Ifin]-Back,scale/np.sqrt(wtFactor*wt),Gmat,BinsBack,iterMax,report=True)
    BinMag = BinMag/(2.*Dbins)
    return chisq,Bins,Dbins,BinMag,Q[Ibeg:Ifin],Ic[Ibeg:Ifin]
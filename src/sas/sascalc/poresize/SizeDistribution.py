
import numpy as np
import logging
from scipy import stats, integrate 

from sasdata.dataloader.data_info import Data1D, DataInfo
from sasmodels.data import empty_data1D
from sasmodels.core import load_model
from sasmodels.direct_model import call_kernel
from sasmodels.direct_model import DirectModel
from sasmodels import resolution as rst

from sas.sascalc.poresize.maxEnt_method import matrix_operation, maxEntMethod

logger = logging.getLogger(__name__)

def add_gaussian_noise(x, dx, seed=None):
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
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, std_dev)
    noisy_data = data + noise

    return noisy_data

def background_fit(data, power=None, qmin=None, qmax=None, type="fixed"):
    """
    THIS IS A WORK IN PROGRESS AND WILL NOT RUN
    Fit data for $y = ax + b$  return $a$ and $b$

    :param Data1D data: data to fit
    :param power: a fixed, otherwise None
    :param qmin: Minimum Q-value
    :param qmax: Maximum Q-value

    If performing a linear fit for background, then set power = 0.0 and type = "fixed"
    Otherwise,
    """
    if qmin is None:
        qmin = min(data.x)
    if qmax is None:
        qmax = max(data.x)

    # Identify the bin range for the fit
    idx = (data.x >= qmin) & (data.x <= qmax)

    fx = np.zeros(len(data.x))

    # Uncertainty
    if isinstance(data.dy, np.ndarray) and \
        len(data.dy) == len(data.x) and \
            np.all(data.dy > 0):
        sigma = data.dy
    else:
        sigma = np.ones(len(data.x))

    # Compute theory data f(x)
    fx[idx] = data.y[idx]

    ##Get values of scale and if required power
    if power is not None and power != 0:
        # Linearize the data for a power law fit (log, log)
        linearized_data = Data1D(np.log(data.x[idx]), np.log(fx[idx]), dy=(1/np.log(10))*sigma[idx]/fx[idx])
    else:
        linearized_data = Data1D(data.x[idx], fx[idx], dy=None)

    # slope, intercept, _, _, err_slope, err_int = stats.linregress(linearized_data.x, linearized_data.y)
    result = stats.linregress(linearized_data.x, linearized_data.y)
    intercept = np.mean(linearized_data.y - result.slope * linearized_data.x)
    n = len(linearized_data.x)
    residuals = linearized_data.y - (result.slope * linearized_data.x + intercept)
    sigma = np.sqrt(np.sum(residuals**2) / (n - 1))  # Sample standard deviation
    #std_dev_intercept = sigma * np.sqrt(np.sum(linearized_data.x**2) / (n * np.sum((linearized_data.x - np.mean(linearized_data.x))**2)))
    #mean_value = np.mean(numbers)
    #std_dev = np.std(numbers)
    return np.exp(result.slope), result.intercept


def ellipse_volume(rp,re):
    return (4*np.pi/3)*rp*re**2

class DistModel():
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

        self.data = data  
        self.model = load_model(model)
        self.params = pars
        self.dim_distr = dimension
        self.bins = bins
        self.intensity = []
        self.pars = pars
        self.pars["scale"] = 1.0
        self.pars["background"] = 0.0


    def base_matrix(self):
        f = DirectModel(self.data, self.model)
        for i in self.bins: self.intensity.append(f(**self.pars))
        return np.array(self.intensity)


class sizeDistribution():

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
        self._useWeights = True
        self._weightType = 'dI'  
        self._weightFactor = 1.0
        self._weights = self.data.dy

        ## Return Values after the MaxEnt should 
        self.BinMagnitude_maxEnt = np.zeros_like(self.bins)
        self.BinMagnitude_Errs = None
        self.chiSq_maxEnt = np.inf
        self.Iq_maxEnt = None

        self.MaxEnt_statistics = {'volume':0., 'volume_err':0., 'mean':0., 'median':0., 'mode':0.}

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
        self.set_bins()

    @property
    def diamMin(self):
        return self._diamMin
        
    @diamMin.setter
    def diamMin(self, value):
        self._diamMin = value
        self.set_bins()

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

        #self._volume_bins = ellipse_volume(self._bins*self.aspectRatio, )
        self._bin_edges = self._bins
        self._binDiff = np.diff(self._bins)
        self._bins = self._bins[:-1] + self._binDiff/2  

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value:str):
        if value != "ellipsoid":
            logger.info("model is hard coded to ellipsoid for the time being. Please only use ellipsoid. Setting model to ellipsoid.")
            self._model = "ellipsoid"
        else:
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
    
    def update_weights(self, sigma=None, percent_value=0.01):

        if sigma is None:
            wdata = self.data
        else:
            wdata = sigma
        
        if self._useWeights == False:
            self._weights = np.ones_like(wdata.y)
        else:
            if (self.weightType == 'dI'):
                self._weights = 1/np.array(wdata.dy)

            elif (self.weightType == 'sqrt(I Data)'):
                self._weights = 1/np.sqrt(wdata.y)

            elif (self.weightType == 'abs(I Data)'):
                self._weights = 1/np.abs(wdata.y)

            elif self.weightType == 'percentI':
                self._useWeights=False
                self._weights = 1/np.abs(percent_value*wdata.y)
            else:
                logger.error("weightType doesn't match the possible strings for weight selection.\n Please check the value entered or use 'dI'.")
        
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
            pars['radius_polar'] = bin*self.aspectRatio
            intensities.append(kernel(**pars))
        
        self.model_matrix = np.vstack(intensities).T

        ## For data with no resolution. Should be defined in moddata
        #if self.resolution == 'Pinhole1D':
        #    kernel.resolution = rst.Pinhole1D(moddata.x, moddata.dx)
        #elif self.resolution == 'Slit1D':
        #    kernel.resolution = rst.Slit1D(moddata.x, moddata.dx)
        #else:
        #    kernel.resolution = rst.Perfect1D(moddata.x)


    def calc_volume_weighted_dist(self, binmag):
        """
        Calculate the volume weighted distribution. 
        """
        if self.logbin:

            radbins = np.logspace(np.log10(self.diamMin),
                                      np.log10(self.diamMax), 
                                       self.nbins+1, True)/2
            
        else: 
            radbins = np.linspace(self.diamMin, self.diamMax, self.nbins+1,True)/2

        self.volume_bins = ellipse_volume(self.aspectRatio*radbins, radbins)
        self.vbin_diff = np.diff(self.volume_bins)
        self.volume_bins = self.volume_bins[:-1] + self.vbin_diff/2
        self.volume_fraction = binmag*self.volume_bins/(2*self.vbin_diff)

        if self.BinMagnitude_Errs is not None:
            self.volume_fraction_errs = self.BinMagnitude_Errs*(self.volume_bins/(2*self.vbin_diff))
        else: 
            self.volume_fraction_errs = None
        
    def prep_maxEnt(self, sub_intensities:Data1D, full_fit:bool=False, nreps:int = 10, rngseed=None):
        """
        1. Subtract intensities from the raw data. 
        2. Trim the data to the correct q-range for maxEnt; Create new trimmed Data1D object to return after MaxEnt.
        3. Generate Model Data based of the trimmed data 
        4. Create a list of intensities for maxEnt, if full_fit == True , call add_gausisan_noise nreps times; pass just subtracted intensities
        5. calculate initial bin weights, sigma, and return
        """
        # after setting up the details for the fit, run run_maxEnt.
        # Then, if full fit is selected set up loop with a callable number of
        # iterations that calls add_gaussian_noise(x, dx) before
        # running run_maxEnt for iter number of times
        
        ## subtract the background and powerlaw from the raw data
        ## sub_intensities Data1D object with y=A*x^M + B; should have dy as well

        ## Loop through parameters for the 
        pars_keys = ['x','y','dx','dy'] #,'dxw','dxl']
        trim_data_pars = {}

        assert len(sub_intensities.y) == len(self._data.y)

        for pkey in pars_keys:
            check_data = (pkey in list(self._data.__dict__.keys()))
            
            if check_data:
                item = self._data.__dict__[pkey]
                try:
                    if pkey == 'y':
                        item = item - sub_intensities.y
                    elif pkey == 'dy':
                        item = item + sub_intensities.dy

                    data_vals = item[self.ndx_qmin:self.ndx_qmax]

                except Exception as e:
                    print(e)
                trim_data_pars[pkey] = data_vals

        
        trim_data = Data1D(**trim_data_pars)
        trim_data.__dict__['qmin'] = self.qMin
        trim_data.__dict__['qmax'] = self.qMax

        self.generate_model_matrix(trim_data)

        intensities = []
        if full_fit:
            for j in range(nreps):
                intensities.append(add_gaussian_noise(trim_data.y, trim_data.dy, seed=rngseed))
        else:
            intensities.append(trim_data.y)

        self.update_weights(trim_data)
        init_binsBack = np.ones_like(self.bins)*self.skyBackground*self.scale/self.contrast
        sigma = self.scale/(self.weightFactor*self.weights)

        return trim_data, intensities, init_binsBack, sigma

    def run_maxEnt(self, maxentdata:Data1D, intensities:list, BinsBack:np.array, sigma:np.array):
        
        ChiSq = []
        BinMag = []
        IMaxEnt = []
        convergence = []

         ## run MaxEnt
        for nint, intensity in enumerate(intensities):
            MethodCall = maxEntMethod()
            try:
                chisq, bin_magnitude, icalc, converged, conv_iter = MethodCall.MaxEnt_SB(intensity,
                                                             sigma,
                                                               self.model_matrix,
                                                                 BinsBack,
                                                                   self.iterMax, report=True)
            
                ChiSq.append(chisq)
                BinMag.append(bin_magnitude)
                IMaxEnt.append(icalc)
                convergence.append([converged, conv_iter])
                if (not converged):
                    logger.warning("Maximum Entropy did not converge. Try lowering the weight factor to increase the weighting effect.")
            except ZeroDivisionError as e:
                logger.error("Divide by Zero Error occured in maximum entropy fitting. Try lowering the weight factor to increase the error weighting")
            


        ## Check len of intensities for full vs. quick fit
        if len(intensities) == 1:
            self.chiSq_maxEnt = np.mean(ChiSq)
            self.BinMagnitude_maxEnt = np.mean(BinMag,axis=0)/(2.*self._binDiff)

            self.BinMagnitude_Errs = None 
            maxentdata.y = np.mean(IMaxEnt, axis=0)
            maxentdata.dy = None
            self.Iq_maxEnt  = maxentdata
            
        elif len(intensities) > 1:
            self.chiSq_maxEnt = np.mean(ChiSq)
            self.BinMagnitude_maxEnt = np.mean(BinMag, axis=0)/(2.*self._binDiff)

            self.BinMagnitude_Errs = np.std(BinMag, axis=0)/(2.*self._binDiff)
            maxentdata.y = np.mean(IMaxEnt, axis=0)
            maxentdata.dy = np.std(IMaxEnt, axis=0)
            self.Iq_maxEnt  = maxentdata
            

        else:
            logger.error('The length of the intensity array is 0. Did you run prep_maxEnt before run_maxEnt? Check that intensities is an array of at least length 1.')

        self.calculate_statistics(BinMag)
        #self.calc_volume_weighted_dist(np.mean(BinMag, axis=0))
        

        return convergence

    def calculate_statistics(self, bin_mag:list, 
                             ):
        
        maxent_cdf_array = integrate.cumulative_trapezoid(bin_mag/(2*self._binDiff), 2*self.bins, axis=1)
        #print(maxent_cdf_array[:,-1])
        self.BinMag_numberDist = self.BinMagnitude_maxEnt/ellipse_volume(self.aspectRatio*self.bins, self.bins)

        rvdist = stats.rv_histogram((self.BinMagnitude_maxEnt, self._bin_edges*2)) ## volume fraction weighted
        #print(rvdist.mean(), rvdist.median())
        number_cdf = integrate.cumulative_trapezoid(self.BinMag_numberDist, 2*self.bins)
        self.number_cdf = number_cdf/number_cdf[-1]

        self.volumefrac_cdf = np.mean(maxent_cdf_array,axis=0)/np.mean(maxent_cdf_array[:,-1])
        self.MaxEnt_statistics['volume'] = np.mean(maxent_cdf_array[:,-1])
        self.MaxEnt_statistics['volume_err'] = np.std(maxent_cdf_array[:,-1])
        self.MaxEnt_statistics['mode'] = 2*self.bins[np.argmax(self.BinMag_numberDist)] ## number density
        ndx_med = np.where(self.volumefrac_cdf >= 0.5)[0][0]
        self.MaxEnt_statistics['median'] = 2*self.bins[ndx_med] ## volume fraction weighted Median
        self.MaxEnt_statistics['mean'] = rvdist.mean() ## volume fraction weighted mean



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
    Gmat = matrix_operation().G_matrix(Q[Ibeg:Ifin],Bins,contrast,model,res).T
    BinsBack = np.ones_like(Bins)*sky*scale/contrast
    MethodCall = maxEntMethod()
    sigma = scale/np.sqrt(wtFactor*wt)
    ## run MaxEnt
    chisq,BinMag,Ic[Ibeg:Ifin] = MethodCall.MaxEnt_SB(scale*I[Ibeg:Ifin]-Back,
                                                      scale/np.sqrt(wtFactor*wt),Gmat,BinsBack,iterMax,report=True)
    BinMag = BinMag/(2.*Dbins)
    return chisq,Bins,Dbins,BinMag,Q[Ibeg:Ifin],Ic[Ibeg:Ifin]

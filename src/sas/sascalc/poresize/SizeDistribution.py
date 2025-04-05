
import numpy as np

from sasdata.dataloader.data_info import Data1D 
from sasmodels.core import load_model
from sasmodels.direct_model import call_kernel
from sasmodels.direct_model import DirectModel

from maxEnt_method import matrix_operation, maxEntMethod


class SizeDistribution:

    def __init__(self):

        self.q = np.zeros(0,  dtype=np.float64)
        self.Iq = np.zeros(0, dtype=np.float64)
        self.dIq =np.zeros(0, dtype=np.float64) 

        self.set_qmin(0)
        self.set_qmax(-1)

        self.set_diammin(-1)
        self.set_diammax(-1)
        self.set_nbins(2)
        self.set_logbin(False)
        self.set_bins()

        #sasmodels -> DistModel
        self.set_contrast(0.0)
        self.set_model("ellipsoid") ## spheroid, aspect ratio 
        self.set_aspectRatio(1.0)
        self.set_background(0.0)
        self.set_scale(1.0)
        
        #advanced parameters for MaxEnt 
        self.set_iterMax(5000)
        self.set_sky(1e-6) ## feedback loop
        self.set_weightFactor()
        self.set_weights()
        
        ## Return Values after the MaxEnt? 
        self.BinMagnitude_maxEnt = np.zeros_like(self.bins)
        self.chiSq_maxEnt = np.inf
        self.Iq_maxEnt = np.zeros_like(self.Iq)



    def set_qmin(self, value:float):
        """
        
        """
        return ndata
    
    def get_qmin(self):
        """
        
        """
        return self.qmin
    
    def set_qmax(self, value:float):
        """
        
        """
        return ndata

    def set_diammin(self, value:float) -> None:
        """
        
        """
        return None  

    def set_diammax(self, value:float) -> None:
        """
        
        """
        return None 
    

    def calculate_powerlaw(self):
        return None
    
    def calculate_background(self):
        return None

def sizeDistribution(input):
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
    iterMax = input.get("IterMax", 5000)
    scale = input["Scale"]
    logbin = input["Logbin"] ## Boolean? 
    sky = input["Sky"]

    res = input["Resolution"] ## dQ 

    ## Dependent
    if logbin:
        Bins = np.logspace(np.log10(minDiam),np.log10(maxDiam),Nbins+1,True)/2        #make radii
    else:
        Bins = np.linspace(minDiam, maxDiam, Nbins+1,True)/2        #make radii

    Dbins = np.diff(Bins)
    Bins = Bins[:-1]+Dbins/2.
    Ibeg = np.searchsorted(Q,Qmin)
    Ifin = np.searchsorted(Q,Qmax)+1        #include last point
    wt = input["Weights"][Ibeg:Ifin]
    wtFactor = input["WeightFactors"][Ibeg:Ifin]
    Back = input["Background"][Ibeg:Ifin]
    BinMag = np.zeros_like(Bins)
    
    ## setup MaxEnt
    Gmat = matrix_operation().G_matrix(Q[Ibeg:Ifin],Bins,contrast,model,res)
    BinsBack = np.ones_like(Bins)*sky*scale/contrast
    MethodCall = maxEntMethod()

    ## run MaxEnt
    chisq,BinMag,Ic[Ibeg:Ifin] = MethodCall.MaxEnt_SB(scale*I[Ibeg:Ifin]-Back,scale/np.sqrt(wtFactor*wt),Gmat,BinsBack,iterMax,report=True)
    BinMag = BinMag/(2.*Dbins)
    return chisq,Bins,Dbins,BinMag,Q[Ibeg:Ifin],Ic[Ibeg:Ifin]
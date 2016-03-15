"""
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#See the license text in license.txt
"""
import numpy
import math

## Singular point
SIGMA_ZERO = 1.0e-010
## Limit of how many sigmas to be covered for the Gaussian smearing
# default: 2.5 to cover 98.7% of Gaussian
LIMIT = 3.0
## Defaults
R_BIN = {'Xhigh':10, 'High':5, 'Med':5, 'Low':3}
PHI_BIN ={'Xhigh':20, 'High':12, 'Med':6, 'Low':4}   

class Smearer2D:
    """
    Gaussian Q smearing class for SAS 2d data
    """
     
    def __init__(self, data=None, model=None, index=None, 
                 limit=LIMIT, accuracy='Low', coords='polar', engine='c'):
        """
        Assumption: equally spaced bins in dq_r, dq_phi space.
        
        :param data: 2d data used to set the smearing parameters
        :param model: model function
        :param index: 1d array with len(data) to define the range 
         of the calculation: elements are given as True or False
        :param nr: number of bins in dq_r-axis
        :param nphi: number of bins in dq_phi-axis
        :param coord: coordinates [string], 'polar' or 'cartesian'
        :param engine: engine name [string]; 'c' or 'numpy'
        """
        ## data
        self.data = data
        ## model
        self.model = model
        ## Accuracy: Higher stands for more sampling points in both directions 
        ## of r and phi.
        self.accuracy = accuracy
        ## number of bins in r axis for over-sampling 
        self.nr = R_BIN
        ## number of bins in phi axis for over-sampling 
        self.nphi = PHI_BIN
        ## maximum nsigmas
        self.limit = limit
        self.index = index
        self.coords = coords
        self.smearer = True
        self._engine = engine
        self.qx_data = None
        self.qy_data = None
        self.q_data = None
        # dqx and dqy mean dq_parr and dq_perp
        self.dqx_data = None
        self.dqy_data = None
        self.phi_data = None
        
    def get_data(self):   
        """
        Get qx_data, qy_data, dqx_data,dqy_data,
        and calculate phi_data=arctan(qx_data/qy_data)
        """
        if self.data == None or self.data.__class__.__name__ == 'Data1D':
            return None
        if self.data.dqx_data == None or self.data.dqy_data == None:
            return None
        self.qx_data = self.data.qx_data[self.index]
        self.qy_data = self.data.qy_data[self.index]
        self.q_data = self.data.q_data[self.index]
        # Here dqx and dqy mean dq_parr and dq_perp
        self.dqx_data = self.data.dqx_data[self.index]
        self.dqy_data = self.data.dqy_data[self.index]
        self.phi_data = numpy.arctan(self.qx_data / self.qy_data)
        ## Remove singular points if exists
        self.dqx_data[self.dqx_data < SIGMA_ZERO] = SIGMA_ZERO
        self.dqy_data[self.dqy_data < SIGMA_ZERO] = SIGMA_ZERO
        return True
    
    def set_accuracy(self, accuracy='Low'):   
        """
        Set accuracy.
        
        :param accuracy:  string
        """
        self.accuracy = accuracy

    def set_smearer(self, smearer=True):
        """
        Set whether or not smearer will be used
        
        :param smearer: smear object
        
        """
        self.smearer = smearer
        
    def set_data(self, data=None):   
        """
        Set data.
        
        :param data: DataLoader.Data_info type
        """
        self.data = data
  
            
    def set_model(self, model=None):   
        """
        Set model.
        
        :param model: sas.models instance
        """
        self.model = model  
           
    def set_index(self, index=None):   
        """
        Set index.
        
        :param index: 1d arrays
        """
        self.index = index       
    
    def get_value(self):
        """
        Over sampling of r_nbins times phi_nbins, calculate Gaussian weights, 
        then find smeared intensity
        """    
        valid = self.get_data()
        if valid == None:
            return valid
        # all zero values of dq
        if numpy.all(numpy.fabs(self.dqx_data <= 1.1e-10)) and \
                        numpy.all(numpy.fabs(self.dqy_data <= 1.1e-10)):
            self.smearer = False
  
        if self.smearer == False:
            return self.model.evalDistribution([self.qx_data, self.qy_data]) 

        nr = self.nr[self.accuracy]
        nphi = self.nphi[self.accuracy]
        # Number of bins in the dqr direction (polar coordinate of dqx and dqy)
        bin_size = self.limit / nr
        # Total number of bins = # of bins 
        # in dq_r-direction times # of bins in dq_phi-direction
        n_bins = nr * nphi
        # data length in the range of self.index
        len_data = len(self.qx_data)
        #len_datay = len(self.qy_data)
        if self._engine == 'c' and self.coords == 'polar':
            try:
                import sas.models.sas_extension.smearer2d_helper as smearer2dc
                smearc = smearer2dc.new_Smearer_helper(self.qx_data, 
                                              self.qy_data,
                                              self.dqx_data, self.dqy_data,
                                              self.limit, nr, nphi, 
                                              int(len_data))
                weight_res = numpy.zeros(nr * nphi )
                qx_res = numpy.zeros(nr * nphi * int(len_data))
                qy_res = numpy.zeros(nr * nphi * int(len_data))
                smearer2dc.smearer2d_helper(smearc, weight_res, qx_res, qy_res)
            except:
                raise 
        else:
            # Mean values of dqr at each bins 
            # starting from the half of bin size
            r = bin_size / 2.0 + numpy.arange(nr) * bin_size
            # mean values of qphi at each bines
            phi = numpy.arange(nphi)
            dphi = phi * 2.0 * math.pi / nphi
            dphi = dphi.repeat(nr)
    
            ## Transform to polar coordinate, 
            #  and set dphi at each data points ; 1d array
            dphi = dphi.repeat(len_data)
            q_phi = self.qy_data / self.qx_data
            
            # Starting angle is different between polar 
            #  and cartesian coordinates.
            #if self.coords != 'polar':
            #    dphi += numpy.arctan( q_phi * self.dqx_data/ \
            #                  self.dqy_data).repeat(n_bins).reshape(len_data,\
            #                                n_bins).transpose().flatten()
    
            # The angle (phi) of the original q point
            q_phi = numpy.arctan(q_phi).repeat(n_bins).reshape(len_data,\
                                                n_bins).transpose().flatten()
            ## Find Gaussian weight for each dq bins: The weight depends only 
            #  on r-direction (The integration may not need)
            weight_res = numpy.exp(-0.5 * ((r - bin_size / 2.0) * \
                                    (r - bin_size / 2.0)))- \
                                    numpy.exp(-0.5 * ((r + bin_size / 2.0 ) *\
                                    (r + bin_size / 2.0)))
            # No needs of normalization here.
            #weight_res /= numpy.sum(weight_res)
            weight_res = weight_res.repeat(nphi).reshape(nr, nphi)
    
            weight_res = weight_res.transpose().flatten()
            
            ## Set dr for all dq bins for averaging
            dr = r.repeat(nphi).reshape(nr, nphi).transpose().flatten()
            ## Set dqr for all data points
            dqx = numpy.outer(dr, self.dqx_data).flatten()
            dqy = numpy.outer(dr, self.dqy_data).flatten()
    
            qx = self.qx_data.repeat(n_bins).reshape(len_data, \
                                                 n_bins).transpose().flatten()
            qy = self.qy_data.repeat(n_bins).reshape(len_data, \
                                                 n_bins).transpose().flatten()
    
            # The polar needs rotation by -q_phi
            if self.coords == 'polar':
                q_r = numpy.sqrt(qx * qx + qy * qy)
                qx_res = ((dqx*numpy.cos(dphi) + q_r) * numpy.cos(-q_phi) +\
                               dqy*numpy.sin(dphi) * numpy.sin(-q_phi))
                qy_res = (-(dqx*numpy.cos(dphi) + q_r) * numpy.sin(-q_phi) +\
                               dqy*numpy.sin(dphi) * numpy.cos(-q_phi))
            else:
                qx_res = qx +  dqx*numpy.cos(dphi)
                qy_res = qy +  dqy*numpy.sin(dphi)
            
        ## Evaluate all points
        val = self.model.evalDistribution([qx_res, qy_res]) 
        ## Reshape into 2d array to use numpy weighted averaging
        value_res= val.reshape(n_bins, len(self.qx_data))
        ## Averaging with Gaussian weighting: normalization included.
        value =numpy.average(value_res,axis=0, weights=weight_res)
        ## Return the smeared values in the range of self.index
        return value
"""    
if __name__ == '__main__':
    ## Test w/ 2D linear function
    x = 0.001*numpy.arange(1, 11)
    dx = numpy.ones(len(x))*0.0003
    y = 0.001*numpy.arange(1, 11)
    dy = numpy.ones(len(x))*0.001
    z = numpy.ones(10)
    dz = numpy.sqrt(z)
    
    from sas.sascalc.dataloader import Data2D
    #for i in range(10): print i, 0.001 + i*0.008/9.0 
    #for i in range(100): print i, int(math.floor( (i/ (100/9.0)) )) 
    out = Data2D()
    out.data = z
    out.qx_data = x
    out.qy_data = y
    out.dqx_data = dx
    out.dqy_data = dy
    out.q_data = numpy.sqrt(dx * dx + dy * dy)
    index = numpy.ones(len(x), dtype = bool)
    out.mask = index
    from sas.models.LineModel import LineModel
    model = LineModel()
    model.setParam("A", 0)

    smear = Smearer2D(out, model, index)
    #smear.set_accuracy('Xhigh')
    value = smear.get_value()
    ## All data are ones, so the smeared should also be ones.
    print "Data length =", len(value)
    print " 2D linear function, I = 0 + 1*qy"
    text = " Gaussian weighted averaging on a 2D linear function will "
    text += "provides the results same as without the averaging."
    print text
    print "qx_data", "qy_data", "I_nonsmear", "I_smeared"
    for ind in range(len(value)):
        print x[ind], y[ind], model.evalDistribution([x, y])[ind], value[ind]
        
  
if __name__ == '__main__':
    ## Another Test w/ constant function
    x = 0.001*numpy.arange(1,11)
    dx = numpy.ones(len(x))*0.001
    y = 0.001*numpy.arange(1,11)
    dy = numpy.ones(len(x))*0.001
    z = numpy.ones(10)
    dz = numpy.sqrt(z)
    
    from DataLoader import Data2D
    #for i in range(10): print i, 0.001 + i*0.008/9.0 
    #for i in range(100): print i, int(math.floor( (i/ (100/9.0)) )) 
    out = Data2D()
    out.data = z
    out.qx_data = x
    out.qy_data = y
    out.dqx_data = dx
    out.dqy_data = dy
    index = numpy.ones(len(x), dtype = bool)
    out.mask = index
    from sas.models.Constant import Constant
    model = Constant()

    value = Smearer2D(out,model,index).get_value()
    ## All data are ones, so the smeared values should also be ones.
    print "Data length =",len(value), ", Data=",value
"""    

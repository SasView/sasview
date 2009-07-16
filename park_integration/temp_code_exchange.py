"""
    This file is intended to be a temporary file to communicate in-progress code 
    to the developers. 
    This file should be removed after its content has been used by the team.
"""


# This code belongs in AbstractFitEngine
class FitData1D:
    def setFitRange(self,qmin=None,qmax=None):
        """ 
            Change the fit range.
            Take into account the fact that if smearing is applied, 
            a wider range in unsmeared Q might be necessary to cover
            the smeared (observed) Q range.        
        """
        
        # Skip Q=0 point, (especially for y(q=0)=None at x[0]).
        #ToDo: Fix this.
        if qmin==0.0 and not numpy.isfinite(self.data.y[qmin]):
            self.qmin = min(self.data.x[self.data.x!=0])
        elif qmin!=None:                       
            self.qmin = qmin            

        if qmax !=None:
            self.qmax = qmax
            
        # Range used for input to smearing
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax    
        
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        if self.smearer.__class__.__name__ == 'SlitSmearer':
            # The entries in the slit smearer matrix remain
            # large across all bins, so we keep the full Q range.
            self._qmin_unsmeared = min(self.data.x)
            self._qmax_unsmeared = max(self.data.x)
        elif self.smearer.__class__.__name__ == 'QSmearer':
            # Take 3 sigmas as the offset between smeared and unsmeared space.
            try:
                offset = 3.0*max(self.smearer.width)
                self._qmin_unsmeared = max([min(self.data.x), self.qmin-offset])
                self._qmax_unsmeared = min([max(self.data.x), self.qmax+offset])
            except:
                logging.error("FitData1D.setFitRange: %s" % sys.exc_value)
        

    def residuals(self, fn):
        """ 
            Compute residuals.
            
            If self.smearer has been set, use if to smear
            the data before computing chi squared.
            
            This is a version based on the current version of residuals.
            
            It takes into account the fact that the unsmearing range
            might need to be wider than the smeared (observed) range.
            
            @param fn: function that return model value
            @return residuals
        """
        x,y = [numpy.asarray(v) for v in (self.x,self.y)]
        if self.dy ==None or self.dy==[]:
            dy= numpy.zeros(len(y))  
        else:
            dy= numpy.asarray(dy)
     
        dy[dy==0]=1
        idx_unsmeared = (x>=self._qmin_unsmeared) & (x <= self._qmax_unsmeared)
  
        # Compute theory data f(x)
        idx=[]
        tempy=[]
        tempfx=[]
        tempdy=[]
    
        _first_bin = None
        for i_x in range(len(x)):
            try:
                if idx_unsmeared[i_x]==True:
                    if _first_bin is None:
                        _first_bin = i_x
                    
                    value= fn(x[i_x])
                    idx.append(x[i_x]>=self.qmin and x[i_x]<=self.qmax)
                    tempfx.append( value)
                    tempy.append(y[i_x])
                    tempdy.append(dy[i_x])
            except:
                ## skip error for model.run(x)
                pass
                 
        ## Smear theory data
        # The tempfx array has a length limited by the Q range.
        if self.smearer is not None:
            tempfx = self.smearer(tempfx, _first_bin)
       
        newy = numpy.asarray(tempy)
        newfx= numpy.asarray(tempfx)
        newdy= numpy.asarray(tempdy)
       
        ## Sanity check
        if numpy.size(newdy)!= numpy.size(newfx):
            raise RuntimeError, "FitData1D: invalid error array %d <> %d" % (numpy.size(newdy), numpy.size(newfx))

        return (newy[idx]-newfx[idx])/newdy[idx]
     
     
    def residuals_alt(self, fn):
        """ 
            Compute residuals.
            
            If self.smearer has been set, use if to smear
            the data before computing chi squared.
            
            This is a more streamlined version of the above. To use this version,
            the _BaseSmearer class below needs to be modified to have its __call__
            method have the following signature:
            
            __call__(self, iq, first_bin, last_bin)
            
            This is because we are storing results in arrays of a length
            corresponding to the full Q-range.
            
            It takes into account the fact that the unsmearing range
            might need to be wider than the smeared (observed) range.            
            
            @param fn: function that return model value
            @return residuals
        """
        # Make sure the arrays are numpy arrays, which are
        # expected by the fitter.
        x,y = [numpy.asarray(v) for v in (self.x,self.y)]
        if self.dy ==None or self.dy==[]:
            dy= numpy.zeros(len(y))  
        else:
            dy= numpy.asarray(dy)
     
        dy[dy==0]=1
        idx = (x>=self.qmin) & (x <= self.qmax)
        idx_unsmeared = (x>=self._qmin_unsmeared) & (x <= self._qmax_unsmeared)
  
        # Compute theory data f(x)
        fx= numpy.zeros(len(x))
    
        # First and last bins of the array, corresponding to
        # the Q range to be smeared
        _first_bin = None
        _last_bin  = None
        for i_x in range(len(x)):
            try:
                if idx_unsmeared[i_x]==True:
                    if _first_bin is None:
                        _first_bin = i_x
                    else:
                        _last_bin  = i_x
                    
                    value = fn(x[i_x])
                    fx[i_x] = value
            except:
                ## skip error for model.run(x)
                ## Should properly log the error
                pass
                 
        # Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, _first_bin, _last_bin)
       
        # Sanity check
        if numpy.size(dy)!= numpy.size(fx):
            raise RuntimeError, "FitData1D: invalid error array %d <> %d" % (numpy.size(dy), numpy.size(fx))

        # Return the residuals for the smeared (observed) Q range
        return (y[idx]-fx[idx])/dy[idx]
     
# The following code belongs in DataLoader.qsmearing
class _BaseSmearer(object):
    
    def __init__(self):
        self.nbins = 0
        self._weights = None
        
    def _compute_matrix(self): return NotImplemented

    def __call__(self, iq, first_bin=0):
        """
            Return the smeared I(q) value at the given q.
            The smeared I(q) is computed using a predetermined 
            smearing matrix for a particular binning.
        
            @param q: I(q) array
            @param first_bin: first bin of the given iq array if shorter than full data length
            @return: smeared I(q)
        """
        # Sanity check
        if len(iq)+first_bin > self.nbins:
            raise RuntimeError, "Invalid I(q) vector: inconsistent array length %s > %s" % (str(len(iq)+first_bin), str(self.nbins))
        
        if self._weights == None:
            self._compute_matrix()
            
        iq_smeared = numpy.zeros(len(iq))
        # Loop over q-values
        idwb=[]
        
        for q_i in range(len(iq)):
            sum = 0.0
            counts = 0.0  
            for i in range(len(iq)):
                if iq[i]==0 or self._weights[q_i+first_bin][i+first_bin]==0:
                    continue
                else:
                    sum += iq[i] * self._weights[q_i+first_bin][i+first_bin] 
                    counts += self._weights[q_i+first_bin][i+first_bin]
            
            if counts == 0:
                iq_smeared[q_i] = 0
            else:
                iq_smeared[q_i] = sum/counts 
        return iq_smeared              
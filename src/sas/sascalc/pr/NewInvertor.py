import numpy as np

# TODO: Add docstrings later

class NewInvertor():

    def __init__(self):
        self.init_default_values()

    def init_default_values(self):
        ## Chisqr of the last computation
        self.chi2 = 0
        ## Time elapsed for last computation
        self.elapsed = 0
        ## Alpha to get the reg term the same size as the signal
        self.suggested_alpha = 0.0
        ## Last number of base functions used
        self.nfunc = 10
        ## Last output values
        self.out = None
        ## Last errors on output values
        self.cov = None
        ## Background value
        self.background = 0
        ## TODO: My suspicion is that this'll go.
        ## Information dictionary for application use
        self.info = {}

        # Stuff that was on p_invertor

        #Maximum distance between any two points in the system
        self.dmax = 180
        #Minimum q to include in inversion
        self.q_min = 0
        #Maximum q to include in inversion
        self.q_max = np.inf
        #Flag for whether or not to evaluate a constant background
        #while inverting
        self.est_bck = 0
        self.alpha = 0.0

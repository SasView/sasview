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

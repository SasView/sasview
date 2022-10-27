from bumps import fitters, options


class Fitting:
    def __init__(self):
        self.DEFAULT_OPTIMIZER = fitters.MPFit.id
        self.FITTERS = fitters.FITTERS
        self.FIT_CONFIG = options.FIT_CONFIG


fitting = Fitting()

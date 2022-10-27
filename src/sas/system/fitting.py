from bumps import fitters


class Fitting:
    def __init__(self):
        self.DEFAULT_OPTIMIZER = fitters.MPFit.id


fitting = Fitting()

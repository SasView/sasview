from bumps import fitters


class FittingConfig:
    def __init__(self):
        self.DEFAULT_OPTIMIZER = fitters.MPFit.id


fitting = FittingConfig()

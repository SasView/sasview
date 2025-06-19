import numpy as np

def sinc(x) -> np.ndarray:
    """
    function for calculating sinc = sin(x)/x
    numpy.sinc is defined as sinc(x) = sin(pi*x)/(pi*x)
    """
    return np.sinc(x / np.pi)   
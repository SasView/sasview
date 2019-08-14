import numpy as np

#libfunc.c's methods -
#Sine integral function, don't think will be needed, scipy.special.sici?
def Si():
    pass

#np.sinc()
def sinc():
    pass

#np.math.factorial
def factorial():
    pass

#defines structure, with a global free, call_msld
#Doesn't need to be a class? Originally had seperate variables for complex/real component
#of two numbers re_ud im_ud, assuming.
class polar_sld():
    uu = np.complex(0)
    dd = np.complex(0)

    def __init__(self):
        pass

#librefl.c definitions -
#defines matrix of 4 complex numbers, just use numpy array of complex numbers?
class matrix():
    a = np.complex(0)
    b = np.complex(0)
    c = np.complex(0)
    d = np.complex(0)

#and defines custom interface of complex numbers, just use np.complex methods. Defines
#cmplx * + / **, sqrt etc. etc. omitted for now.

def intersldfunc():
    pass

def interfunc():
    pass

def linePq():
    pass

#needs other private functions for these as well. May be able to use numpy for some of these.


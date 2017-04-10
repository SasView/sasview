from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.dataloader.data_info import Data1D
from scipy.fftpack import dct
import numpy as np
from time import sleep

class FourierThread(CalcThread):
    def __init__(self, raw_data, extrapolated_data, bg, updatefn=None,
        completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        self.data = raw_data
        self.background = bg
        self.extrapolation = extrapolated_data

    def compute(self):
        qs = self.extrapolation.x
        iqs = self.extrapolation.y
        q = self.data.x
        background = self.background

        self.ready(delay=0.0)
        self.update(msg="Starting Fourier transform.")
        self.ready(delay=0.0)
        if self.isquit():
            return
        try:
            gamma = dct((iqs-background)*qs**2)
            gamma = gamma / gamma.max()
        except:
            self.update(msg="Fourier transform failed.")
            self.complete(transform=None)
            return
        if self.isquit():
            return
        self.update(msg="Fourier transform completed.")

        xs = np.pi*np.arange(len(qs),dtype=np.float32)/(q[1]-q[0])/len(qs)
        transform = Data1D(xs, gamma)

        self.complete(transform=transform)

class HilbertThread(CalcThread):
    def __init__(self, raw_data, extrapolated_data, bg, updatefn=None,
        completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        self.data = raw_data
        self.background = bg
        self.extrapolation = extrapolated_data

    def compute(self):
        qs = self.extrapolation.x
        iqs = self.extrapolation.y
        q = self.data.x
        background = self.background

        self.ready(delay=0.0)
        self.update(msg="Starting Hilbert transform.")
        self.ready(delay=0.0)
        if self.isquit():
            return

        # TODO: Implement hilbert transform

        self.update(msg="Hilbert transform completed.")

        self.complete(transform=None)

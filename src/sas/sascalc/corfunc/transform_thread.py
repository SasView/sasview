from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.dataloader.data_info import Data1D
from scipy.fftpack import dct
from scipy.integrate import trapz, cumtrapz
import numpy as np
from time import sleep

class FourierThread(CalcThread):
    def __init__(self, raw_data, extrapolated_data, bg, updatefn=None,
        completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        self.data = raw_data
        self.background = bg
        self.extrapolation = extrapolated_data

    def check_if_cancelled(self):
        if self.isquit():
            self.update("Fourier transform cancelled.")
            self.complete(transforms=None)
            return True
        return False

    def compute(self):
        qs = self.extrapolation.x
        iqs = self.extrapolation.y
        q = self.data.x
        background = self.background

        xs = np.pi*np.arange(len(qs),dtype=np.float32)/(q[1]-q[0])/len(qs)

        self.ready(delay=0.0)
        self.update(msg="Fourier transform in progress.")
        self.ready(delay=0.0)

        if self.check_if_cancelled(): return
        try:
            # ----- 1D Correlation Function -----
            gamma1 = dct((iqs-background)*qs**2)
            Q = gamma1.max()
            gamma1 /= Q

            if self.check_if_cancelled(): return

            # ----- 3D Correlation Function -----
            # gamma3(R) = 1/R int_{0}^{R} gamma1(x) dx
            # trapz uses the trapezium rule to calculate the integral
            mask = xs <= 200.0 # Only calculate gamma3 up to x=200 (as this is all that's plotted)
            # gamma3 = [trapz(gamma1[:n], xs[:n])/xs[n-1] for n in range(2, len(xs[mask]) + 1)]j
            # gamma3.insert(0, 1.0) # Gamma_3(0) is defined as 1
            n = len(xs[mask])
            gamma3 = cumtrapz(gamma1[:n], xs[:n])/xs[1:n]
            gamma3 = np.hstack((1.0, gamma3)) # Gamma_3(0) is defined as 1

            if self.check_if_cancelled(): return

            # ----- Interface Distribution function -----
            idf = dct(-qs**4 * (iqs-background))

            if self.check_if_cancelled(): return

            # Manually calculate IDF(0.0), since scipy DCT tends to give us a
            # very large negative value.
            # IDF(x) = int_0^inf q^4 * I(q) * cos(q*x) * dq
            # => IDF(0) = int_0^inf q^4 * I(q) * dq
            idf[0] = trapz(-qs**4 * (iqs-background), qs)
            idf /= Q # Normalise using scattering invariant

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(e)

            self.update(msg="Fourier transform failed.")
            self.complete(transforms=None)
            return
        if self.isquit():
            return
        self.update(msg="Fourier transform completed.")

        transform1 = Data1D(xs, gamma1)
        transform3 = Data1D(xs[xs <= 200], gamma3)
        idf = Data1D(xs, idf)

        transforms = (transform1, transform3, idf)

        self.complete(transforms=transforms)

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

        self.complete(transforms=None)

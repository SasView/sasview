from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.dataloader.data_info import Data1D
from scipy.fftpack import dct
from scipy.integrate import trapz
import numpy as np
from time import sleep

class FourierThread(CalcThread):
    def __init__(self, raw_data, extrapolated_data, bg, extrap_fn=None,
        updatefn=None, completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        self.data = raw_data
        self.background = bg
        self.extrapolation = extrapolated_data
        self.extrap_fn = extrap_fn

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
            gamma1 = gamma1 / gamma1.max()

            if self.check_if_cancelled(): return

            # ----- 3D Correlation Function -----
            # gamma3(R) = 1/R int_{0}^{R} gamma1(x) dx
            # trapz uses the trapezium rule to calculate the integral
            mask = xs <= 200.0 # Only calculate gamma3 up to x=200 (as this is all that's plotted)
            gamma3 = [trapz(gamma1[:n], xs[:n])/xs[n-1] for n in range(2, len(xs[mask]) + 1)]
            gamma3.insert(0, 1.0) # Gamma_3(0) is defined as 1
            gamma3 = np.array(gamma3)

            if self.check_if_cancelled(): return

            # ----- Interface Distribution function -----
            dmax = 200.0 # Max real space value to calculate IDF up to
            dstep = 0.5
            qmax = 1.0 # Max q value to integrate up to when calculating IDF

            # Units of x axis depend on qmax (for some reason?). This scales
            # the xgamma array appropriately, since qmax was set to 0.6 in
            # the original fortran code.
            x_scale = qmax / 0.6

            xgamma = np.arange(0, dmax/x_scale, step=dstep/x_scale)
            idf = np.zeros(len(xgamma))

            # nth moment = integral(q^n * I(q), q=0, q=inf)
            moment = np.zeros(5)
            for n in range(5):
                integrand = qs**n * (iqs-background)
                moment[n] = trapz(integrand[qs < qmax], qs[qs < qmax])
                if self.check_if_cancelled(): return

            # idf(x) = -integral(q^4 * I(q)*cos(qx), q=0, q=inf) / 2nd moment
            # => idf(0) = -integral(q^4 * I(q), 0, inf) / (2nd moment)
            #  = -(4th moment)/(2nd moment)
            idf[0] = -moment[4] / moment[2]
            for i in range(1, len(xgamma)):
                d = xgamma[i]

                integrand = -qs**4 * (iqs-background) * np.cos(d*qs)
                idf[i] = trapz(integrand[qs < qmax], qs[qs < qmax])
                idf[i] /= moment[2]
                if self.check_if_cancelled(): return

            xgamma *= x_scale

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
        idf = Data1D(xgamma, idf)

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

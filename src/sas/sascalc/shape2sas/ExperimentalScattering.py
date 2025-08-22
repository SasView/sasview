from dataclasses import dataclass, field

import numpy as np

from sas.sascalc.shape2sas.Typing import *


@dataclass
class SimulateScattering:
    """Class containing parameters for
    simulating scattering"""

    q: np.ndarray
    I0: np.ndarray
    I: np.ndarray
    exposure: float | None = field(default_factory=lambda:500.0)


@dataclass
class SimulatedScattering:
    """Class containing parameters for
    simulated scattering"""

    I_sim: np.ndarray
    q: np.ndarray
    I_err: np.ndarray

class IExperimental:
    def __init__(self, 
                 q: np.ndarray, 
                 I0: np.ndarray, 
                 I: np.ndarray, 
                 exposure: float):
        self.q = q
        self.I0 = I0
        self.I = I
        self.exposure = exposure

    def simulate_data(self) -> Vector2D:
        """
        Simulate SAXS data using calculated scattering and empirical expression for sigma

        input
        q,I      : calculated scattering, normalized
        I0       : forward scattering
        #noise   : relative noise (scales the simulated sigmas by a factor)
        exposure : exposure (in arbitrary units) - affects the noise level of data

        output
        sigma    : simulated noise
        Isim     : simulated data

        data is also written to a file
        """

        ## simulate exp error
        #input, sedlak errors (https://doi.org/10.1107/S1600576717003077)
        #k = 5000000
        #c = 0.05
        #sigma = noise*np.sqrt((I+c)/(k*q))

        ## simulate exp error, other approach, also sedlak errors

        # set constants
        k = 4500
        c = 0.85

        # convert from intensity units to counts
        scale = self.exposure
        I_sed = scale * self.I0 * self.I

        # make N
        N = k * self.q # original expression from Sedlak2017 paper

        qt = 1.4 # threshold - above this q value, the linear expression do not hold
        a = 3.0 # empirical constant 
        b = 0.6 # empirical constant
        idx = np.where(self.q > qt)
        N[idx] = k * qt * np.exp(-0.5 * ((self.q[idx] - qt) / b)**a)

        # make I(q_arb)
        q_max = np.amax(self.q)
        q_arb = 0.3
        if q_max <= q_arb:
           I_sed_arb = I_sed[-2]
        else: 
            idx_arb = np.where(self.q > q_arb)[0][0]
            I_sed_arb = I_sed[idx_arb]

        # calc variance and sigma
        v_sed = (I_sed + 2 * c * I_sed_arb / (1 - c)) / N
        sigma_sed = np.sqrt(v_sed)

        # rescale
        #sigma = noise * sigma_sed/scale
        sigma = sigma_sed / scale

        ## simulate data using errors
        mu = self.I0 * self.I
        Isim = np.random.normal(mu, sigma)

        return Isim, sigma

    def save_Iexperimental(self, Isim: np.ndarray, sigma: np.ndarray, Model: str):
        with open('Isim%s.dat' % Model,'w') as f:
            f.write('# Simulated data\n')
            f.write('# sigma generated using Sedlak et al, k=100000, c=0.55, https://doi.org/10.1107/S1600576717003077, and rebinned with 10 per bin)\n')
            f.write('# %-12s %-12s %-12s\n' % ('q','I','sigma'))
            for i in range(len(Isim)):
                f.write('  %-12.5e %-12.5e %-12.5e\n' % (self.q[i], Isim[i], sigma[i]))


def getSimulatedScattering(scalc: SimulateScattering) -> SimulatedScattering:
    """Simulate scattering for a given theoretical scattering."""

    Isim_class = IExperimental(scalc.q, scalc.I0, scalc.I, scalc.exposure)
    I_sim, I_err = Isim_class.simulate_data()

    return SimulatedScattering(I_sim=I_sim, q=scalc.q, I_err=I_err)
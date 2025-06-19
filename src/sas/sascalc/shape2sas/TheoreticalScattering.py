from sas.sascalc.shape2sas.Typing import *
from sas.sascalc.shape2sas.HelperFunctions import sinc

from dataclasses import dataclass
from sas.sascalc.shape2sas.Models import ModelSystem, SimulationParameters
import numpy as np

@dataclass
class TheoreticalScatteringCalculation:
    """Class containing parameters for simulating
    scattering for a given model system"""

    System: ModelSystem
    Calculation: SimulationParameters


@dataclass
class TheoreticalScattering:
    """Class containing parameters for
    theoretical scattering"""

    q: np.ndarray
    I0: np.ndarray
    I: np.ndarray
    S_eff: np.ndarray

class WeightedPairDistribution:
    def __init__(self, x: np.ndarray, 
                       y: np.ndarray, 
                       z: np.ndarray, 
                       p: np.ndarray):
        self.x = x
        self.y = y
        self.z = z
        self.p = p #contrast

    @staticmethod
    def calc_dist(x: np.ndarray) -> np.ndarray:
        """
        calculate all distances between points in an array
        """
        # mesh this array so that you will have all combinations
        m, n = np.meshgrid(x, x, sparse=True)
        # get the distance via the norm
        dist = abs(m - n) 
        return dist

    def calc_all_dist(self) -> np.ndarray:
        """ 
        calculate all pairwise distances
        calls calc_dist() for each set of coordinates: x,y,z
        does a square sum of coordinates
        convert from matrix to 
        """

        square_sum = 0
        for arr in [self.x, self.y, self.z]:
            square_sum += self.calc_dist(arr)**2 #arr will input x_new, then y_new and z_new so you get 
                                            #x_new^2 + y_new^2 + z_new^2
        d = np.sqrt(square_sum)             #then the square root is taken to get avector for the distance
        # convert from matrix to array
        # reshape is slightly faster than flatten() and ravel()
        dist = d.reshape(-1)
        # reduce precision, for computational speed
        dist = dist.astype('float32')

        return dist

    def calc_all_contrasts(self) -> np.ndarray:
        """
        calculate all pairwise contrast products
        of p: all contrasts 
        """

        dp = np.outer(self.p, self.p)
        contrast = dp.reshape(-1)
        contrast = contrast.astype('float32')
        return contrast

    @staticmethod
    def generate_histogram(dist: np.ndarray, contrast: np.ndarray, r_max: float, Nbins: int) -> Vector2D:
        """
        make histogram of point pairs, h(r), binned after pair-distances, r
        used for calculating scattering (fast Debye)

        input
        dist     : all pairwise distances
        Nbins    : number of bins in h(r)
        contrast : contrast of points
        r_max    : max distance to include in histogram

        output
        r        : distances of bins
        histo    : histogram, weighted by contrast

        """

        histo, bin_edges = np.histogram(dist, bins=Nbins, weights=contrast, range=(0, r_max)) 
        dr = bin_edges[2] - bin_edges[1]
        r = bin_edges[0:-1] + dr / 2

        return r, histo

    @staticmethod
    def calc_Rg(r: np.ndarray, pr: np.ndarray) -> float:
        """ 
        calculate Rg from r and p(r)
        """
        sum_pr_r2 = np.sum(pr * r**2)
        sum_pr = np.sum(pr)
        Rg = np.sqrt(abs(sum_pr_r2 / sum_pr) / 2)

        return Rg
    
    def calc_hr(self, 
                dist: np.ndarray, 
                Nbins: int, 
                contrast: np.ndarray, 
                polydispersity: float) -> Vector2D:
        """
        calculate h(r)
        h(r) is the contrast-weighted histogram of distances, including self-terms (dist = 0)

        input: 
        dist      : all pairwise distances
        contrast  : all pair-wise contrast products
        polydispersity: relative polydispersity, float

        output:
        hr        : pair distance distribution function 
        """

        ## make r range in h(r) histogram slightly larger than Dmax
        ratio_rmax_dmax = 1.05

        ## calc h(r) with/without polydispersity
        if polydispersity > 0.0:
            Dmax = np.amax(dist) * (1 + 3 * polydispersity)
            r_max = Dmax * ratio_rmax_dmax
            r, hr_1 = self.generate_histogram(dist, contrast, r_max, Nbins)
            N_poly_integral = 10
            factor_range = 1 + np.linspace(-3, 3, N_poly_integral) * polydispersity
            hr, norm = 0, 0
            for factor_d in factor_range:
                if factor_d == 1.0:
                    hr += hr_1
                    norm += 1
                else:
                    _, dhr = self.generate_histogram(dist * factor_d, contrast, r_max, Nbins)
                    #dhr = histogram1d(dist * factor_d, bins=Nbins, weights=contrast, range=(0,r_max))
                    res = (1.0 - factor_d) / polydispersity
                    w = np.exp(-res**2 / 2.0) # weight: normal distribution
                    vol = factor_d**3 # weight: relative volume, because larger particles scatter more
                    hr += dhr * w * vol**2
                    norm += w * vol**2
            hr /= norm
        else:
            Dmax = np.amax(dist)
            r_max = Dmax * ratio_rmax_dmax
            r, hr = self.generate_histogram(dist, contrast, r_max, Nbins)

        # print Dmax
        print(f"        Dmax: {Dmax:.3e} A")

        return r, hr

    def calc_pr(self, Nbins: int, polydispersity: float) -> Vector3D:
        """
        calculate p(r)
        p(r) is the contrast-weighted histogram of distances, without the self-terms (dist = 0)

        input: 
        dist      : all pairwise distances
        contrast  : all pair-wise contrast products
        polydispersity: boolian, True or False

        output:
        pr        : pair distance distribution function
        """
        dist = self.calc_all_dist()
        contrast = self.calc_all_contrasts()

        ## calculate pr
        idx_nonzero = np.where(dist > 0.0) #  nonzero elements
        r, pr = self.calc_hr(dist[idx_nonzero], Nbins, contrast[idx_nonzero], polydispersity)

        ## normalize so pr_max = 1
        pr_norm = pr / np.amax(pr)

        ## calculate Rg
        Rg = self.calc_Rg(r, pr_norm)
        print(f"        Rg  : {Rg:.3e} A")

        #returned N values after generating
        pr /= len(self.x)**2 #NOTE: N_total**2

        #NOTE: If Nreps is to be added from the original code
        #Then r_sum, pr_sum and pr_norm_sum should be added here

        return r, pr, pr_norm 
    
    @staticmethod
    def save_pr(Nbins: int,
                r: np.ndarray, 
                pr_norm: np.ndarray, 
                Model: str):
        """
        save p(r) to textfile
        """
        with open('pr%s.dat' % Model,'w') as f:
            f.write('# %-17s %-17s\n' % ('r','p(r)'))
            for i in range(Nbins):
                f.write('  %-17.5e %-17.5e\n' % (r[i], pr_norm[i]))


class ITheoretical:
    def __init__(self, q: np.ndarray):
        self.q = q

    def calc_Pq(self, r: np.ndarray, pr: np.ndarray, conc: float, volume_total: float) -> Vector2D:
        """
        calculate form factor, P(q), and forward scattering, I(0), using pair distribution, p(r) 
        """
        ## calculate P(q) and I(0) from p(r)
        I0, Pq = 0, 0
        for (r_i, pr_i) in zip(r, pr):
            I0 += pr_i
            qr = self.q * r_i
            Pq += pr_i * sinc(qr)
    
        # normalization, P(0) = 1
        if I0 == 0:
            I0 = 1E-5
        elif I0 < 0:
            I0 = abs(I0)
        Pq /= I0

        # make I0 scale with volume fraction (concentration) and 
        # volume squared and scale so default values gives I(0) of approx unity

        I0 *= conc * volume_total * 1E-4

        return I0, Pq

    def calc_Iq(self, Pq: np.ndarray, 
                S_eff: np.ndarray, 
                sigma_r: float) -> np.ndarray:
        """
        calculates intensity
        """

        ## save structure factor to file
        #self.save_S(self.q, S_eff, Model)

        ## multiply formfactor with structure factor
        I = Pq * S_eff

        ## interface roughness (Skar-Gislinge et al. 2011, DOI: 10.1039/c0cp01074j)
        if sigma_r > 0.0:
            roughness = np.exp(-(self.q * sigma_r)**2 / 2)
            I *= roughness

        return I

    def save_I(self, I: np.ndarray, Model: str):
        """Save theoretical intensity to file"""

        with open('Iq%s.dat' % Model,'w') as f:
            f.write('# Calculated data\n')
            f.write('# %-12s %-12s\n' % ('q','I'))
            for i in range(len(I)):
                f.write('  %-12.5e %-12.5e\n' % (self.q[i], I[i]))

import numpy as np
import matplotlib.pyplot as plt
from sas.sascalc.shape2sas.Typing import *
from sas.sascalc.shape2sas.models import *
from sas.sascalc.shape2sas.Math import sinc

################################ Shape2SAS helper functions ###################################
class Qsampling:
    def onQsampling(qmin: float, qmax: float, Nq: int) -> np.ndarray:
        """Returns uniform q sampling"""
        return np.linspace(qmin, qmax, Nq)

    def onUserSampledQ(q: np.ndarray) -> np.ndarray:
        """Returns user sampled q"""
        if isinstance(q, list):
            q = np.array(q)
        return q

    def qMethodsNames(name: str):
        methods = {
            "Uniform": Qsampling.onQsampling,
            "User_sampled": Qsampling.onUserSampledQ
        }
        return methods[name]
    
    def qMethodsInput(name: str):
        inputs = {
            "Uniform": {"qmin": 0.001, "qmax": 0.5, "Nq": 400},
            "User_sampled": {"q": Qsampling.onQsampling(0.001, 0.5, 400)} #if the user does not input q
        }
        return inputs[name]


class Rotation:
    def __init__(self, x_add: np.ndarray, 
                       y_add: np.ndarray, 
                       z_add: np.ndarray, 
                       alpha: float, 
                       beta: float, 
                       gam: float,
                       rotp_x: float,
                       rotp_y: float,
                       rotp_z: float):
        self.x_add = x_add
        self.y_add = y_add
        self.z_add = z_add
        self.alpha = alpha
        self.beta = beta
        self.gam = gam
        self.rotp_x = rotp_x
        self.rotp_y = rotp_y
        self.rotp_z = rotp_z
    
    def onRotatingPoints(self) -> Vector3D:
        """Simple Euler rotation"""
        self.x_add -= self.rotp_x
        self.y_add -= self.rotp_y
        self.z_add -= self.rotp_z

        x_rot = (self.x_add * np.cos(self.gam) * np.cos(self.beta) 
             + self.y_add * (np.cos(self.gam) * np.sin(self.beta) * np.sin(self.alpha) - np.sin(self.gam) * np.cos(self.alpha)) 
             + self.z_add * (np.cos(self.gam) * np.sin(self.beta) * np.cos(self.alpha) + np.sin(self.gam) * np.sin(self.alpha)))
    
        y_rot = (self.x_add * np.sin(self.gam) * np.cos(self.beta) 
             + self.y_add * (np.sin(self.gam) * np.sin(self.beta) * np.sin(self.alpha) + np.cos(self.gam) * np.cos(self.alpha)) 
             + self.z_add * (np.sin(self.gam) * np.sin(self.beta) * np.cos(self.alpha) - np.cos(self.gam) * np.sin(self.alpha)))

        z_rot = (-self.x_add * np.sin(self.beta)
            + self.y_add * np.cos(self.beta) * np.sin(self.alpha)
            + self.z_add * np.cos(self.beta) * np.cos(self.alpha))
        
        x_rot += self.rotp_x
        y_rot += self.rotp_y
        z_rot += self.rotp_z

        return x_rot, y_rot, z_rot
    
    #More advanced rotation functions can be added here
    #but GeneratePoints should be changed....


class Translation:
    def __init__(self, x_add: np.ndarray, 
                       y_add: np.ndarray, 
                       z_add: np.ndarray, 
                       com_x: float, 
                       com_y: float, 
                       com_z: float):
        self.x_add = x_add
        self.y_add = y_add
        self.z_add = z_add
        self.com_x = com_x
        self.com_y = com_y
        self.com_z = com_z
    
    def onTranslatingPoints(self) -> Vector3D:
        """Translates points"""
        return self.x_add + self.com_x, self.y_add + self.com_y, self.z_add + self.com_z


class GeneratePoints:
    def __init__(self, com: List[float], 
                    subunitClass: object, 
                    dimensions: List[float], 
                    rotation: List[float],
                    rotation_point: list[float],
                    Npoints: int):

        self.com = com
        self.subunitClass = subunitClass
        self.dimensions = dimensions
        self.rotation = rotation
        self.rotation_point = rotation_point
        self.Npoints = Npoints

    def onGeneratingPoints(self) -> Vector3D:
        """Generates the points"""
        x, y, z= self.subunitClass(self.dimensions).getPointDistribution(self.Npoints)
        x, y, z = self.onTransformingPoints(x, y, z)
        return x, y, z
    
    def onTransformingPoints(self, x: np.ndarray, 
                                   y: np.ndarray, 
                                   z: np.ndarray) -> Vector3D:
        """Transforms the points"""
        alpha, beta, gam = self.rotation
        rotp_x, rotp_y, rotp_z = self.rotation_point
        alpha = np.radians(alpha)
        beta = np.radians(beta)
        gam = np.radians(gam)
        com_x, com_y, com_z = self.com

        x, y, z = Rotation(x, y, z, alpha, beta, gam, rotp_x, rotp_y, rotp_z).onRotatingPoints()
        x, y, z = Translation(x, y, z, com_x, com_y, com_z).onTranslatingPoints()
        return x, y, z
    

class GenerateAllPoints:
    def __init__(self, Npoints: int, 
                            com: List[List[float]], 
                        subunits: List[List[float]], 
                        dimensions: List[List[float]], 
                        rotation : List[List[float]],
                        rotation_point: list[float],
                        p: List[float], 
                        exclude_overlap: bool):
        self.Npoints = Npoints
        self.com = com
        self.subunits = subunits
        self.Number_of_subunits = len(subunits)
        self.dimensions = dimensions
        self.rotation = rotation
        self.rotation_point = rotation_point
        self.p_s = p
        self.exclude_overlap = exclude_overlap
        self.setAvailableSubunits()

    def setAvailableSubunits(self):
        """Returns the available subunits"""
        self.subunitClasses = {
                "sphere": Sphere,
                "ball": Sphere,

                "hollow_sphere": HollowSphere, 
                "Hollow sphere": HollowSphere, 

                "cylinder": Cylinder,

                "ellipsoid": Ellipsoid,

                "elliptical_cylinder": EllipticalCylinder,
                "Elliptical cylinder": EllipticalCylinder,

                "disc": Disc,

                "cube": Cube,

                "hollow_cube": HollowCube,
                "Hollow cube": HollowCube,

                "cuboid": Cuboid,

                "cyl_ring": CylinderRing,
                "Cylinder ring": CylinderRing,

                "disc_ring": DiscRing,
                "Disc ring": DiscRing,
                
                "superellipsoid": SuperEllipsoid}

    def getSubunitClass(self, key: str):
        if key in self.subunitClasses:
            return self.subunitClasses[key]
        else:
            try:
                return globals()[key]
            except KeyError:
                raise ValueError(f"Class {key} not found in subunitClasses or global scope")

    @staticmethod
    def onAppendingPoints(x_new: np.ndarray, 
                          y_new: np.ndarray, 
                          z_new: np.ndarray,
                          p_new: np.ndarray, 
                          x_add: np.ndarray, 
                          y_add: np.ndarray, 
                          z_add: np.ndarray, 
                          p_add: np.ndarray) -> Vector4D:
        """append new points to vectors of point coordinates"""
        
        # add points to (x_new,y_new,z_new)
        if isinstance(x_new, int):
            # if these are the first points to append to (x_new,y_new,z_new)
            x_new = x_add
            y_new = y_add
            z_new = z_add
            p_new = p_add
        else:
            x_new = np.append(x_new, x_add)
            y_new = np.append(y_new, y_add)
            z_new = np.append(z_new, z_add)
            p_new = np.append(p_new, p_add)

        return x_new, y_new, z_new, p_new

    @staticmethod
    def onCheckOverlap(x: np.ndarray, 
                       y: np.ndarray, 
                       z: np.ndarray, 
                       p: np.ndarray, 
                       rotation: List[float], 
                       rotation_point: list[float],
                       com: List[float], 
                       subunitClass: object, 
                       dimensions: List[float]):
        """check for overlap with previous subunits. 
        if overlap, the point is removed"""

        if sum(rotation) != 0:
            ## effective coordinates, shifted by (x_com,y_com,z_com)
            x_eff, y_eff, z_eff = Translation(x, y, z, -com[0], -com[1], -com[2]).onTranslatingPoints()

            #rotate backwards with minus rotation angles
            alpha, beta, gam = rotation
            rotp_x, rotp_y, rotp_z = rotation_point
            alpha = np.radians(alpha)
            beta = np.radians(beta)
            gam = np.radians(gam)

            x_eff, y_eff, z_eff = Rotation(x_eff, y_eff, z_eff, -alpha, -beta, -gam, rotp_x, rotp_y, rotp_z).onRotatingPoints()

        else:
            ## effective coordinates, shifted by (x_com,y_com,z_com)
            x_eff, y_eff, z_eff = Translation(x, y, z, -com[0], -com[1], -com[2]).onTranslatingPoints()


        idx = subunitClass(dimensions).checkOverlap(x_eff, y_eff, z_eff)
        x_add, y_add, z_add, p_add = x[idx], y[idx], z[idx], p[idx]

        ## number of excluded points
        N_x = len(x) - len(idx[0])

        return x_add, y_add, z_add, p_add, N_x

    def onGeneratingAllPointsSeparately(self) -> Vector3D:
        """Generating points for all subunits from each built model, but
        save them separately in their own list"""
        volume = []
        sum_vol = 0

        #Get volume of each subunit
        for i in range(self.Number_of_subunits):
            subunitClass = self.getSubunitClass(self.subunits[i])
            v = subunitClass(self.dimensions[i]).getVolume()
            volume.append(v)
            sum_vol += v

        N, rho, N_exclude = [], [], []
        x_new, y_new, z_new, p_new, volume_total = [], [], [], [], 0

        for i in range(self.Number_of_subunits):
            Npoints = int(self.Npoints * volume[i] / sum_vol)

            x_add, y_add, z_add = GeneratePoints(self.com[i], self.getSubunitClass(self.subunits[i]), self.dimensions[i], 
                                                    self.rotation[i], self.rotation_point[i], Npoints).onGeneratingPoints()
            
            #Remaining points
            N_subunit = len(x_add)
            rho_subunit = N_subunit / volume[i]
            p_add = np.ones(N_subunit) * self.p_s[i]

            #Check for overlap with previous subunits
            N_x_sum = 0
            if self.exclude_overlap:
                for j in range(i): 
                    x_add, y_add, z_add, p_add, N_x = self.onCheckOverlap(x_add, y_add, z_add, p_add, self.rotation[j], self.rotation_point[j], 
                                                    self.com[j], self.getSubunitClass(self.subunits[j]), self.dimensions[j])
                    N_x_sum += N_x
    
            N.append(N_subunit)
            rho.append(rho_subunit)
            N_exclude.append(N_x_sum)
            fraction_left = (N_subunit-N_x_sum) / N_subunit
            volume_total += volume[i] * fraction_left

            x_new.append(x_add)
            y_new.append(y_add)
            z_new.append(z_add)
            p_new.append(p_add)
        
        #Show information about the model and its subunits
        N_remain = []
        for j in range(self.Number_of_subunits):
            srho = rho[j] * self.p_s[j]
            N_remain.append(N[j] - N_exclude[j])
            print(f"        {N[j]} points for subunit {j}: {self.subunits[j]}")
            print(f"             Point density     : {rho[j]:.3e} (points per volume)")
            print(f"             Scattering density: {srho:.3e} (density times scattering length)")
            print(f"             Excluded points   : {N_exclude[j]} (overlap region)")
            print(f"             Remaining points  : {N_remain[j]} (non-overlapping region)")

        N_total = sum(N_remain)
        print(f"        Total points in model: {N_total}")
        print(f"        Total volume of model: {volume_total:.3e} A^3")
        print(" ")

        return x_new, y_new, z_new, p_new, volume_total

    def onGeneratingAllPoints(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
        """Generating points for all subunits from each built model"""
        volume = []
        sum_vol = 0
        #Get volume of each subunit
        for i in range(self.Number_of_subunits):
            subunitClass = self.getSubunitClass(self.subunits[i])
            v = subunitClass(self.dimensions[i]).getVolume()
            volume.append(v)
            sum_vol += v
        
        N, rho, N_exclude = [], [], []
        x_new, y_new, z_new, p_new, volume_total = 0, 0, 0, 0, 0

        #Generate subunits
        for i in range(self.Number_of_subunits):
            Npoints = int(self.Npoints * volume[i] / sum_vol)

            x_add, y_add, z_add = GeneratePoints(self.com[i], self.getSubunitClass(self.subunits[i]), self.dimensions[i], 
                                                    self.rotation[i], self.rotation_point, Npoints).onGeneratingPoints()
            
            #Remaining points
            N_subunit = len(x_add)
            rho_subunit = N_subunit / volume[i]
            p_add = np.ones(N_subunit) * self.p_s[i]

            #Check for overlap with previous subunits
            N_x_sum = 0
            if self.exclude_overlap:
                for j in range(i): 
                    x_add, y_add, z_add, p_add, N_x = self.onCheckOverlap(x_add, y_add, z_add, p_add, self.rotation[j], self.rotation_point[j], 
                                                    self.com[j], self.getSubunitClass(self.subunits[j]), self.dimensions[j])
                    N_x_sum += N_x
            
            #Append data
            x_new, y_new, z_new, p_new = self.onAppendingPoints(x_new, y_new, z_new, p_new, x_add, y_add, z_add, p_add)

            N.append(N_subunit)
            rho.append(rho_subunit)
            N_exclude.append(N_x_sum)
            fraction_left = (N_subunit-N_x_sum) / N_subunit
            volume_total += volume[i] * fraction_left

        #Show information about the model and its subunits
        N_remain = []
        for j in range(self.Number_of_subunits):
            srho = rho[j] * self.p_s[j]
            N_remain.append(N[j] - N_exclude[j])
            print(f"        {N[j]} points for subunit {j}: {self.subunits[j]}")
            print(f"             Point density     : {rho[j]:.3e} (points per volume)")
            print(f"             Scattering density: {srho:.3e} (density times scattering length)")
            print(f"             Excluded points   : {N_exclude[j]} (overlap region)")
            print(f"             Remaining points  : {N_remain[j]} (non-overlapping region)")

        N_total = sum(N_remain)
        print(f"        Total points in model: {N_total}")
        print(f"        Total volume of model: {volume_total:.3e} A^3")
        print(" ")

        return x_new, y_new, z_new, p_new, volume_total


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


def get_max_dimension(x_list: np.ndarray, y_list: np.ndarray, z_list: np.ndarray) -> float:
    """
    find max dimensions of n models
    used for determining plot limits
    """

    max_x,max_y,max_z = 0, 0, 0
    for i in range(len(x_list)):
        tmp_x = np.amax(abs(x_list[i]))
        tmp_y = np.amax(abs(y_list[i]))
        tmp_z = np.amax(abs(z_list[i]))
        if tmp_x>max_x:
            max_x = tmp_x
        if tmp_y>max_y:
            max_y = tmp_y
        if tmp_z>max_z:
            max_z = tmp_z

    max_l = np.amax([max_x,max_y,max_z])

    return max_l


def plot_2D(x_list: np.ndarray, 
            y_list: np.ndarray, 
            z_list: np.ndarray, 
            p_list: np.ndarray, 
            Models: np.ndarray, 
            high_res: bool) -> None:
    """
    plot 2D-projections of generated points (shapes) using matplotlib:
    positive contrast in red (Model 1) or blue (Model 2) or yellow (Model 3) or green (Model 4)
    zero contrast in grey
    negative contrast in black

    input
    (x_list,y_list,z_list) : coordinates of simulated points
    p_list                 : excess scattering length densities (contrast) of simulated points
    Model                  : Model number

    output
    plot                : points<Model>.png

    """

    ## figure settings
    markersize = 0.5
    max_l = get_max_dimension(x_list, y_list, z_list)*1.1
    lim = [-max_l, max_l]

    for x,y,z,p,Model in zip(x_list,y_list,z_list,p_list,Models):

        ## find indices of positive, zero and negatative contrast
        idx_neg = np.where(p < 0.0)
        idx_pos = np.where(p > 0.0)
        idx_nul = np.where(p == 0.0)

        f,ax = plt.subplots(1, 3, figsize=(12,4))

        ## plot, perspective 1
        ax[0].plot(x[idx_pos], z[idx_pos], linestyle='none', marker='.', markersize=markersize)
        ax[0].plot(x[idx_neg], z[idx_neg], linestyle='none', marker='.', markersize=markersize, color='black')
        ax[0].plot(x[idx_nul], z[idx_nul], linestyle='none', marker='.', markersize=markersize, color='grey')
        ax[0].set_xlim(lim)
        ax[0].set_ylim(lim)
        ax[0].set_xlabel('x')
        ax[0].set_ylabel('z')
        ax[0].set_title('pointmodel, (x,z), "front"')

        ## plot, perspective 2
        ax[1].plot(y[idx_pos], z[idx_pos], linestyle='none', marker='.', markersize=markersize) 
        ax[1].plot(y[idx_neg], z[idx_neg], linestyle='none', marker='.', markersize=markersize, color='black')
        ax[1].plot(y[idx_nul], z[idx_nul], linestyle='none', marker='.', markersize=markersize, color='grey')
        ax[1].set_xlim(lim)
        ax[1].set_ylim(lim)
        ax[1].set_xlabel('y')
        ax[1].set_ylabel('z')
        ax[1].set_title('pointmodel, (y,z), "side"')

        ## plot, perspective 3
        ax[2].plot(x[idx_pos], y[idx_pos], linestyle='none', marker='.', markersize=markersize) 
        ax[2].plot(x[idx_neg], y[idx_neg], linestyle='none', marker='.', markersize=markersize, color='black')
        ax[2].plot(x[idx_nul], y[idx_nul], linestyle='none', marker='.', markersize=markersize, color='grey')    
        ax[2].set_xlim(lim)
        ax[2].set_ylim(lim)
        ax[2].set_xlabel('x')
        ax[2].set_ylabel('y')
        ax[2].set_title('pointmodel, (x,y), "bottom"')
    
        plt.tight_layout()
        if high_res:
            plt.savefig('points%s.png' % Model,dpi=600)
        else:
            plt.savefig('points%s.png' % Model)
        plt.close()


def plot_results(q: np.ndarray, 
                 r_list: List[np.ndarray], 
                 pr_list: List[np.ndarray], 
                 I_list: List[np.ndarray], 
                 Isim_list: List[np.ndarray], 
                 sigma_list: List[np.ndarray], 
                 S_list: List[np.ndarray], 
                 names: List[str], 
                 scales: List[float], 
                 xscale_log: bool, 
                 high_res: bool) -> None:
    """
    plot results for all models, using matplotlib:
    - p(r) 
    - calculated formfactor, P(r) on log-log or log-lin scale
    - simulated noisy data on log-log or log-lin scale

    """
    fig, ax = plt.subplots(1,3,figsize=(12,4))

    zo = 1
    for (r, pr, I, Isim, sigma, S, model_name, scale) in zip (r_list, pr_list, I_list, Isim_list, sigma_list, S_list, names, scales):
        ax[0].plot(r,pr,zorder=zo,label='p(r), %s' % model_name)

        if scale > 1: 
            ax[2].errorbar(q,Isim*scale,yerr=sigma*scale,linestyle='none',marker='.',label=r'$I_\mathrm{sim}(q)$, %s, scaled by %d' % (model_name,scale),zorder=1/zo)
        else:
            ax[2].errorbar(q,Isim*scale,yerr=sigma*scale,linestyle='none',marker='.',label=r'$I_\mathrm{sim}(q)$, %s' % model_name,zorder=zo)

        if S[0] != 1.0 or S[-1] != 1.0:
            ax[1].plot(q, S, linestyle='--', label=r'$S(q)$, %s' % model_name,zorder=0)
            ax[1].plot(q, I, zorder=zo, label=r'$I(q)=P(q)S(q)$, %s' % model_name)
            ax[1].set_ylabel(r'$I(q)=P(q)S(q)$')
        else:
            ax[1].plot(q, I, zorder=zo, label=r'$P(q)=I(q)/I(0)$, %s' % model_name)
            ax[1].set_ylabel(r'$P(q)=I(q)/I(0)$')
        zo += 1

    ## figure settings, p(r)
    ax[0].set_xlabel(r'$r$ [$\mathrm{\AA}$]')
    ax[0].set_ylabel(r'$p(r)$')
    ax[0].set_title('pair distance distribution function')
    ax[0].legend(frameon=False)

    ## figure settings, calculated scattering
    if xscale_log:
        ax[1].set_xscale('log')
    ax[1].set_yscale('log')
    ax[1].set_xlabel(r'$q$ [$\mathrm{\AA}^{-1}$]')
    ax[1].set_title('normalized scattering, no noise')
    ax[1].legend(frameon=False)

    ## figure settings, simulated scattering
    if xscale_log:
        ax[2].set_xscale('log')
    ax[2].set_yscale('log')
    ax[2].set_xlabel(r'$q$ [$\mathrm{\AA}^{-1}$]')
    ax[2].set_ylabel(r'$I(q)$ [a.u.]')
    ax[2].set_title('simulated scattering, with noise')
    ax[2].legend(frameon=True)

    ## figure settings
    plt.tight_layout()
    if high_res:
        plt.savefig('plot.png', dpi=600)
    else:
        plt.savefig('plot.png')
    plt.close()


def generate_pdb(x_list: List[np.ndarray], 
                 y_list: List[np.ndarray], 
                 z_list: List[np.ndarray], 
                 p_list: List[np.ndarray], 
                 Model_list: List[str]) -> None:
    """
    Generates a visualisation file in PDB format with the simulated points (coordinates) and contrasts
    ONLY FOR VISUALIZATION!
    Each bead is represented as a dummy atom
    Carbon, C : positive contrast
    Hydrogen, H : zero contrast
    Oxygen, O : negateive contrast
    information of accurate contrasts not included, only sign
    IMPORTANT: IT WILL NOT GIVE THE CORRECT RESULTS IF SCATTERING IS CACLLUATED FROM THIS MODEL WITH E.G. CRYSOL, PEPSI-SAXS, FOXS, CAPP OR THE LIKE!
    """

    for (x,y,z,p,Model) in zip(x_list, y_list, z_list, p_list, Model_list):
        with open('model%s.pdb' % Model,'w') as f:
            f.write('TITLE    POINT SCATTER : MODEL%s\n' % Model)
            f.write('REMARK   GENERATED WITH Shape2SAS\n')
            f.write('REMARK   EACH BEAD REPRESENTED BY DUMMY ATOM\n')
            f.write('REMARK   CARBON, C : POSITIVE EXCESS SCATTERING LENGTH\n')
            f.write('REMARK   HYDROGEN, H : ZERO EXCESS SCATTERING LENGTH\n')
            f.write('REMARK   OXYGEN, O : NEGATIVE EXCESS SCATTERING LENGTH\n')
            f.write('REMARK   ACCURATE SCATTERING LENGTH DENSITY INFORMATION NOT INCLUDED\n')
            f.write('REMARK   OBS: WILL NOT GIVE CORRECT RESULTS IF SCATTERING IS CALCULATED FROM THIS MODEL WITH E.G CRYSOL, PEPSI-SAXS, FOXS, CAPP OR THE LIKE!\n')
            f.write('REMARK   ONLY FOR VISUALIZATION, E.G. WITH PYMOL\n')
            f.write('REMARK    \n')
            for i in range(len(x)):
                if p[i] > 0:
                    atom = 'C'
                elif p[i] == 0:
                    atom = 'H'
                else:
                    atom = 'O'
                f.write('ATOM  %6i %s   ALA A%6i  %8.3f%8.3f%8.3f  1.00  0.00           %s \n'  % (i,atom,i,x[i],y[i],z[i],atom))
            f.write('END')


def check_unique(A_list: List[float]) -> bool:
    """
    if all elements in a list are unique then return True, else return False
    """
    unique = True
    N = len(A_list)
    for i in range(N):
        for j in range(N):
            if i != j:
                if A_list[i] == A_list[j]:
                    unique = False

    return unique

from sas.sascalc.shape2sas.Typing import *
from sas.sascalc.shape2sas.models import *
from sas.sascalc.shape2sas.HelperFunctions import Qsampling

from dataclasses import dataclass, field
from typing import Optional, List
import numpy as np

@dataclass
class ModelProfile:
    """Class containing parameters for
    creating a particle
    
    NOTE: Default values create a sphere with a 
    radius of 50 Å at the origin.
    """

    subunits: List[str] = field(default_factory=lambda: ['sphere'])
    p_s: List[float] = field(default_factory=lambda: [1.0]) # scattering length density
    dimensions: Vectors = field(default_factory=lambda: [[50]])
    com: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    rotation_points: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    rotation: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    exclude_overlap: Optional[bool] = field(default_factory=lambda: True)


@dataclass
class ModelPointDistribution:
    """Point distribution of a model"""

    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    p: np.ndarray #scattering length density for each point
    volume_total: float


@dataclass
class SimulationParameters:
    """Class containing parameters for
    the simulation itself"""

    q: Optional[np.ndarray] = field(default_factory=lambda: Qsampling.onQsampling(0.001, 0.5, 400))
    prpoints: Optional[int] = field(default_factory=lambda: 100)
    Npoints: Optional[int] = field(default_factory=lambda: 3000)
    #seed: Optional[int] #TODO:Add for future projects
    #method: Optional[str] #generation of point method #TODO: Add for future projects
    model_name: Optional[List[str]] = field(default_factory=lambda: ['Model_1'])


@dataclass
class ModelSystem:
    """Class containing parameters for
    the system"""

    PointDistribution: ModelPointDistribution
    Stype: str = field(default_factory=lambda: "None") #structure factor
    par: List[float] = field(default_factory=lambda: np.array([]))#parameters for structure factor
    polydispersity: float = field(default_factory=lambda: 0.0)#polydispersity
    conc: float = field(default_factory=lambda: 0.02) #concentration
    sigma_r: float = field(default_factory=lambda: 0.0) #interface roughness


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
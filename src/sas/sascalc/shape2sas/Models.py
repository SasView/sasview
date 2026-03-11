from dataclasses import dataclass, field

import numpy as np

from sas.sascalc.shape2sas.HelperFunctions import Qsampling, euler_rotation_matrix
from sas.sascalc.shape2sas.models import (
    Cube,
    Cuboid,
    Cylinder,
    CylinderRing,
    Disc,
    DiscRing,
    Ellipsoid,
    EllipticalCylinder,
    HollowCube,
    HollowSphere,
    Sphere,
    SuperEllipsoid,
)
from sas.sascalc.shape2sas.Typing import Vector3D, Vector4D, Vectors


@dataclass
class ModelProfile:
    """Class containing parameters for
    creating a particle
    
    NOTE: Default values create a sphere with a 
    radius of 50 Å at the origin.
    """

    subunits: list[str] = field(default_factory=lambda: ['sphere'])
    p_s: list[float] = field(default_factory=lambda: [1.0]) # scattering length density
    dimensions: Vectors = field(default_factory=lambda: [[50]])
    com: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    rotation_points: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    rotation: Vectors = field(default_factory=lambda: [[0, 0, 0]])
    exclude_overlap: bool | None = field(default_factory=lambda: True)


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

    q: np.ndarray | None = field(default_factory=lambda: Qsampling.onQsampling(0.001, 0.5, 400))
    prpoints: int | None = field(default_factory=lambda: 100)
    Npoints: int | None = field(default_factory=lambda: 3000)
    #seed: Optional[int] #TODO:Add for future projects
    #method: Optional[str] #generation of point method #TODO: Add for future projects
    model_name: list[str] | None = field(default_factory=lambda: ['Shape2SAS model'])


@dataclass
class ModelSystem:
    """Class containing parameters for
    the system"""

    PointDistribution: ModelPointDistribution
    Stype: str = field(default_factory=lambda: "None") #structure factor
    par: list[float] = field(default_factory=lambda: np.array([]))#parameters for structure factor
    polydispersity: float = field(default_factory=lambda: 0.0)#polydispersity
    conc: float = field(default_factory=lambda: 0.02) #concentration
    sigma_r: float = field(default_factory=lambda: 0.0) #interface roughness


class Rotation:
    def __init__(self, matrix: np.ndarray, center_mass: np.ndarray):
        self.M = matrix        # matrix
        self.cm = center_mass  # center of mass
Translation = np.ndarray

def transform(coords: np.ndarray[Vector3D], translate: Translation = np.array([0, 0, 0]), rotate: Rotation = Rotation(np.eye(3), np.array([0, 0, 0]))):
    """Transform a set of coordinates by a rotation R and translation T"""
    if isinstance(rotate, np.ndarray):
        rotate = Rotation(rotate, np.array([0, 0, 0]))
    assert coords.shape[0] == 3
    assert translate.shape == (3,)
    assert rotate.M.shape == (3, 3)
    assert rotate.cm.shape == (3,)

    # The transform is:
    #   v' = R*(v - R_cm) + R_cm + T
    #      = R*v - R*R_cm + R_cm + T
    #      = R*v + T'

    Tp = -np.dot(rotate.M, rotate.cm) + rotate.cm + translate
    return np.dot(rotate.M, coords) + Tp[:, np.newaxis]


class GeneratePoints:
    def __init__(self, com: list[float],
                    subunitClass: object,
                    dimensions: list[float],
                    rotation: list[float],
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
        # print(f"Generating {self.Npoints} points for subunit {self.subunitClass.__name__} with dimensions {self.dimensions}")
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
        rotation = Rotation(euler_rotation_matrix(alpha, beta, gam), np.array([rotp_x, rotp_y, rotp_z]))
        translation = np.array(self.com)
        return transform(np.vstack([x, y, z]), translation, rotation)


class GenerateAllPoints:
    def __init__(self, Npoints: int,
                            com: list[list[float]],
                        subunits: list[list[float]],
                        dimensions: list[list[float]],
                        rotation : list[list[float]],
                        rotation_point: list[float],
                        p: list[float],
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

            "superellipsoid": SuperEllipsoid
        }

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
    def onCheckOverlap(
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        p: np.ndarray,
        rotation: list[float],
        rotation_point: list[float],
        com: list[float],
        subunitClass: object,
        dimensions: list[float]
    ):
        """check for overlap with previous subunits. 
        if overlap, the point is removed"""

        if any(r != 0 for r in rotation):
            ## effective coordinates, shifted by (x_com,y_com,z_com)
            x_eff, y_eff, z_eff = transform(np.vstack([x, y, z]), translate=np.array([-com[0], -com[1], -com[2]]))

            #rotate backwards with minus rotation angles
            alpha, beta, gam = rotation
            rotp_x, rotp_y, rotp_z = rotation_point
            alpha = np.radians(alpha)
            beta = np.radians(beta)
            gam = np.radians(gam)

            rotation = Rotation(euler_rotation_matrix(-alpha, -beta, -gam), np.array([rotp_x, rotp_y, rotp_z]))
            x_eff, y_eff, z_eff = transform(np.vstack([x_eff, y_eff, z_eff]), rotate=rotation)

        else:
            ## effective coordinates, shifted by (x_com,y_com,z_com)
            x_eff, y_eff, z_eff = transform(np.vstack([x, y, z]), translate=np.array([-com[0], -com[1], -com[2]]))

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
            fraction_left = (N_subunit-N_x_sum) / max(N_subunit, 1)
            volume_total += volume[i] * fraction_left

            x_new.append(x_add)
            y_new.append(y_add)
            z_new.append(z_add)
            p_new.append(p_add)

        #Show information about the model and its subunits
        # N_remain = []
        # for j in range(self.Number_of_subunits):
        #     srho = rho[j] * self.p_s[j]
        #     N_remain.append(N[j] - N_exclude[j])
        #     print(f"        {N[j]} points for subunit {j}: {self.subunits[j]}")
        #     print(f"             Point density     : {rho[j]:.3e} (points per volume)")
        #     print(f"             Scattering density: {srho:.3e} (density times scattering length)")
        #     print(f"             Excluded points   : {N_exclude[j]} (overlap region)")
        #     print(f"             Remaining points  : {N_remain[j]} (non-overlapping region)")

        # N_total = sum(N_remain)
        # print(f"        Total points in model: {N_total}")
        # print(f"        Total volume of model: {volume_total:.3e} A^3")
        # print(" ")

        return x_new, y_new, z_new, p_new, volume_total

    def onGeneratingAllPoints(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
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
        # N_remain = []
        # for j in range(self.Number_of_subunits):
        #     srho = rho[j] * self.p_s[j]
        #     N_remain.append(N[j] - N_exclude[j])
        #     print(f"        {N[j]} points for subunit {j}: {self.subunits[j]}")
        #     print(f"             Point density     : {rho[j]:.3e} (points per volume)")
        #     print(f"             Scattering density: {srho:.3e} (density times scattering length)")
        #     print(f"             Excluded points   : {N_exclude[j]} (overlap region)")
        #     print(f"             Remaining points  : {N_remain[j]} (non-overlapping region)")

        # N_total = sum(N_remain)
        # print(f"        Total points in model: {N_total}")
        # print(f"        Total volume of model: {volume_total:.3e} A^3")
        # print(" ")

        return x_new, y_new, z_new, p_new, volume_total


def getPointDistribution(prof: ModelProfile, Npoints):
    """Generate points for a given model profile."""

    # print(f"Generating points for model profile: {prof.subunits}")
    # print(f"Number of subunits: {len(prof.subunits)}")
    # for i, subunit in enumerate(prof.subunits):
    #     print(f"  Subunit {i}: {subunit} with dimensions {prof.dimensions[i]} at COM {prof.com[i]}")
    #     print(f"  Rotation: {prof.rotation[i]} at rotation point {prof.rotation_points[i]} with SLD {prof.p_s[i]}")

    x_new, y_new, z_new, p_new, volume_total = GenerateAllPoints(Npoints, prof.com, prof.subunits,
                                                  prof.dimensions, prof.rotation, prof.rotation_points,
                                                  prof.p_s, prof.exclude_overlap).onGeneratingAllPointsSeparately()

    return ModelPointDistribution(x=x_new, y=y_new, z=z_new, p=p_new, volume_total=volume_total)

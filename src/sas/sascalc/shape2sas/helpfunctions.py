from typing import Any

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
                       rotation: list[float],
                       rotation_point: list[float],
                       com: list[float],
                       subunitClass: object,
                       dimensions: list[float]):
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
                 r_list: list[np.ndarray],
                 pr_list: list[np.ndarray],
                 I_list: list[np.ndarray],
                 Isim_list: list[np.ndarray],
                 sigma_list: list[np.ndarray],
                 S_list: list[np.ndarray],
                 names: list[str],
                 scales: list[float],
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


def generate_pdb(x_list: list[np.ndarray],
                 y_list: list[np.ndarray],
                 z_list: list[np.ndarray],
                 p_list: list[np.ndarray],
                 Model_list: list[str]) -> None:
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


def check_unique(A_list: list[float]) -> bool:
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

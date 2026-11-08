import matplotlib.pyplot as plt
import numpy as np


################################ Shape2SAS helper functions ###################################
class Qsampling:
    @staticmethod
    def onQsampling(qmin: float, qmax: float, Nq: int) -> np.ndarray:
        """Returns uniform q sampling"""
        return np.linspace(qmin, qmax, Nq)

    @staticmethod
    def onUserSampledQ(q: np.ndarray) -> np.ndarray:
        """Returns user sampled q"""
        if isinstance(q, list):
            q = np.array(q)
        return q

    @staticmethod
    def qMethodsNames(name: str):
        methods = {
            "Uniform": Qsampling.onQsampling,
            "User_sampled": Qsampling.onUserSampledQ
        }
        return methods[name]

    @staticmethod
    def qMethodsInput(name: str):
        inputs = {
            "Uniform": {"qmin": 0.001, "qmax": 0.5, "Nq": 400},
            "User_sampled": {"q": Qsampling.onQsampling(0.001, 0.5, 400)} #if the user does not input q
        }
        return inputs[name]


def euler_rotation_matrix(alpha: float, beta: float, gamma: float) -> np.ndarray:
    """
    Convert Euler angles to a rotation matrix, following the intrinsic ZYX convention.
    """
    cosa, cosb, cosg = np.cos(alpha), np.cos(beta), np.cos(gamma)
    sina, sinb, sing = np.sin(alpha), np.sin(beta), np.sin(gamma)
    sinasinb, cosasinb = sina*sinb, cosa*sinb
    return np.array([
        [cosb*cosg, sinasinb*cosg - cosa*sing, cosasinb*cosg + sina*sing],
        [cosb*sing, sinasinb*sing + cosa*cosg, cosasinb*sing - sina*cosg],
        [-sinb, sina*cosb, cosa*cosb]
    ])


def sinc(x) -> np.ndarray:
    """
    function for calculating sinc = sin(x)/x
    numpy.sinc is defined as sinc(x) = sin(pi*x)/(pi*x)
    """
    return np.sinc(x / np.pi)


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

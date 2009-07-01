#if !defined(prolate_h)
#define prolate_h
/** Structure definition for prolate parameters
 * [PYTHONCLASS] = ProlateModel
 * [DISP_PARAMS] = major_core, minor_core, major_shell,minor_shell, axis_theta, axis_phi
   [DESCRIPTION] = <text> Calculates the form factor for a monodisperse prolate ellipsoid particle with a
						core/shell structure
						Note:It is the users' responsibility to ensure that shell radii are larger than core radii, and
					that major radii are larger than minor radii.</text>

   [FIXED] = <text>axis_phi.width; axis_theta.width; major_core.width;minor_core.width; major_shell; minor_shell</text>
   [ORIENTATION_PARAMS] = <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>

 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Major core of prolate [A]
    //  [DEFAULT]=major_core=100.0 [A]
    double major_core;
	/// Minor core of prolate [A]
    //  [DEFAULT]=minor_core=50.0 [A]
    double minor_core;
	/// Major shell of prolate [A]
    //  [DEFAULT]=major_shell=110.0 [A]
    double major_shell;
	/// Minor shell of prolate [A]
    //  [DEFAULT]=minor_shell=60.0 [A]
    double minor_shell;
    ///  Scattering contrast [1/A²]
    //  [DEFAULT]=contrast=1.0e-6 [1/A²]
    double contrast;
	/// Solvent scattering length density  [1/A²]
    //  [DEFAULT]=sld_solvent=6.3e-6 [1/A²]
    double sld_solvent;
	/// Incoherent Background [1/cm] 0.001
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
    /// Orientation of the prolate axis w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.0 [rad]
    double axis_theta;
    /// Orientation of the prolate in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=1.0 [rad]
    double axis_phi;

} ProlateParameters;



/// 1D scattering function
double prolate_analytical_1D(ProlateParameters *pars, double q);

/// 2D scattering function
double prolate_analytical_2D(ProlateParameters *pars, double q, double phi);
double prolate_analytical_2DXY(ProlateParameters *pars, double qx, double qy);
double prolate_analytical_2D_scaled(ProlateParameters *pars, double q, double q_x, double q_y);

#endif

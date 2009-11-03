#if !defined(spheroid_h)
#define spheroid_h
/** Structure definition for oblate parameters
 * [PYTHONCLASS] = CoreShellEllipsoidModel
 * [DISP_PARAMS] = equat_core, polar_core, equat_shell,polar_shell,axis_phi, axis_theta
   [DESCRIPTION] = <text>[SpheroidCoreShellModel] Calculates the form factor for an spheroid
			ellipsoid particle with a core_shell structure.
			The form factor is averaged over all possible
			orientations of the ellipsoid such that P(q)
			= scale*<f^2>/Vol + bkg, where f is the
			single particle scattering amplitude.
			[Parameters]:
			equat_core = equatorial radius of core,
			polar_core = polar radius of core,
			equat_shell = equatorial radius of shell,
			polar_shell = polar radius (revolution axis) of shell,
			contrast = SLD_core - SLD_shell
			sld_solvent = SLD_solvent
			background = Incoherent bkg
			scale =scale
			Note:It is the users' responsibility to ensure
			that shell radii are larger than core radii.
			oblate: polar radius < equatorial radius
			prolate :  polar radius > equatorial radius
			</text>

   [FIXED] = <text>equat_core.width;polar_core.width; equat_shell.width; polar_shell.width; axis_phi.width; axis_theta.width</text>
   [ORIENTATION_PARAMS]= <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>

 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Equatorial radius of core [A]
    //  [DEFAULT]=equat_core=200.0 [A]
    double equat_core;
	/// Polar radius of core [A]
    //  [DEFAULT]=polar_core=20.0 [A]
    double polar_core;
	/// equatorial radius of shell [A]
    //  [DEFAULT]=equat_shell=250.0 [A]
    double equat_shell;
	/// polar radius of shell [A]
    //  [DEFAULT]=polar_shell=30.0 [A]
    double polar_shell;
    ///  Scattering contrast [1/A^(2)]
    //  [DEFAULT]=contrast=1.0e-6 [1/A^(2)]
    double contrast;
	/// Solvent scattering length density  [1/A^(2)]
    //  [DEFAULT]=sld_solvent=6.3e-6 [1/A^(2)]
    double sld_solvent;
	/// Incoherent Background [1/cm] 0.001
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
	//Disable for now
    /// Orientation of the oblate axis w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=0.0 [rad]
    double axis_theta;
    /// Orientation of the oblate in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 [rad]
    double axis_phi;

} SpheroidParameters;



/// 1D scattering function
double spheroid_analytical_1D(SpheroidParameters *pars, double q);

/// 2D scattering function
double spheroid_analytical_2D(SpheroidParameters *pars, double q, double phi);
double spheroid_analytical_2DXY(SpheroidParameters *pars, double qx, double qy);
double spheroid_analytical_2D_scaled(SpheroidParameters *pars, double q, double q_x, double q_y);

#endif

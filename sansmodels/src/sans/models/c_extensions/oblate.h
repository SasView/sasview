#if !defined(oblate_h)
#define oblate_h
/** Structure definition for oblate parameters
 * [PYTHONCLASS] = OblateModel
 * [DISP_PARAMS] = major_core, minor_core, major_shell,minor_shell
   [DESCRIPTION] = <text>[OblateCoreShellModel] Calculates the form factor for an oblate
			ellipsoid particle with a core_shell structure.
			The form factor is averaged over all possible
			orientations of the ellipsoid such that P(q)
			= scale*<f^2>/Vol + bkg, where f is the
			single particle scattering amplitude.
			[Parameters]:
			major_core = radius of major_core,
			minor_core = radius of minor_core,
			major_shell = radius of major_shell,
			minor_shell = radius of minor_shell,
			contrast = SLD_core - SLD_shell
			sld_solvent = SLD_solvent
			background = Incoherent bkg
			scale =scale
			Note:It is the users' responsibility to ensure
			that shell radii are larger than core radii.
			</text>

   [FIXED] = <text>major_core.width;minor_core.width; major_shell.width; minor_shell.width</text>
   [ORIENTATION_PARAMS]= <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>

 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Major core of oblate [A]
    //  [DEFAULT]=major_core=200.0 [A]
    double major_core;
	/// Minor core of oblate [A]
    //  [DEFAULT]=minor_core=20.0 [A]
    double minor_core;
	/// Major shell of oblate [A]
    //  [DEFAULT]=major_shell=250.0 [A]
    double major_shell;
	/// Minor shell of oblate [A]
    //  [DEFAULT]=minor_shell=30.0 [A]
    double minor_shell;
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
    /// Orientation of the oblate axis w/respect incoming beam [deg]
    //  [DEFAULT]=axis_theta=57.325 [deg]
    double axis_theta;
    /// Orientation of the oblate in the plane of the detector [deg]
    //  [DEFAULT]=axis_phi=57.325 [deg]
    double axis_phi;

} OblateParameters;



/// 1D scattering function
double oblate_analytical_1D(OblateParameters *pars, double q);

/// 2D scattering function
double oblate_analytical_2D(OblateParameters *pars, double q, double phi);
double oblate_analytical_2DXY(OblateParameters *pars, double qx, double qy);
//double oblate_analytical_2D_scaled(OblateParameters *pars, double q, double q_x, double q_y);

#endif

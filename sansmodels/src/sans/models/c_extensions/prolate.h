#if !defined(prolate_h)
#define prolate_h
/** Structure definition for prolate parameters
 * [PYTHONCLASS] = ProlateModel
 * [DISP_PARAMS] = major_core, minor_core, major_shell,minor_shell
   [DESCRIPTION] = <text>[ProlateCoreShellModel] Calculates the form factor for a prolate
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
			scale = scale
			Note:It is the users' responsibility to ensure
			that shell radii are larger than core radii.
			</text>
   [FIXED] = <text>major_core.width;minor_core.width; major_shell.width; minor_shell.width</text>
   [ORIENTATION_PARAMS] =

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

} ProlateParameters;



/// 1D scattering function
double prolate_analytical_1D(ProlateParameters *pars, double q);

/// 2D scattering function
double prolate_analytical_2D(ProlateParameters *pars, double q, double phi);
double prolate_analytical_2DXY(ProlateParameters *pars, double qx, double qy);
//double prolate_analytical_2D_scaled(ProlateParameters *pars, double q, double q_x, double q_y);

#endif

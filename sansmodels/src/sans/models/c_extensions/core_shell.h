#if !defined(core_shell_h)
#define core_shell_h

/**
 * Structure definition for core-shell parameters
 */
 //[PYTHONCLASS] = CoreShellModel
 //[DISP_PARAMS] = radius, thickness
 //[DESCRIPTION] =<text>Form factor for a monodisperse spherical particle with particle
 //    with a core-shell structure:
 //
 //    The form factor is normalized by the
 //    total particle volume.
 //
 //		radius: core radius, thickness: shell thickness
 //
 //     Ref: Guinier, A. and G. Fournet,
 //     John Wiley and Sons, New York, 1955.
 //				</text>
 //[FIXED]= <text> thickness.width;radius.width</text>


typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    ///	Core Radius [A] 60.0
    //  [DEFAULT]=radius=60.0 [A]
    double radius;
    /// Shell Thickness [A] 10.0
    //  [DEFAULT]=thickness=10 [A]
    double thickness;
    ///	Core SLD [1/A²] 1.0e-6
    //  [DEFAULT]=core_sld=1.0e-6 [1/A²]
    double core_sld;
	/// Shell SLD [1/A²] 2.0e-6
	//  [DEFAULT]=shell_sld=2.0e-6 [1/A²]
	double shell_sld;
	/// Solvent SLD [1/A²] 3.0e-6
	//  [DEFAULT]=solvent_sld=3.0e-6 [1/A²]
	double solvent_sld;
	/// Incoherent Background [1/cm] 0.000
	//  [DEFAULT]=background=0 [1/cm]
	double background;
} CoreShellParameters;



/// 1D scattering function
double core_shell_analytical_1D(CoreShellParameters *pars, double q);

/// 2D scattering function
double core_shell_analytical_2D(CoreShellParameters *pars, double q, double phi);
double core_shell_analytical_2DXY(CoreShellParameters *pars, double qx, double qy);

#endif

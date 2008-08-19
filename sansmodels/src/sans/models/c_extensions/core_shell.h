#if !defined(core_shell_h)
#define core_shell_h

/**
 * Structure definition for core-shell parameters
 */
 //[PYTHONCLASS] = CoreShellModel
 //[DISP_PARAMS] = radius, thickness
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    ///	Core Radius (A) 60.0
    //  [DEFAULT]=radius=60.0 A
    double radius;
    /// Shell Thickness (A) 10.0
    //  [DEFAULT]=thickness=10 A
    double thickness;
    ///	Core SLD (Å-2) 1.0e-6
    //  [DEFAULT]=core_sld=1.0e-6 A-2
    double core_sld;
	/// Shell SLD (Å-2) 2.0e-6
	//  [DEFAULT]=shell_sld=2.0e-6 A-2
	double shell_sld;
	/// Solvent SLD (Å-2) 3.0e-6
	//  [DEFAULT]=solvent_sld=3.0e-6 A-2
	double solvent_sld;
	/// Incoherent Background (cm-1) 0.000
	//  [DEFAULT]=background=0 cm-1
	double background;
} CoreShellParameters;



/// 1D scattering function
double core_shell_analytical_1D(CoreShellParameters *pars, double q);

/// 2D scattering function
double core_shell_analytical_2D(CoreShellParameters *pars, double q, double phi);
double core_shell_analytical_2DXY(CoreShellParameters *pars, double qx, double qy);

#endif

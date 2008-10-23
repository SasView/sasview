#if !defined(core_shell_cylinder_h)
#define core_shell_cylinder_h

/**
 * Structure definition for core-shell cylinder parameters
 */
 //[PYTHONCLASS] = CoreShellCylinderModel
 //[DISP_PARAMS] = radius, thickness, length, axis_theta, axis_phi
 //[DESCRIPTION] = ''
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;

    /// Core radius [A]
    //  [DEFAULT]=radius=20.0 A
    double radius;

    /// Shell thickness [A]
    //  [DEFAULT]=thickness=10.0 A
    double thickness;

    /// Core length [A]
    //  [DEFAULT]=length=400.0 A
    double length;

    /// Core SLD [A-2]
    //  [DEFAULT]=core_sld=1.0e-6 A-2
    double core_sld;

    /// Shell SLD [A-2]
    //  [DEFAULT]=shell_sld=4.0e-6 A-2
    double shell_sld;

    /// Solvent SLD [A-2]
    //  [DEFAULT]=solvent_sld=1.0e-6 A-2
    double solvent_sld;

	/// Incoherent Background [cm-1]
	//  [DEFAULT]=background=0 cm-1
	double background;

    /// Orientation of the long axis of the core-shell cylinder w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.57 rad
    double axis_theta;

    /// Orientation of the long axis of the core-shell cylinder in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 rad
    double axis_phi;

} CoreShellCylinderParameters;



/// 1D scattering function
double core_shell_cylinder_analytical_1D(CoreShellCylinderParameters *pars, double q);

/// 2D scattering function
double core_shell_cylinder_analytical_2D(CoreShellCylinderParameters *pars, double q, double phi);
double core_shell_cylinder_analytical_2DXY(CoreShellCylinderParameters *pars, double qx, double qy);
double core_shell_cylinder_analytical_2D_scaled(CoreShellCylinderParameters *pars, double q, double q_x, double q_y);

#endif

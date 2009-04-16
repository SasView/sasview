#if !defined(core_shell_cylinder_h)
#define core_shell_cylinder_h

/**
 * Structure definition for core-shell cylinder parameters
 */
 //[PYTHONCLASS] = CoreShellCylinderModel
 //[DISP_PARAMS] = radius, thickness, length, axis_theta, axis_phi
 //[DESCRIPTION] = <text>P(q,alpha)= scale/Vs*f(q)^(2) + bkg,  where: f(q)= 2(core_sld
//			- solvant_sld)* Vc*sin[qLcos(alpha/2)]
//			/[qLcos(alpha/2)]*J1(qRsin(alpha))
 //			/[qRsin(alpha)]+2(shell_sld-solvent_sld)
 //			*Vs*sin[q(L+T)cos(alpha/2)][[q(L+T)
 //			*cos(alpha/2)]*J1(q(R+T)sin(alpha))
 //			/q(R+T)sin(alpha)]
 //
 //			alpha:is the angle between the axis of
 //          the cylinder and the q-vector
 //			Vs: the volume of the outer shell
 //			Vc: the volume of the core
 //			L: the length of the core
 //    		shell_sld: the scattering length density
 //			of the shell
 //			solvent_sld: the scattering length density
 //			of the solvent
 //			bkg: the background
 //			T: the thickness
 //    		R+T: is the outer radius
 // 		L+2T: The total length of the outershell
 //			J1: the first order Bessel function
 // 		theta: axis_theta of the cylinder
 // 		phi: the axis_phi of the cylinder...
 //		</text>
 //[FIXED]= <text> axis_phi.width; axis_theta.width; length.width;radius.width; thickness_width</text>
 //[ORIENTATION_PARAMS]= axis_phi; axis_theta;axis_phi.width; axis_theta.width


typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;

    /// Core radius [A]
    //  [DEFAULT]=radius=20.0 [A]
    double radius;

    /// Shell thickness [A]
    //  [DEFAULT]=thickness=10.0 [A]
    double thickness;

    /// Core length [A]
    //  [DEFAULT]=length=400.0 [A]
    double length;

    /// Core SLD [1/A²]
    //  [DEFAULT]=core_sld=1.0e-6 [1/A²]
    double core_sld;

    /// Shell SLD [1/A²]
    //  [DEFAULT]=shell_sld=4.0e-6 [1/A²]
    double shell_sld;

    /// Solvent SLD [1/A²]
    //  [DEFAULT]=solvent_sld=1.0e-6 [1/A²]
    double solvent_sld;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;

    /// Orientation of the long axis of the core-shell cylinder w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.57 [rad]
    double axis_theta;

    /// Orientation of the long axis of the core-shell cylinder in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 [rad]
    double axis_phi;

} CoreShellCylinderParameters;



/// 1D scattering function
double core_shell_cylinder_analytical_1D(CoreShellCylinderParameters *pars, double q);

/// 2D scattering function
double core_shell_cylinder_analytical_2D(CoreShellCylinderParameters *pars, double q, double phi);
double core_shell_cylinder_analytical_2DXY(CoreShellCylinderParameters *pars, double qx, double qy);
double core_shell_cylinder_analytical_2D_scaled(CoreShellCylinderParameters *pars, double q, double q_x, double q_y);

#endif

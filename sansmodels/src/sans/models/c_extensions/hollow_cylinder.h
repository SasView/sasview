#if !defined(hollow_cylinder_h)
#define hollow_cylinder_h

/**
 * Structure definition for hollow cylinder parameters
 */
 //[PYTHONCLASS] = HollowCylinderModel
 //[DISP_PARAMS] = core_radius, radius, length, axis_theta, axis_phi
 //[DESCRIPTION] = <text> P(q) = scale*<f*f>/Vol + bkg, where f is the scattering amplitude.
 //					core_radius = the radius of core
 //				radius = the radius of shell
 // 			length = the total length of the cylinder
 //				contrast = SLD of solvent - SLD of shell
 //				background = incoherent background
 //	</text>
 //[FIXED]= <text> axis_phi.width; axis_theta.width; length.width;core_radius.width; radius</text>
 //[ORIENTATION_PARAMS]= axis_phi; axis_theta;axis_phi.width; axis_theta.width


typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;

    /// Core radius [A]
    //  [DEFAULT]=core_radius=20.0 [A]
    double core_radius;

    /// Shell radius [A]
    //  [DEFAULT]=radius=30.0 [A]
    double radius;

    /// Hollow cylinder length [A]
    //  [DEFAULT]=length=400.0 [A]
    double length;

    /// Contrast  [1/A^(2)]
    //  [DEFAULT]=contrast=5.3e-6 [1/A^(2)]
    double contrast;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.01 [1/cm]
	double background;

    /// Orientation of the long axis of the hollow cylinder w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.57 [rad]
    double axis_theta;

    /// Orientation of the long axis of the hollow cylinder in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 [rad]
    double axis_phi;

} HollowCylinderParameters;



/// 1D scattering function
double hollow_cylinder_analytical_1D(HollowCylinderParameters *pars, double q);

/// 2D scattering function
double hollow_cylinder_analytical_2D(HollowCylinderParameters *pars, double q, double phi);
double hollow_cylinder_analytical_2DXY(HollowCylinderParameters *pars, double qx, double qy);
double hollow_cylinder_analytical_2D_scaled(HollowCylinderParameters *pars, double q, double q_x, double q_y);

#endif

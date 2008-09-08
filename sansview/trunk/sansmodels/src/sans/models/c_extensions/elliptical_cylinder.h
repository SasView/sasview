#if !defined(ell_cylinder_h)
#define ell_cylinder_h

/** Structure definition for cylinder parameters
 * [PYTHONCLASS] = EllipticalCylinderModel
 * [DISP_PARAMS] = r_minor, r_ratio, length, cyl_theta, cyl_phi, cyl_psi
 *
 * */
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Minor radius [A]
    //  [DEFAULT]=r_minor=20.0 A
    double r_minor;
    /// Ratio of major/minor radii
    //  [DEFAULT]=r_ratio=1.5 A
    double r_ratio;
    /// Length of the cylinder [A]
    //  [DEFAULT]=length=400.0 A
    double length;
    /// Contrast [A-2]
    //  [DEFAULT]=contrast=3.0e-6 A-2
    double contrast;
	/// Incoherent Background (cm-1) 0.000
	//  [DEFAULT]=background=0 cm-1
	double background;
    /// Orientation of the cylinder axis w/respect incoming beam [rad]
    //  [DEFAULT]=cyl_theta=1.57 rad
    double cyl_theta;
    /// Orientation of the cylinder in the plane of the detector [rad]
    //  [DEFAULT]=cyl_phi=0.0 rad
    double cyl_phi;
    /// Orientation of major radius of the cross-section w/respect vector q [rad]
    //  [DEFAULT]=cyl_psi=0.0 rad
    double cyl_psi;
} EllipticalCylinderParameters;



/// 1D scattering function
double elliptical_cylinder_analytical_1D(EllipticalCylinderParameters *pars, double q);

/// 2D scattering function
double elliptical_cylinder_analytical_2D(EllipticalCylinderParameters *pars, double q, double phi);
double elliptical_cylinder_analytical_2DXY(EllipticalCylinderParameters *pars, double qx, double qy);
double elliptical_cylinder_analytical_2D_scaled(EllipticalCylinderParameters *pars, double q, double q_x, double q_y);

#endif

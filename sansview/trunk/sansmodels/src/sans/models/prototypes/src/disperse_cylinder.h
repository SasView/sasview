#if !defined(disperse_cylinder_h)
#define disperse_cylinder_h

/** Structure definition for dispersed cylinder parameters 
 * [PYTHONCLASS] = DispCylinderModel
 * [BASESTRUCT]  = CylinderParameters 
 * [BASE_H]      = cylinder
 * */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Radius of the cylinder [A]
    //  [DEFAULT]=radius=20.0 A
    double radius;
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
    
    ///
    //  [DEFAULT]=cyl_phi=0.0 rad
    double cyl_phi;    
    
    ///
    //  [DEFAULT]=sigma_theta=0.0 rad
    double sigma_theta;
    
    ///
    //  [DEFAULT]=sigma_phi=0.0 rad
    double sigma_phi;
    
    ///
    //  [DEFAULT]=sigma_radius=0.0 rad
    double sigma_radius;
    
    ///
    //  [DEFAULT]=sigma_radius=0.0 rad
    double sigma_length;
    
    ///
    //  [DEFAULT]=n_pts=25
    double n_pts;
    
    
} DispCylinderParameters;



/// 1D scattering function
double disperse_cylinder_analytical_1D(DispCylinderParameters *pars, double q);

/// 2D scattering function
double disperse_cylinder_analytical_2D(DispCylinderParameters *pars, double q, double phi);
double disperse_cylinder_dist( double x, double mean, double sigma );

#endif

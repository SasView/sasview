#if !defined(ellipsoid_h)
#define ellipsoid_h

/** 
 * Structure definition for ellipsoid parameters 
 * The ellipsoid has axes radius_b, radius_b, radius_a.
 * Ref: Jan Skov Pedersen, Advances in Colloid and Interface Science, 70 (1997) 171-210
 */
 //[PYTHONCLASS] = EllipsoidModel
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    
    ///	Rotation axis radius_a [A] 
    //  [DEFAULT]=radius_a=20.0 A
    double radius_a;
    
    /// Radius_b [A] 
    //  [DEFAULT]=radius_b=400 A
    double radius_b;
    
    ///	Contrast [Å-2] 
    //  [DEFAULT]=contrast=3.0e-6 A-2
    double contrast;
    
	/// Incoherent Background [cm-1]
	//  [DEFAULT]=background=0 cm-1
	double background;    
	
    /// Orientation of the long axis of the ellipsoid w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.57 rad
    double axis_theta;
    /// Orientation of the long axis of the ellipsoid in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 rad
    double axis_phi;    
} EllipsoidParameters;



/// 1D scattering function
double ellipsoid_analytical_1D(EllipsoidParameters *pars, double q);

/// 2D scattering function
double ellipsoid_analytical_2D(EllipsoidParameters *pars, double q, double phi);
double ellipsoid_analytical_2DXY(EllipsoidParameters *pars, double qx, double qy);
double ellipsoid_analytical_2D_scaled(EllipsoidParameters *pars, double q, double q_x, double q_y);

#endif

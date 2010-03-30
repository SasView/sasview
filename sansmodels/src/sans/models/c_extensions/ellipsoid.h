#if !defined(ellipsoid_h)
#define ellipsoid_h

/**
 * Structure definition for ellipsoid parameters
 * The ellipsoid has axes radius_b, radius_b, radius_a.
 * Ref: Jan Skov Pedersen, Advances in Colloid and Interface Science, 70 (1997) 171-210
 */
 //[PYTHONCLASS] = EllipsoidModel
 //[DISP_PARAMS] = radius_a, radius_b, axis_theta, axis_phi
 //[DESCRIPTION] = <text>"P(q.alpha)= scale*f(q)^(2)+ bkg, where f(q)= 3*(sld_ell
 //		- sld_solvent)*V*[sin(q*r(Ra,Rb,alpha))
 //		-q*r*cos(qr(Ra,Rb,alpha))]
 //		/[qr(Ra,Rb,alpha)]^(3)"
 //
 //     r(Ra,Rb,alpha)= [Rb^(2)*(sin(alpha))^(2)
 //     + Ra^(2)*(cos(alpha))^(2)]^(1/2)
 //
 //		scatter_sld: SLD of the scatter
 //		solvent_sld: SLD of the solvent
 //     sldEll: SLD of ellipsoid
 //		sldSolv: SLD of solvent
 //		V: volune of the Eliipsoid
 //		Ra: radius along the rotation axis
 //		of the Ellipsoid
 //		Rb: radius perpendicular to the
 //		rotation axis of the ellipsoid
 //		</text>
 //[FIXED]= <text> axis_phi.width; axis_theta.width;radius_a.width;
 //radius_b.width; length.width; r_minor.width;
 //r_ratio.width</text>
 //[ORIENTATION_PARAMS]=  axis_phi.width; axis_theta.width;axis_phi; axis_theta


typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;

    ///	Rotation axis radius_a [A]
    //  [DEFAULT]=radius_a=20.0 [A]
    double radius_a;

    /// Radius_b [A]
    //  [DEFAULT]=radius_b=400 [A]
    double radius_b;

    ///	sldEll [1/A^(2)]
    //  [DEFAULT]=sldEll=4.0e-6 [1/A^(2)]
    double sldEll;

    ///	sld of solvent [1/A^(2)]
    //  [DEFAULT]=sldSolv=1.0e-6 [1/A^(2)]
    double sldSolv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;

    /// Orientation of the long axis of the ellipsoid w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.57 [rad]
    double axis_theta;
    /// Orientation of the long axis of the ellipsoid in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=0.0 [rad]
    double axis_phi;
} EllipsoidParameters;



/// 1D scattering function
double ellipsoid_analytical_1D(EllipsoidParameters *pars, double q);

/// 2D scattering function
double ellipsoid_analytical_2D(EllipsoidParameters *pars, double q, double phi);
double ellipsoid_analytical_2DXY(EllipsoidParameters *pars, double qx, double qy);
double ellipsoid_analytical_2D_scaled(EllipsoidParameters *pars, double q, double q_x, double q_y);

#endif

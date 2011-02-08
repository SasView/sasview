#if !defined(DiamEllip_h)
#define DiamEllip_h

/**
 * To calculate the 2nd virial coefficient
* [PYTHONCLASS] = DiamEllipFunc
* [DISP_PARAMS] = radius_a, radius_b
  [DESCRIPTION] =<text>To calculate the 2nd virial coefficient for
                            the non-spherical object, then find the
                            radius of sphere that has this value of
                            virial coefficient:
                              radius_a = polar radius,
                              radius_b = equatorial radius;
                                 radius_a > radius_b: Prolate spheroid,
                                 radius_a < radius_b: Oblate spheroid.
 				</text>
	[FIXED]= <text>
				radius_a.width;radius_b.width
			</text>

 **/
typedef struct {
    ///	Polar radius [A]
    //  [DEFAULT]=radius_a=20.0 A
    double radius_a;

    /// Equatorial radius [A]
    //  [DEFAULT]=radius_b= 400 A
    double radius_b;

} DiamEllipsParameters;



/// 1D scattering function
//double DiamEllips_analytical_1D(DiamEllipsParameters *pars, double q);

/// 2D scattering function
//double DiamEllips_analytical_2D(DiamEllipsParameters *pars, double q, double phi);
//double DiamEllips_analytical_2DXY(DiamEllipsParameters *pars, double qx, double qy);

#endif

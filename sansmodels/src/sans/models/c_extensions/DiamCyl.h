#if !defined(DiamCyl_h)
#define DiamCyl_h

/**
* To calculate the 2nd virial coefficient
* [PYTHONCLASS] = DiamCylFunc
* [DISP_PARAMS] = radius, length
  [DESCRIPTION] =<text>To calculate the 2nd virial coefficient for
  the non-spherical object, then find the
  radius of sphere that has this value of
  virial coefficient.
 				</text>
	[FIXED]= <text>
				radius.width; length.width
			</text>
**/

typedef struct {
    ///	Radius [A]
    //  [DEFAULT]=radius=20.0 A
    double radius;

    /// Length [A]
    //  [DEFAULT]=length= 400 A
    double length;

} DiamCyldParameters;



/// 1D scattering function
//double DiamCyld_analytical_1D(DiamCyldParameters *pars, double q);

/// 2D scattering function
//double DiamCyld_analytical_2D(DiamCyldParameters *pars, double q, double phi);
//double DiamCyld_analytical_2DXY(DiamCyldParameters *pars, double qx, double qy);

#endif

#if !defined(SquareWell_h)
#define SquareWell_h

/**Structure definition for SquareWell parameters
*/
//   [PYTHONCLASS] = SquareWellStructure
//   [DISP_PARAMS] = radius
//   [DESCRIPTION] = <text> Structure Factor for interacting particles:
//
//  The interaction potential is
//
//		U(r)= inf   , r < 2R
//			= -d    , 2R <= r <=2Rw
//			= 0     , r >= 2Rw
//
//		R: radius (A)of the particle, v: volume fraction
//		d: well depth
//		w: well width; multiples of the particle diameter
//
//		Ref: Sharma, R. V.; Sharma, K. C., Physica,
//            1977, 89A, 213.
//   			</text>
//   [FIXED]= radius.width
//[ORIENTATION_PARAMS]= <text> </text>


typedef struct {
    ///	Radius of particle [Å]
    //  [DEFAULT]=radius=50.0 [Å]
    double radius;

    /// Volume fraction
    //  [DEFAULT]=volfraction= 0.040
    double volfraction;

    ///	Well depth [kT]
    //  [DEFAULT]=welldepth= 1.50 [kT]
    double welldepth;

    ///	Well width
    //  [DEFAULT]=wellwidth= 1.20
    double wellwidth;

} SquareWellParameters;



/// 1D scattering function
double SquareWell_analytical_1D(SquareWellParameters *pars, double q);

/// 2D scattering function
double SquareWell_analytical_2D(SquareWellParameters *pars, double q, double phi);
double SquareWell_analytical_2DXY(SquareWellParameters *pars, double qx, double qy);

#endif

#if !defined(StickyHS_h)
#define StickyHS_h

/**
 * Structure definition for StickyHS_struct (struncture factor) parameters
 */
 //[PYTHONCLASS] = StickyHSStructure
 //[DISP_PARAMS] = radius
 //[DESCRIPTION] =<text> Structure Factor for interacting particles:                               .
 //
 //  The interaction potential is
 //
 //                     U(r)= inf , r < 2R
 //                         = -Uo  , 2R < r < 2R + w
 //                         = 0   , r >= 2R +w
 //
 //						R: radius of the hardsphere
 //                     stickiness = [exp(Uo/kT)]/(12*perturb)
 //                     perturb = w/(w+ 2R) , 0.01 =< w <= 0.1
 //                     w: The width of the square well ,w > 0
 //						v: The volume fraction , v > 0
 //
 //                     Ref: Menon, S. V. G.,et.al., J. Chem.
 //                      Phys., 1991, 95(12), 9186-9190.
 //				</text>
 //[FIXED]= radius.width
typedef struct {
    /// Radius of hardsphere [A]
    //  [DEFAULT]=radius=50.0 [A]
    double radius;

    ///	Volume fraction
    //  [DEFAULT]=volfraction= 0.1
    double volfraction;

	/// Perturbation Parameter ( between 0.01 - 0.1)
    //  [DEFAULT]=perturb=0.05
    double perturb;

    ///	Stickiness
    //  [DEFAULT]=stickiness= 0.2
    double stickiness;
} StickyHSParameters;



/// 1D scattering function
double StickyHS_analytical_1D(StickyHSParameters *pars, double q);

/// 2D scattering function
double StickyHS_analytical_2D(StickyHSParameters *pars, double q, double phi);
double StickyHS_analytical_2DXY(StickyHSParameters *pars, double qx, double qy);

#endif

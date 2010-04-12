#if !defined(polygausscoil_h)
#define polygausscoil_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = Poly_GaussCoil
 //[DISP_PARAMS] = rg
 //[DESCRIPTION] =<text>I(q)=(scale)*2*[(1+U*x)^(-1/U)+x-1]/[(1+U)*x^2]
 //						+ background
 //				where x = [rg^2*q^2] and the polydispersity is
 //					U = [M_w/M_n]-1.
 //				scale = scale factor * volume fraction
 //				rg: radius of gyration
 //				poly_m = polydispersity of molecular weight
 //				background:incoherent background
 //		</text>
 //[FIXED]=
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Radius of gyration [A]
    //  [DEFAULT]=rg=60.0 [A]
    double rg;

    ///	polydispersity of molecular weight
    //  [DEFAULT]=poly_m= 2.0 [Mw/Mn]
    double poly_m;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
} PolyGaussCoilParameters;



/// 1D scattering function
double polygausscoil_analytical_1D(PolyGaussCoilParameters *pars, double q);

/// 2D scattering function
double polygausscoil_analytical_2D(PolyGaussCoilParameters *pars, double q, double phi);
double polygausscoil_analytical_2DXY(PolyGaussCoilParameters *pars, double qx, double qy);

#endif

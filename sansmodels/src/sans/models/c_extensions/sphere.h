#if !defined(sphere_h)
#define sphere_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = SphereModel
 //[DISP_PARAMS] = radius
 //[DESCRIPTION] =<text>P(q)=(scale/V)
 //						*[3V(scatter_sld-solvent_sld)*(sin(qR)-qRcos(qR))/(qR)^3]^(2)
 //						+bkg
 //						bkg: background level
 //						R: radius of the sphere
 //						V:The volume of the scatter
 //						scatter_sld: the scattering length density of the scatter
 //						solvent_sld: the scattering length density of the solvent
 //				</text>
 //[FIXED]=  radius.width
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Radius of sphere [Å]
    //  [DEFAULT]=radius=60.0 [Å]
    double radius;

    ///	Contrast [1/Å²]
    //  [DEFAULT]=contrast= 1.0e-6 [1/Å²]
    double contrast;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;
} SphereParameters;



/// 1D scattering function
double sphere_analytical_1D(SphereParameters *pars, double q);

/// 2D scattering function
double sphere_analytical_2D(SphereParameters *pars, double q, double phi);
double sphere_analytical_2DXY(SphereParameters *pars, double qx, double qy);

#endif

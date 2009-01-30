#if !defined(sphere_h)
#define sphere_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = SphereModel
 //[DISP_PARAMS] = radius
 //[DESCRIPTION] =<text>P(q)=(scale/V)*[3V(scatter_sld-solvent_sld)*(sin(qR)-qRcos(qR))/(qR)^3]^(2)
 //						+bkg
 //						bkg: background level
 //						R: radius of the sphere
 //						V:The volume of the scatter
 //						scatter_sld: the scattering length density of the scatter
 //						solvent_sld: the scattering length density of the solvent
 //				</text>
 //[FIXED]=  radius.width
 
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Radius of sphere [A]
    //  [DEFAULT]=radius=60.0 A
    double radius;

    ///	Contrast [Å-2]
    //  [DEFAULT]=contrast= 1.0e-6 A-2
    double contrast;

	/// Incoherent Background [cm-1]
	//  [DEFAULT]=background=0 cm-1
	double background;
} SphereParameters;



/// 1D scattering function
double sphere_analytical_1D(SphereParameters *pars, double q);

/// 2D scattering function
double sphere_analytical_2D(SphereParameters *pars, double q, double phi);
double sphere_analytical_2DXY(SphereParameters *pars, double qx, double qy);

#endif

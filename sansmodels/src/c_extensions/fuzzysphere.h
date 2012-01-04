#if !defined(fuzzysphere_h)
#define fuzzysphere_h

/**
 * Structure definition for FuzzySphere parameters
 */
 //[PYTHONCLASS] = FuzzySphereModel
 //[DISP_PARAMS] = radius, fuzziness
 //[DESCRIPTION] =<text>
 //				scale: scale factor times volume fraction,
 //					or just volume fraction for absolute scale data
 //				radius: radius of the solid sphere
 //				fuzziness = the STD of the height of fuzzy interfacial
 //				 thickness (ie., so-called interfacial roughness)
 //				sldSph: the SLD of the sphere
 //				sldSolv: the SLD of the solvent
 //				background: incoherent background
 //			Note: By definition, this function works only when fuzziness << radius.
 //		</text>
 //[FIXED]=  radius.width; fuzziness.width
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 0.01
    double scale;

    ///	Radius of sphere [A]
    //  [DEFAULT]=radius=60.0 [A]
    double radius;

    ///	surface roughness [A]
    //  [DEFAULT]=fuzziness= 10.0 [A]
    double fuzziness;

    ///	sldSph [1/A^(2)]
    //  [DEFAULT]=sldSph= 1.0e-6 [1/A^(2)]
    double sldSph;

    ///	sldSolv [1/A^(2)]
    //  [DEFAULT]=sldSolv= 3.0e-6 [1/A^(2)]
    double sldSolv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
} FuzzySphereParameters;

/// kernel
double fuzzysphere_kernel(double dp[], double q);

/// 1D scattering function
double fuzzysphere_analytical_1D(FuzzySphereParameters *pars, double q);

/// 2D scattering function
double fuzzysphere_analytical_2D(FuzzySphereParameters *pars, double q, double phi);
double fuzzysphere_analytical_2DXY(FuzzySphereParameters *pars, double qx, double qy);
double fuzzysphere_analytical_2D_scaled(FuzzySphereParameters *pars, double q, double q_x, double q_y);
#endif

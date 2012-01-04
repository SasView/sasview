#if !defined(flexcyl_ellipX_h)
#define flexcyl_ellipX_h

/** Structure definition for Flexible cylinder w/ EllipX parameters
 * [PYTHONCLASS] = FlexCylEllipXModel
 * [DISP_PARAMS] = length, kuhn_length, radius, axis_ratio
   [DESCRIPTION] = <text> Note : scale and contrast=sldCyl-sldSolv are both multiplicative factors in the
		model and are perfectly correlated. One or
		both of these parameters must be held fixed
		during model fitting.
		</text>
	[FIXED]= <text>length.width; kuhn_length.width; radius.width; axis_ratio.width</text>
	[ORIENTATION_PARAMS]= <text></text>


 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Length of the flexible cylinder [A]
    //  [DEFAULT]=length=1000 [A]
    double length;
	/// Kuhn length of the flexible cylinder [A]
    //  [DEFAULT]=kuhn_length=100 [A]
    double kuhn_length;
	/// Radius of the flexible cylinder [A]
    //  [DEFAULT]=radius=20.0 [A]
    double radius;
    /// axis_ratio (major_radius/radius
    //  [DEFAULT]=axis_ratio=1.5
    double axis_ratio;
    /// SLD of cylinder [1/A^(2)]
    //  [DEFAULT]=sldCyl=1.0e-6 [1/A^(2)]
    double sldCyl;
    /// SLD of solvent [1/A^(2)]
    //  [DEFAULT]=sldSolv=6.3e-6 [1/A^(2)]
    double sldSolv;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0001 [1/cm]
	double background;
} FlexCylEXParameters;



/// 1D scattering function
double flexcyl_ellipX_analytical_1D(FlexCylEXParameters *pars, double q);

/// 2D scattering function
double flexcyl_ellipX_analytical_2D(FlexCylEXParameters *pars, double q, double phi);
double flexcyl_ellipX_analytical_2DXY(FlexCylEXParameters *pars, double qx, double qy);

#endif

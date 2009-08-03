/*
	TODO: Add 2D model
*/

#if !defined(flexible_cylinder_h)
#define flexible_cylinder_h
/** Structure definition for Flexible cylinder parameters
 * [PYTHONCLASS] = FlexibleCylinderModel
 * [DISP_PARAMS] = length, kuhn_length, radius
   [DESCRIPTION] = <text> Note : 'scale' and 'contrast' are both multiplicative factors in the
		model and are perfectly correlated. One or
		both of these parameters must be held fixed
		during model fitting.
		</text>
	[FIXED]= <text>length.width; kuhn_length.width; radius.width</text>
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
    /// Contrast [1/A²]
    //  [DEFAULT]=contrast=5.3e-6 [1/A²]
    double contrast;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0001 [1/cm]
	double background;


} FlexibleCylinderParameters;



/// 1D scattering function
double flexible_cylinder_analytical_1D(FlexibleCylinderParameters *pars, double q);

/// 2D scattering function
double flexible_cylinder_analytical_2D(FlexibleCylinderParameters *pars, double q, double phi);
double flexible_cylinder_analytical_2DXY(FlexibleCylinderParameters *pars, double qx, double qy);

#endif

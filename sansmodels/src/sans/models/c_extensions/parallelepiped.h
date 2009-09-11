/*
	TODO: Add 2D model
*/

#if !defined(parallelepiped_h)
#define parallelepiped_h
/** Structure definition for Parallelepiped parameters
 * [PYTHONCLASS] = ParallelepipedModel
 * [DISP_PARAMS] = short_a, short_b, long_c,parallel_phi,parallel_psi, parallel_theta
   [DESCRIPTION] = <text> Form factor for a rectangular solid with uniform scattering length density.

		scale:Scale factor
		short_a: length of short edge  [A]
		short_b: length of another short edge [A]
		long_c: length of long edge  of the parallelepiped [A]
		contrast: particle_sld - solvent_sld
		background:Incoherent Background [1/cm]
		</text>
	[FIXED]= <text>short_a.width; short_b.width; long_c.width;parallel_phi.width;parallel_psi.width; parallel_theta.width</text>
	[ORIENTATION_PARAMS]= <text>parallel_phi;parallel_psi; parallel_theta; parallel_phi.width;parallel_psi.width; parallel_theta.width</text>


 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    ///  Length of short edge of the parallelepiped [A]
    //  [DEFAULT]=short_a=35 [A]
    double short_a;
	/// Length of short edge edge of the parallelepiped [A]
    //  [DEFAULT]=short_b=75 [A]
    double short_b;
	/// Length of long edge of the parallelepiped [A]
    //  [DEFAULT]=long_c=400 [A]
    double long_c;
    /// Contrast [1/A²]
    //  [DEFAULT]=contrast=53e-7 [1/A²]
    double contrast;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;
    /// Orientation of the parallelepiped axis w/respect incoming beam [rad]
    //  [DEFAULT]=parallel_theta=0.0 [rad]
    double parallel_theta;
    /// Orientation of the longitudinal axis of the parallelepiped in the plane of the detector [rad]
    //  [DEFAULT]=parallel_phi=0.0 [rad]
    double parallel_phi;
    /// Orientation of the cross-sectional minor axis of the parallelepiped in the plane of the detector [rad]
    //  [DEFAULT]=parallel_psi=0.0 [rad]
    double parallel_psi;


} ParallelepipedParameters;



/// 1D scattering function
double parallelepiped_analytical_1D(ParallelepipedParameters *pars, double q);

/// 2D scattering function
double parallelepiped_analytical_2D(ParallelepipedParameters *pars, double q, double phi);
double parallelepiped_analytical_2DXY(ParallelepipedParameters *pars, double qx, double qy);
double parallelepiped_analytical_2D_scaled(ParallelepipedParameters *pars, double q, double q_x, double q_y);
#endif

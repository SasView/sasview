/*
	TODO: Add 2D model
*/

#if !defined(parallelepiped_h)
#define parallelepiped_h
/** Structure definition for Parallelepiped parameters
 * [PYTHONCLASS] = ParallelepipedModel
 * [DISP_PARAMS] = short_edgeA, longer_edgeB, longuest_edgeC,parallel_phi, parallel_theta
   [DESCRIPTION] = <text> Calculates the form factor for a rectangular solid with uniform scattering length density.
		
		scale:Scale factor
		short_edgeA: Shortest edge of the parallelepiped [A]
		longer_edgeB: Longer edge of the parallelepiped [A]
		longuest_edgeC: Longuest edge of the parallelepiped [A]
		constrast: particle_sld - solvent_sld
		background:Incoherent Background [1/cm] 
		</text>
	[FIXED]= <text>short_edgeA.width; longer_edgeB.width; longuest_edgeC.width;parallel_phi.width; parallel_theta.width</text>
	[ORIENTATION_PARAMS]= <text>parallel_phi; parallel_theta; parallel_phi.width; parallel_theta.width</text>


 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Shortest edge of the parallelepiped [A]
    //  [DEFAULT]=short_edgeA=35 [A]
    double short_edgeA;
	/// Longer edge of the parallelepiped [A]
    //  [DEFAULT]=longer_edgeB=75 [A]
    double longer_edgeB;
	/// Longuest edge of the parallelepiped [A]
    //  [DEFAULT]=longuest_edgeC=400 [A]
    double longuest_edgeC;
    /// Contrast [1/A²]
    //  [DEFAULT]=contrast=5.3e-6 [1/A²]
    double contrast;
	/// Incoherent Background [1/cm] 
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;
    /// Orientation of the parallelepiped axis w/respect incoming beam [rad]
    //  [DEFAULT]=parallel_theta=1.0 [rad]
    double parallel_theta;
    /// Orientation of the parallelepiped in the plane of the detector [rad]
    //  [DEFAULT]=parallel_phi=1.0 [rad]
    double parallel_phi;


} ParallelepipedParameters;



/// 1D scattering function
double parallelepiped_analytical_1D(ParallelepipedParameters *pars, double q);

/// 2D scattering function
double parallelepiped_analytical_2D(ParallelepipedParameters *pars, double q, double phi);
double parallelepiped_analytical_2DXY(ParallelepipedParameters *pars, double qx, double qy);
double parallelepiped_analytical_2D_scaled(ParallelepipedParameters *pars, double q, double q_x, double q_y);

#endif

/*
	TODO: Add 2D model
*/

#if !defined(stacked_disks_h)
#define stacked_disks_h
/** Structure definition for stacked disks parameters
 * [PYTHONCLASS] = StackedDisksModel
 * [DISP_PARAMS] = length, radius, axis_theta, axis_phi
   [DESCRIPTION] = <text>
		</text>
	[FIXED]= <text>length.width; radius.width; axis_theta.width; axis_phi.width</text>
	[ORIENTATION_PARAMS]= <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>


 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=0.01
    double scale;
	/// radius of the staked disk [A]
    //  [DEFAULT]=radius=3000 [A]
    double radius;
    /// Length of the staked disk [A]
    //  [DEFAULT]=length=10.0 [A]
    double length;
	/// Thickness of the staked disk [A]
    //  [DEFAULT]=thickness=15.0 [A]
    double thickness;
	/// Core scattering length density[1/A²]
    //  [DEFAULT]=core_sld=4e-6 [1/A²]
    double core_sld;
	/// layer scattering length density[1/A²]
    //  [DEFAULT]=layer_sld=-4e-7 [1/A²]
    double layer_sld;
	/// solvent scattering length density[1/A²]
    //  [DEFAULT]=solvent_sld=5.0e-6 [1/A²]
    double solvent_sld;
    /// number of layers
    //  [DEFAULT]=nlayers=1
	double nlayers;
    /// GSD of disks spacing
    //  [DEFAULT]=spacing=0
    double spacing;
	/// Incoherent Background [1/cm] 
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
    /// Orientation of the staked disk axis w/respect incoming beam [rad]
    //  [DEFAULT]=axis_theta=1.0 [rad]
    double axis_theta;
    /// Orientation of the  staked disk in the plane of the detector [rad]
    //  [DEFAULT]=axis_phi=1.0 [rad]
    double axis_phi;


} StackedDisksParameters;



/// 1D scattering function
double stacked_disks_analytical_1D(StackedDisksParameters *pars, double q);

/// 2D scattering function
double stacked_disks_analytical_2D(StackedDisksParameters *pars, double q, double phi);
double stacked_disks_analytical_2DXY(StackedDisksParameters *pars, double qx, double qy);
double stacked_disks_analytical_2D_scaled(StackedDisksParameters *pars, double q, double q_x, double q_y);

#endif

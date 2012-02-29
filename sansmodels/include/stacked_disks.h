/*
	TODO: Add 2D model
 */

#if !defined(stacked_disks_h)
#define stacked_disks_h
#include "parameters.hh"

/** Structure definition for stacked disks parameters
 * [PYTHONCLASS] = StackedDisksModel
 * [DISP_PARAMS] = core_thick, layer_thick, radius, axis_theta, axis_phi
   [DESCRIPTION] = <text> One layer of disk consists of a core, a top layer, and a bottom layer.
		radius =  the radius of the disk
		core_thick = thickness of the core
		layer_thick = thickness of a layer
		core_sld = the SLD of the core
		layer_sld = the SLD of the layers
		n_stacking = the number of the disks
		sigma_d =  Gaussian STD of d-spacing
		solvent_sld = the SLD of the solvent
		</text>
	[FIXED]= <text>core_thick.width;layer_thick.width; radius.width; axis_theta.width; axis_phi.width</text>
	[ORIENTATION_PARAMS]= <text>axis_phi; axis_theta; axis_phi.width; axis_theta.width</text>


 **/

class StackedDisksModel{
public:
  // Model parameters

  /// Scale factor
  //  [DEFAULT]=scale=0.01
  Parameter scale;
  /// Thickness of the core disk [A]
  //  [DEFAULT]=core_thick=10.0 [A]
  Parameter core_thick;
  /// radius of the staked disk [A]
  //  [DEFAULT]=radius=3000 [A]
  Parameter radius;
  /// Thickness of the staked disk [A]
  //  [DEFAULT]=layer_thick=15.0 [A]
  Parameter layer_thick;
  /// Core scattering length density[1/A^(2)]
  //  [DEFAULT]=core_sld=4e-6 [1/A^(2)]
  Parameter core_sld;
  /// layer scattering length density[1/A^(2)]
  //  [DEFAULT]=layer_sld=-4e-7 [1/A^(2)]
  Parameter layer_sld;
  /// solvent scattering length density[1/A^(2)]
  //  [DEFAULT]=solvent_sld=5.0e-6 [1/A^(2)]
  Parameter solvent_sld;
  /// number of stacking
  //  [DEFAULT]=n_stacking=1
  Parameter n_stacking;
  /// GSD of disks sigma_d
  //  [DEFAULT]=sigma_d=0
  Parameter sigma_d;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;
  /// Orientation of the staked disk axis w/respect incoming beam [rad]
  //  [DEFAULT]=axis_theta=0.0 [rad]
  Parameter axis_theta;
  /// Orientation of the  staked disk in the plane of the detector [rad]
  //  [DEFAULT]=axis_phi=0.0 [rad]
  Parameter axis_phi;

  // Constructor
  StackedDisksModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

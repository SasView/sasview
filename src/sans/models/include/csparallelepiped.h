/*
	TODO: Add 2D model
*/

#if !defined(csparallelepiped_h)
#define csparallelepiped_h
#include "parameters.hh"
/** Structure definition for CSParallelepiped parameters
 * [PYTHONCLASS] = CSParallelepipedModel
 * [DISP_PARAMS] = shortA, midB, longC,parallel_phi,parallel_psi, parallel_theta
   [DESCRIPTION] = <text> Form factor for a rectangular Shell. Below are the Parameters.
		scale: scale factor
		shortA: length of short edge  [A]
		midB: length of another short edge [A]
		longC: length of long edge  of the parallelepiped [A]
		rimA: length of short edge  [A]
		rimB: length of another short edge [A]
		rimC: length of long edge  of the parallelepiped [A]
		sld_rimA: sld of rimA [1/A^(2)]
		sld_rimB: sld of rimB [1/A^(2)]
		sld_rimC: sld of rimC [1/A^(2)]
		sld_core: Pipe_sld [1/A^(2)]
		sld_solv: solvent_sld [1/A^(2)]
		background: incoherent Background [1/cm]
		</text>
	[FIXED]= <text>shortA.width; midB.width; longC.width;parallel_phi.width;parallel_psi.width; parallel_theta.width</text>
	[ORIENTATION_PARAMS]= <text>parallel_phi;parallel_psi; parallel_theta; parallel_phi.width;parallel_psi.width; parallel_theta.width</text>


 **/

class CSParallelepipedModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  ///  Length of short edge of the parallelepiped [A]
  //  [DEFAULT]=shortA=35 [A]
  Parameter shortA;
  /// Length of mid edge of the parallelepiped [A]
  //  [DEFAULT]=midB=75 [A]
  Parameter midB;
  /// Length of long edge of the parallelepiped [A]
  //  [DEFAULT]=longC=400 [A]
  Parameter longC;
  ///  Thickness of rimA [A]
  //  [DEFAULT]=rimA=10 [A]
  Parameter rimA;
  /// Thickness of rimB [A] [A]
  //  [DEFAULT]=rimB=10 [A]
  Parameter rimB;
  /// Thickness of rimC [A] [A]
  //  [DEFAULT]=rimC=10 [A]
  Parameter rimC;
  /// SLD_rimA [1/A^(2)]
  //  [DEFAULT]=sld_rimA=2e-6 [1/A^(2)]
  Parameter sld_rimA;
  /// SLD_rimB [1/A^(2)]
  //  [DEFAULT]=sld_rimB=4e-6 [1/A^(2)]
  Parameter sld_rimB;
  /// SLD_rimC [1/A^(2)]
  //  [DEFAULT]=sld_rimC=2e-6 [1/A^(2)]
  Parameter sld_rimC;
  /// SLD_pcore [1/A^(2)]
  //  [DEFAULT]=sld_pcore=1e-6 [1/A^(2)]
  Parameter sld_pcore;
  /// sld_solv [1/A^(2)]
  //  [DEFAULT]=sld_solv=6e-6 [1/A^(2)]
  Parameter sld_solv;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.06 [1/cm]
  Parameter background;
  /// Orientation of the parallelepiped axis w/respect incoming beam [deg]
  //  [DEFAULT]=parallel_theta=0.0 [deg]
  Parameter parallel_theta;
  /// Orientation of the longitudinal axis of the parallelepiped in the plane of the detector [deg]
  //  [DEFAULT]=parallel_phi=0.0 [deg]
  Parameter parallel_phi;
  /// Orientation of the cross-sectional minor axis of the parallelepiped in the plane of the detector [deg]
  //  [DEFAULT]=parallel_psi=0.0 [deg]
  Parameter parallel_psi;

  // Constructor
  CSParallelepipedModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

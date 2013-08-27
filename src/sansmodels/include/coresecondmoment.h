#if !defined(coresecondmoment_h)
#define coresecondmoment_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = Core2ndMomentModel
 //[DISP_PARAMS] = radius_core
 //[DESCRIPTION] =<text>Calculate CoreSecondMoment Model
 //
 //				scale:calibration factor,
 //				density_poly: density of the layer
 //				sld_poly: the SLD of the layer
 //				volf_cores: volume fraction of cores
 //				ads_amount: adsorbed amount
 //				second_moment: second moment of the layer
 //				sld_solv: the SLD of the solvent
 //				background
 //
 //		</text>
 //[FIXED]=  radius_core.width
 //[ORIENTATION_PARAMS]= <text> </text>

class Core2ndMomentModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Density of layer[g/cm^(3)]
  //  [DEFAULT]=density_poly=0.7 [g/cm^(3)]
  Parameter density_poly;

  /// sld_poly [1/A^(2)]
  //  [DEFAULT]=sld_poly= 1.5e-6 [1/A^(2)]
  Parameter sld_poly;

  /// radius_core [A]
  //  [DEFAULT]=radius_core= 500.0 [A]
  Parameter radius_core;

  // Model parameters
  /// volume fraction of_cores
  //  [DEFAULT]=volf_cores= 0.14
  Parameter volf_cores;

  /// adsorbed amount [mg/m^(2)]
  //  [DEFAULT]=ads_amount=1.9 [mg/m^(2)]
  Parameter ads_amount;

  /// sld_solv [1/A^(2)]
  //  [DEFAULT]=sld_solv= 6.3e-6 [1/A^(2)]
  Parameter sld_solv;

  /// second_moment [A]
  //  [DEFAULT]=second_moment=23.0 [A]
  Parameter second_moment;

 /// Incoherent Background [1/cm]
 //  [DEFAULT]=background=0 [1/cm]
 Parameter background;

  // Constructor
 Core2ndMomentModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};


#endif

#if !defined(Hardsphere_h)
#define Hardsphere_h
#include "parameters.hh"

/**
 * Structure definition for HardsphereStructure (factor) parameters
 */
//[PYTHONCLASS] = HardsphereStructure
//[DISP_PARAMS] = effect_radius
//[DESCRIPTION] =<text>Structure factor for interacting particles:                   .
//
//  The interparticle potential is
//
//                     U(r)= inf   , r < 2R
//                         = 0     , r >= 2R
//
//						R: effective radius of the Hardsphere particle
//						V:The volume fraction
//
//    Ref: Percus., J. K.,etc., J. Phy.
//     Rev. 1958, 110, 1.
//	 </text>
//[FIXED]= effect_radius.width

class HardsphereStructure{
public:
  // Model parameters
  /// effect radius of hardsphere [A]
  //  [DEFAULT]=effect_radius=50.0 [A]
  Parameter effect_radius;

  /// Volume fraction
  //  [DEFAULT]=volfraction= 0.2
  Parameter volfraction;

  // Constructor
  HardsphereStructure();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

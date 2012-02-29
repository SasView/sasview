#if !defined(StickyHS_h)
#define StickyHS_h
#include "parameters.hh"

/**
 * Structure definition for StickyHS_struct (struncture factor) parameters
 */
//[PYTHONCLASS] = StickyHSStructure
//[DISP_PARAMS] = effect_radius
//[DESCRIPTION] =<text> Structure Factor for interacting particles:                               .
//
//  The interaction potential is
//
//                     U(r)= inf , r < 2R
//                         = -Uo  , 2R < r < 2R + w
//                         = 0   , r >= 2R +w
//
//						R: effective radius of the hardsphere
//                     stickiness = [exp(Uo/kT)]/(12*perturb)
//                     perturb = w/(w+ 2R) , 0.01 =< w <= 0.1
//                     w: The width of the square well ,w > 0
//						v: The volume fraction , v > 0
//
//                     Ref: Menon, S. V. G.,et.al., J. Chem.
//                      Phys., 1991, 95(12), 9186-9190.
//				</text>
//[FIXED]= effect_radius.width

class StickyHSStructure{
public:
  // Model parameters
  /// effect radius of hardsphere [A]
  //  [DEFAULT]=effect_radius=50.0 [A]
  Parameter effect_radius;

  /// Volume fraction
  //  [DEFAULT]=volfraction= 0.1
  Parameter volfraction;

  /// Perturbation Parameter ( between 0.01 - 0.1)
  //  [DEFAULT]=perturb=0.05
  Parameter perturb;

  /// Stickiness
  //  [DEFAULT]=stickiness= 0.2
  Parameter stickiness;

  // Constructor
  StickyHSStructure();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

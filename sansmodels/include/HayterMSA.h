#if !defined(HayterMSA_h)
#define HayterMSA_h
#include "parameters.hh"

/**
 * Structure definition for screened Coulomb interaction
 */
//[PYTHONCLASS] = HayterMSAStructure
//[DISP_PARAMS] = effect_radius
//[DESCRIPTION] =<text>To calculate the structure factor (the Fourier transform of the
//                     pair correlation function g(r)) for a system of
//                     charged, spheroidal objects in a dielectric
//						medium.
//                     When combined with an appropriate form
//                     factor, this allows for inclusion of
//                     the interparticle interference effects
//                     due to screened coulomb repulsion between
//                     charged particles.
//						(Note: charge > 0 required.)
//
//                     Ref: JP Hansen and JB Hayter, Molecular
//                           Physics 46, 651-656 (1982).
//
//				</text>
//[FIXED]= effect_radius.width

class HayterMSAStructure{
public:
  // Model parameters
  /// effetitve radius of particle [A]
  //  [DEFAULT]=effect_radius=20.75 [A]
  Parameter effect_radius;

  /// charge
  //  [DEFAULT]=charge= 19
  Parameter charge;

  /// Volume fraction
  //  [DEFAULT]=volfraction= 0.0192
  Parameter volfraction;

  /// Temperature [K]
  //  [DEFAULT]=temperature= 318.16 [K]
  Parameter temperature;

  /// Monovalent salt concentration [M]
  //  [DEFAULT]=saltconc= 0 [M]
  Parameter saltconc;

  /// Dielectric constant of solvent
  //  [DEFAULT]=dielectconst= 71.08
  Parameter dielectconst;

  // Constructor
  HayterMSAStructure();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

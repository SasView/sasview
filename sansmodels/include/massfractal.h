#if !defined(massfractal_h)
#define massfractal_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
//[PYTHONCLASS] = MassFractalModel
//[DESCRIPTION] =<text> The scattering intensity  I(x) = scale*P(x)*S(x) + background, where
//		 scale = scale_factor  * V * delta^(2)
//       p(x)=  F(x*radius)^(2)
//       F(x) = 3*[sin(x)-x cos(x)]/x**3
//       S(x) = [(gamma(Dm-1)*colength^(Dm-1)*[1+(x^2*colength^2)]^((1-Dm)/2)
//						* sin[(Dm-1)*arctan(x*colength)])/x]
//       where delta = sldParticle -sldSolv.
//       radius       =  Particle radius
//       mass_dim  =  Mass fractal dimension
//       co_length  =  Cut-off length
//       background   =  background
//		Ref.:Mildner, Hall,J Phys D Appl Phys(1986), 9, 1535-1545
//		Note I: This model is valid for 1<mass_dim<6.
//		Note II: This model is not in absolute scale.
//		</text>
//[ORIENTATION_PARAMS]= <text> </text>

class MassFractalModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Radius [A]
  //  [DEFAULT]=radius=10.0 [A]
  Parameter radius;

  /// Mass fractal dimension
  //  [DEFAULT]=mass_dim=1.9
  Parameter mass_dim;

  /// Cut-off Length [A]
  //  [DEFAULT]=co_length=100.0 [A]
  Parameter co_length;

  /// Incoherent Background
  //  [DEFAULT]=background=0.0
  Parameter background;

  // Constructor
  MassFractalModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

#if !defined(surfacefractal_h)
#define surfacefractal_h
#include "parameters.hh"

/**
 * Structure definition for parameters
 */
//[PYTHONCLASS] = SurfaceFractalModel
//[DESCRIPTION] =<text> The scattering intensity  I(x) = scale*P(x)*S(x) + background, where
//		 scale = scale_factor  * V * delta^(2)
//       p(x)=  F(x*radius)^(2)
//       F(x) = 3*[sin(x)-x cos(x)]/x**3
//       S(x) = [(gamma(5-Ds)*colength^(5-Ds)*[1+(x^2*colength^2)]^((Ds-5)/2)
//						* sin[(Ds-5)*arctan(x*colength)])/x]
//       where delta = sldParticle -sldSolv.
//       radius       =  Particle radius
//       surface_dim  =  Surface fractal dimension (Ds)
//       co_length  =  Cut-off length
//       background   =  background
//		Ref.:Mildner, Hall,J Phys D Appl Phys(1986), 19, 1535-1545
//		Note I: This model is valid for 1<surface_dim<3 with limited q range.
//		Note II: This model is not in absolute scale.
//		</text>
//[ORIENTATION_PARAMS]= <text> </text>

class SurfaceFractalModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Radius [A]
  //  [DEFAULT]=radius=10.0 [A]
  Parameter radius;

  /// Surface fractal dimension
  //  [DEFAULT]=surface_dim=2.0
  Parameter surface_dim;

  /// Cut-off Length [A]
  //  [DEFAULT]=co_length=500.0 [A]
  Parameter co_length;

  /// Incoherent Background
  //  [DEFAULT]=background=0.0
  Parameter background;

  // Constructor
  SurfaceFractalModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

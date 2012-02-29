#if !defined(masssurfacefractal_h)
#define masssurfacefractal_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
//[PYTHONCLASS] = MassSurfaceFractal
//[DESCRIPTION] =<text> The scattering intensity  I(x) = scale*P(x) + background,
//       p(x)= {[1+(x^2*a)]^(Dm/2) * [1+(x^2*b)]^(6-Ds-Dm)/2}^(-1)
//       a = Rg^2/(3*Dm/2)
//       b = rg^2/(3*(6-Ds-Dm)/2)
//       scale        =  scale factor * N*Volume^2*contrast^2
//       mass_dim       =  Dm (mass fractal dimension)
//       surface_dim  =  Ds
//       cluster_rg  =  Rg
//       primary_rg    =  rg
//       background   =  background
//	Ref: Schmidt, J Appl Cryst, eq(19), (1991), 24, 414-435
//       : Hurd, Schaefer, Martin, Phys Rev A, eq(2),(1987),35, 2361-2364
//  Note that 0 < Ds< 6 and 0 < Dm < 6.
//		</text>
//[ORIENTATION_PARAMS]= <text> </text>

class MassSurfaceFractal{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale= 1.0
  Parameter scale;

  /// Mass fractal dimension
  //  [DEFAULT]=mass_dim=1.8
  Parameter mass_dim;

  /// Surface fractal dimension
  //  [DEFAULT]=surface_dim=2.3
  Parameter surface_dim;

  /// cluster_rg [A]
  //  [DEFAULT]=cluster_rg=86.7 [A]
  Parameter cluster_rg;

 /// primary_rg [A]
  //  [DEFAULT]=primary_rg=4000.0 [A]
  Parameter primary_rg;

  /// Incoherent Background
  //  [DEFAULT]=background=0.0
  Parameter background;

  // Constructor
  MassSurfaceFractal();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

#if !defined(fractal_h)
#define fractal_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
//[PYTHONCLASS] = FractalModel
//[DISP_PARAMS] = radius
//[DESCRIPTION] =<text> The scattering intensity  I(x) = P(|x|)*S(|x|) + background, where
//       p(x)= scale * V * delta^(2)* F(x*radius)^(2)
//       F(x) = 3*[sin(x)-x cos(x)]/x**3
//       where delta = sldBlock -sldSolv.
//       scale        =  scale factor * Volume fraction
//       radius       =  Block radius
//       fractal_dim  =  Fractal dimension
//       cor_length  =  Correlation Length
//       sldBlock    =  SDL block
//       sldSolv  =  SDL solvent
//       background   =  background
//		</text>
//[FIXED]= <text> radius.width </text>
//[ORIENTATION_PARAMS]= <text> </text>

class FractalModel{
public:
  // Model parameters
  /// Radius of gyration [A]
  //  [DEFAULT]=radius=5.0 [A]
  Parameter radius;

  /// Scale factor
  //  [DEFAULT]=scale= 0.05
  Parameter scale;

  /// Fractal dimension
  //  [DEFAULT]=fractal_dim=2.0
  Parameter fractal_dim;

  /// Correlation Length [A]
  //  [DEFAULT]=cor_length=100.0 [A]
  Parameter cor_length;

  /// SDL block [1/A^(2)]
  //  [DEFAULT]=sldBlock=2.0e-6 [1/A^(2)]
  Parameter sldBlock;

  /// SDL solvent [1/A^(2)]
  //  [DEFAULT]=sldSolv= 6.35e-6 [1/A^(2)]
  Parameter sldSolv;

  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  // Constructor
  FractalModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

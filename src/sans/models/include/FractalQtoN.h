#if !defined(FractalQtoN_h)
#define FractalQtoN_h
#include "parameters.hh"

/**
 * Structure definition for FractalO_Z (factor) parameters
 */
//[PYTHONCLASS] = FractalO_Z
//[DESCRIPTION] =<text>Structure factor for interacting particles:                   
// Schmidt J Appl Cryst (1991), 24, 414-435 See equation (19)
// Hurd; Schaefer; Martin, Phys Rev A (1987), 35, 2361-2364 See equation (2)
// </text>.

class FractalO_Z{
public:

  // Model parameters

  /// Something scale
  //  [DEFAULT]=scale= 10000.0
  Parameter scale;

  //  [DEFAULT]=m_fractal= 1.8
  Parameter m_fractal;

  //  [DEFAULT]=cluster_rg= 3520.0
  Parameter cluster_rg;
  
  //  [DEFAULT]=s_fractal= 2.5
  Parameter s_fractal;

  //  [DEFAULT]=primary_rg= 82.0
  Parameter primary_rg;

  //  [DEFAULT]=background= 0.01
  Parameter background;


  // Constructor
  FractalO_Z();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

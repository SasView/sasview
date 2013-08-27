#if !defined(GelFit_h)
#define GelFit_h
#include "parameters.hh"

/**
 * Structure definition for GelFitModel (factor) parameters
 */
//[PYTHONCLASS] = GelFitModel
//[DESCRIPTION] =<text>Structure factor for interacting particles:                   .
//  Shibayama-Geissler Two-Length Scale Fit for Gels
//  (GelFit)
//
//  Sibayama; Tanaka; Han J Chem Phys(1992), 97(9), 6829-6841
//  Mallam; Horkay; Hecht; Rennie; Geissler, Macromol(1991), 24, 543
//	 </text>

class GelFitModel{
public:

  // Model parameters

  /// Something lScale
  //  [DEFAULT]=lScale= 3.5
  Parameter lScale;

  //  [DEFAULT]=gScale= 1.7
  Parameter gScale;

  //  [DEFAULT]=zeta= 16
  Parameter zeta;
  
  //  [DEFAULT]=radius= 104
  Parameter radius;

  //  [DEFAULT]=scale= 2
  Parameter scale;

  //  [DEFAULT]=background= 0.01
  Parameter background;


  // Constructor
  GelFitModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

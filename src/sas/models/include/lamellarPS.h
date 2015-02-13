/*
	TODO: Add 2D model
 */

#if !defined(lamellarPS_h)
#define lamellarPS_h
#include "parameters.hh"

/** Structure definition for concentrated lamellar form factor parameters
 * [PYTHONCLASS] = LamellarPSModel
 * [DISP_PARAMS] = delta, spacing
   [DESCRIPTION] = <text>[Concentrated Lamellar Form Factor] Calculates the scattered
	   intensity from a lyotropic lamellar phase.
	   The intensity (form factor and structure
	   factor)calculated is for lamellae of
	   uniform scattering length density that
	   are randomly distributed in solution
	   (a powder average). The lamellae thickness
		is polydisperse. The model can also
		be applied to large, multi-lamellar vesicles.
		No resolution smeared version is included
		in the structure factor of this model.
 *Parameters: spacing = repeat spacing,
		delta = bilayer thickness,
		sld_bi = SLD_bilayer
		sld_sol = SLD_solvent
		n_plate = # of Lamellar plates
		caille = Caille parameter (<0.8 or <1)
		background = incoherent bgd
		scale = scale factor
</text>
   [FIXED]= <text>delta.width; spacing.width</text>
   [ORIENTATION_PARAMS]=

 **/

class LamellarPSModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// repeat spacing of the lamellar [A]
  //  [DEFAULT]=spacing=400 [A]
  Parameter spacing;
  /// bilayer thicknes [A]
  //  [DEFAULT]=delta=30 [A]
  Parameter delta;
  /// SLD of bilayer [1/A^(2)]
  //  [DEFAULT]=sld_bi=6.3e-6 [1/A^(2)]
  Parameter sld_bi;
  /// SLD of solvent [1/A^(2)]
  //  [DEFAULT]=sld_sol=1.0e-6 [1/A^(2)]
  Parameter sld_sol;
  /// Number of lamellar plates
  //  [DEFAULT]=n_plates=20
  Parameter n_plates;
  /// caille parameters
  //  [DEFAULT]=caille=0.1
  Parameter caille;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;
  // Constructor
  LamellarPSModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

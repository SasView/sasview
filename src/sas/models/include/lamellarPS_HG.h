/*
	TODO: Add 2D model
 */

#if !defined(lamellarPS_HG_h)
#define lamellarPS_HG_h
#include "parameters.hh"

/** Structure definition for concentrated lamellar form factor parameters
 * [PYTHONCLASS] = LamellarPSHGModel
 * [DISP_PARAMS] = deltaT,deltaH,spacing
   [DESCRIPTION] = <text>[Concentrated Lamellar (head+tail) Form Factor]: Calculates the
	   intensity from a lyotropic lamellar phase.
	   The intensity (form factor and structure factor)
		calculated is for lamellae of two-layer scattering
		length density that are randomly distributed in
		solution (a powder average). The scattering
		length density of the tail region, headgroup
		region, and solvent are taken to be different.
		The model can also be applied to large,
		multi-lamellar vesicles.
		No resolution smeared version is included
		in the structure factor of this model.
 *Parameters: spacing = repeat spacing,
		deltaT = tail length,
		deltaH = headgroup thickness,
		n_plates = # of Lamellar plates
		caille = Caille parameter (<0.8 or <1)
		background = incoherent bgd
		scale = scale factor ...
</text>
   [FIXED]= deltaT.width;deltaH.width;spacing.width
   [ORIENTATION_PARAMS]=
 **/

class LamellarPSHGModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// repeat spacing of the lamellar [A]
  //  [DEFAULT]=spacing=40 [A]
  Parameter spacing;
  ///  tail thickness [A]
  //  [DEFAULT]=deltaT=10 [A]
  Parameter deltaT;
  ///  head thickness [A]
  //  [DEFAULT]=deltaH=2.0 [A]
  Parameter deltaH;
  /// scattering density length of tails [1/A^(2)]
  //  [DEFAULT]=sld_tail=0.4e-6 [1/A^(2)]
  Parameter sld_tail;
  /// scattering density length of head [1/A^(2)]
  //  [DEFAULT]=sld_head=2e-6 [1/A^(2)]
  Parameter sld_head;
  /// scattering density length of solvent [1/A^(2)]
  //  [DEFAULT]=sld_solvent=6e-6 [1/A^(2)]
  Parameter sld_solvent;
  /// Number of lamellar plates
  //  [DEFAULT]=n_plates=30
  Parameter n_plates;
  /// caille parameters
  //  [DEFAULT]=caille=0.001
  Parameter caille;
  /// Incoherent Background [1/cm]
  //  [DEFAULT]=background=0.001 [1/cm]
  Parameter background;

  // Constructor
  LamellarPSHGModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

#if !defined(lamellarPC_h)
#define lamellarPC_h
#include "parameters.hh"

/** Structure definition for lamellar_paracrystal parameters
 * [PYTHONCLASS] = LamellarPCrystalModel
 * [DISP_PARAMS] =  thickness
   [DESCRIPTION] = <text>[Lamellar ParaCrystal Model] Parameter Definitions: scale = scale factor,
			background = incoherent background
			thickness = lamellar thickness,
			sld_layer = layer scattering length density ,
			sld_solvent = solvent scattering length density.
			Nlayers = no. of lamellar layers
			spacing = spacing between layers
			pd_spacing = polydispersity of spacing
			Note: This model can be used for large
				multilamellar vesicles.

	</text>
	[FIXED]= thickness.width;
	[ORIENTATION_PARAMS]=
 **/

class LamellarPCrystalModel{
public:
  // Model parameters
  /// Scale factor
  //  [DEFAULT]=scale=1.0
  Parameter scale;
  /// thickness
  //  [DEFAULT]=thickness=33.0 [A]
  Parameter thickness;
  /// Nlayers
  //  [DEFAULT]=Nlayers=20.0
  Parameter Nlayers;
  /// spacing
  //  [DEFAULT]=spacing=250.0 [A]
  Parameter spacing;
  /// poly-dispersity of spacing
  //  [DEFAULT]=pd_spacing=0.0
  Parameter pd_spacing;
  /// layer scrattering length density[1/A^(2)]
  //  [DEFAULT]=sld_layer=1.0e-6 [1/A^(2)]
  Parameter sld_layer;
  /// solvent scrattering length density[1/A^(2)]
  //  [DEFAULT]=sld_solvent=6.34e-6 [1/A^(2)]
  Parameter sld_solvent;
  /// Incoherent Background [1/cm] 0.00
  //  [DEFAULT]=background=0.0 [1/cm]
  Parameter background;

  // Constructor
  LamellarPCrystalModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

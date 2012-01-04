#if !defined(lamellarPC_h)
#define lamellarPC_h
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
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// thickness
    //  [DEFAULT]=thickness=33.0 [A]
    double thickness;
    /// Nlayers
    //  [DEFAULT]=Nlayers=20.0
    double Nlayers;
    /// spacing
    //  [DEFAULT]=spacing=250.0 [A]
    double spacing;
    /// poly-dispersity of spacing
    //  [DEFAULT]=pd_spacing=0.0
    double pd_spacing;
    /// layer scrattering length density[1/A^(2)]
    //  [DEFAULT]=sld_layer=1.0e-6 [1/A^(2)]
    double sld_layer;
	/// solvent scrattering length density[1/A^(2)]
    //  [DEFAULT]=sld_solvent=6.34e-6 [1/A^(2)]
    double sld_solvent;
	/// Incoherent Background [1/cm] 0.00
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;

} LamellarPCParameters;



/// 1D scattering function
//double lamellarPC_analytical_1D(LamellarPCParameters *pars, double q);

/// 2D scattering function
//double lamellarPC_analytical_2D(LamellarPCParameters *pars, double q, double phi);
//double lamellarPC_analytical_2DXY(LamellarPCParameters *pars, double qx, double qy);

#endif

/*
	TODO: Add 2D model
*/

#if !defined(lamellarPS_h)
#define lamellarPS_h
/** Structure definition for concentrated lamellar form factor parameters
 * [PYTHONCLASS] = LamellarPSModel
 * [DISP_PARAMS] = spacing
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
		sigma = variation in bilayer thickness
		contrast = SLD_solvent - SLD_bilayer
		n_plate = # of Lamellar plates
		caille = Caille parameter (<0.8 or <1)
		background = incoherent bgd
		scale = scale factor
</text>
   [FIXED]= spacing.width
   [ORIENTATION_PARAMS]=

 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// repeat spacing of the lamellar [A]
    //  [DEFAULT]=spacing=400 [A]
    double spacing;
	/// bilayer thicknes [A]
    //  [DEFAULT]=delta=30 [A]
    double delta;
	/// polydispersity of the bilayer thickness  [A]
    //  [DEFAULT]=sigma=0.15
    double sigma;
    /// Contrast [1/A²]
    //  [DEFAULT]=contrast=5.3e-6 [1/A²]
    double contrast;
	 /// Number of lamellar plates
    //  [DEFAULT]=n_plates=20
    double n_plates;
    /// caille parameters
    //  [DEFAULT]=caille=0.1
    double caille;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;

} LamellarPSParameters;



/// 1D scattering function
double lamellarPS_analytical_1D(LamellarPSParameters *pars, double q);

/// 2D scattering function
double lamellarPS_analytical_2D(LamellarPSParameters *pars, double q, double phi);
double lamellarPS_analytical_2DXY(LamellarPSParameters *pars, double qx, double qy);

#endif

#if !defined(multishell_h)
#define multishell_h

/**
 * Structure definition for sphere parameters

	[PYTHONCLASS] = MultiShellModel
	[DISP_PARAMS] = core_radius, s_thickness, w_thickness
	[DESCRIPTION] =<text> MultiShell (Sphere) Model (or Multilamellar Vesicles): Model parameters;
				scale : scale factor
				core_radius : Core radius of the multishell
				s_thickness: shell thickness
				w_thickness: water thickness
				core_sld: core scattering length density
				shell_sld: shell scattering length density
				n_pairs:number of pairs of water/shell
				background: incoherent background
               </text>
	[FIXED]=  core_radius.width; s_thickness.width; w_thickness.width
	[ORIENTATION_PARAMS]= <text> </text>
 */
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Core radius of the multishell [A]
    //  [DEFAULT]=core_radius=60.0 [A]
    double core_radius;

	///	shell thickness [A]
    //  [DEFAULT]=s_thickness= 10.0 [A]
    double s_thickness;

    ///	water thickness [A]
    //  [DEFAULT]=w_thickness= 10.0 [A]
    double w_thickness;

	///	core scattering length density [1/A^(2)]
    //  [DEFAULT]=core_sld= 6.4e-6 [1/A^(2)]
    double core_sld;

    ///	shell scattering length density [1/A^(2)]
    //  [DEFAULT]=shell_sld= 4.0e-7 [1/A^(2)]
    double shell_sld;

	///	number of pairs of water and shell
    //  [DEFAULT]=n_pairs= 2
    double n_pairs;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;

} MultiShellParameters;



/// 1D scattering function
double multishell_analytical_1D(MultiShellParameters *pars, double q);

/// 2D scattering function
double multishell_analytical_2D(MultiShellParameters *pars, double q, double phi);
double multishell_analytical_2DXY(MultiShellParameters *pars, double qx, double qy);

#endif

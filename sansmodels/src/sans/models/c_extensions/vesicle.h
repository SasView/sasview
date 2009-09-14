#if !defined(vesicle_h)
#define vesicle_h

/**
 * Structure definition for vesicle parameters
[PYTHONCLASS] = VesicleModel
[DISP_PARAMS] = radius,thickness
[DESCRIPTION] =<text>Model parameters:    radius : the core radius of the vesicle
		thickness: the shell thickness
		core_sld: the core SLD
		shell_sld: the shell SLD
		background: incoherent background
		scale : scale factor
</text>
[FIXED]=  radius.width; thickness.width
[ORIENTATION_PARAMS]= <text> </text>
 */
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Core radius of the vesicle [A]
    //  [DEFAULT]=radius= 100.0 [A]
    double radius;

	///	shell thickness [Å]
    //  [DEFAULT]=thickness= 30.0 [A]
    double thickness;

	///	core scattering length density [1/Å²]
    //  [DEFAULT]=core_sld= 6.36e-6 [1/A²]
    double core_sld;

    ///	shell scattering length density [1/Å²]
    //  [DEFAULT]=shell_sld= 5.0e-7 [1/A²]
    double shell_sld;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;

} VesicleParameters;



/// 1D scattering function
double vesicle_analytical_1D(VesicleParameters *pars, double q);

/// 2D scattering function
double vesicle_analytical_2D(VesicleParameters *pars, double q, double phi);
double vesicle_analytical_2DXY(VesicleParameters *pars, double qx, double qy);

#endif

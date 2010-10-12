#if !defined(o_h)
#define refl_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = ReflModel
 //[DISP_PARAMS] = thick_inter0
 //[DESCRIPTION] =<text>Form factor of mutishells normalized by the volume. Here each shell is described
 //						 by an exponential function;
 //							I)
 //							For A_shell != 0,
 //							f(r) = B*exp(A_shell*(r-r_in)/thick_shell)+C
 //                         where
 //								B=(sld_out-sld_in)/(exp(A_shell)-1)
 //								C=sld_in-B.
 //							Note that in the above case,
 //								the function becomes a linear function
 //								as A_shell --> 0+ or 0-.
 //							II)
 //							For the exact point of A_shell == 0,
 //							f(r) = sld_in ,i.e., it crosses over flat function
 //							Note that the 'sld_out' becaomes NULL in this case.
 //
 //				background:background,
 //				rad_core: radius of sphere(core)
 //				thick_shell#:the thickness of the shell#
 //				sld_core: the SLD of the sphere
 //				sld_solv: the SLD of the solvent
 //				sld_shell: the SLD of the shell#
 //				A_shell#: the coefficient in the exponential function
 //		</text>
 //[FIXED]=  <text></text>
 //[NON_FITTABLE_PARAMS]= <text>n_layers;func_inter0;func_inter1;func_inter2;func_inter3;func_inter4;func_inter5;func_inter5;func_inter7;func_inter8;func_inter9;func_inter10 </text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
	/// number of layers
	//  [DEFAULT]=n_layers=1
	int n_layers;
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
	double scale;
    ///	thick_inter0 [A]
    //  [DEFAULT]=thick_inter0=1.0 [A]
	double thick_inter0;
	///	func_inter0
	//  [DEFAULT]=func_inter0= 0
	double func_inter0;
	///	sld_sub0 [1/A^(2)]
	//  [DEFAULT]=sld_sub0= 2.07e-6 [1/A^(2)]
	double sld_sub0;
	///	sld_medium [1/A^(2)]
	//  [DEFAULT]=sld_medium= 1.0e-6 [1/A^(2)]
	double sld_medium;
	/// Background
	//  [DEFAULT]=background=0
	double background;

    //  [DEFAULT]=sld_flat1=4.0e-06 [1/A^(2)]
    double sld_flat1;
    //  [DEFAULT]=sld_flat2=3.5e-06 [1/A^(2)]
    double sld_flat2;
    //  [DEFAULT]=sld_flat3=4.0e-06 [1/A^(2)]
    double sld_flat3;
    //  [DEFAULT]=sld_flat4=3.5e-06 [1/A^(2)]
    double sld_flat4;
    //  [DEFAULT]=sld_flat5=4.0e-06 [1/A^(2)]
    double sld_flat5;
    //  [DEFAULT]=sld_flat6=3.5e-06 [1/A^(2)]
    double sld_flat6;
    //  [DEFAULT]=sld_flat7=4.0e-06 [1/A^(2)]
    double sld_flat7;
    //  [DEFAULT]=sld_flat8=3.5e-06 [1/A^(2)]
    double sld_flat8;
    //  [DEFAULT]=sld_flat9=4.0e-06 [1/A^(2)]
    double sld_flat9;
    //  [DEFAULT]=sld_flat10=3.5e-06 [1/A^(2)]
    double sld_flat10;

    //  [DEFAULT]=thick_inter1=1 [A]
    double thick_inter1;
    //  [DEFAULT]=thick_inter2=1 [A]
    double thick_inter2;
    //  [DEFAULT]=thick_inter3=1 [A]
    double thick_inter3;
    //  [DEFAULT]=thick_inter4=1 [A]
    double thick_inter4;
    //  [DEFAULT]=thick_inter5=1 [A]
    double thick_inter5;
    //  [DEFAULT]=thick_inter6=1 [A]
    double thick_inter6;
    //  [DEFAULT]=thick_inter7=1 [A]
    double thick_inter7;
    //  [DEFAULT]=thick_inter8=1 [A]
    double thick_inter8;
    //  [DEFAULT]=thick_inter9=1 [A]
    double thick_inter9;
    //  [DEFAULT]=thick_inter10=1 [A]
    double thick_inter10;

    //  [DEFAULT]=thick_flat1=10 [A]
    double thick_flat1;
    //  [DEFAULT]=thick_flat2=100 [A]
    double thick_flat2;
    //  [DEFAULT]=thick_flat3=100 [A]
    double thick_flat3;
    //  [DEFAULT]=thick_flat4=100 [A]
    double thick_flat4;
    //  [DEFAULT]=thick_flat5=100 [A]
    double thick_flat5;
    //  [DEFAULT]=thick_flat6=100 [A]
    double thick_flat6;
    //  [DEFAULT]=thick_flat7=100 [A]
    double thick_flat7;
    //  [DEFAULT]=thick_flat8=100 [A]
    double thick_flat8;
    //  [DEFAULT]=thick_flat9=100 [A]
    double thick_flat9;
    //  [DEFAULT]=thick_flat10=100 [A]
    double thick_flat10;

    //  [DEFAULT]=func_inter1=0
    double func_inter1;
    //  [DEFAULT]=func_inter2=0
    double func_inter2;
    //  [DEFAULT]=func_inter3=0
    double func_inter3;
    //  [DEFAULT]=func_inter4=0
    double func_inter4;
    //  [DEFAULT]=func_inter5=0
    double func_inter5;
    //  [DEFAULT]=func_inter6=0
    double func_inter6;
    //  [DEFAULT]=func_inter7=0
    double func_inter7;
    //  [DEFAULT]=func_inter8=0
    double func_inter8;
    //  [DEFAULT]=func_inter9=0
    double func_inter9;
    //  [DEFAULT]=func_inter10=0
    double func_inter10;

    //  [DEFAULT]=sldIM_flat1=0
    double sldIM_flat1;
    //  [DEFAULT]=sldIM_flat2=0
    double sldIM_flat2;
    //  [DEFAULT]=sldIM_flat3=0
    double sldIM_flat3;
    //  [DEFAULT]=sldIM_flat4=0
    double sldIM_flat4;
    //  [DEFAULT]=sldIM_flat5=0
    double sldIM_flat5;
    //  [DEFAULT]=sldIM_flat6=0
    double sldIM_flat6;
    //  [DEFAULT]=sldIM_flat7=0
    double sldIM_flat7;
    //  [DEFAULT]=sldIM_flat8=0
    double sldIM_flat8;
    //  [DEFAULT]=sldIM_flat9=0
    double sldIM_flat9;
    //  [DEFAULT]=sldIM_flat10=0
    double sldIM_flat10;
    //  [DEFAULT]=sldIM_sub0=0
    double sldIM_sub0;
    //  [DEFAULT]=sldIM_medium=0
    double sldIM_medium;

} ReflParameters;

double re_kernel(double dq[], double q);

/// 1D scattering function
double refl_analytical_1D(ReflParameters *pars, double q);

/// 2D scattering function
double refl_analytical_2D(ReflParameters *pars, double q, double phi);
double refl_analytical_2DXY(ReflParameters *pars, double qx, double qy);

#endif

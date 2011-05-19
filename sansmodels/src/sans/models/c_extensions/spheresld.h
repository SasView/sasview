#if !defined(o_h)
#define sphere_sld_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = SphereSLDModel
 //[DISP_PARAMS] = rad_core0, thick_inter0
 //[DESCRIPTION] =<text>Calculate neutron reflectivity using the Parratt iterative formula
 //				Parameters:
 //				background:background
 //				scale: scale factor
 //				sld_core0: the SLD of the substrate
 //				sld_solv: the SLD of the incident medium
 //					or superstrate
 //				sld_flatN: the SLD of the flat region of
 //					the N'th layer
 //				thick_flatN: the thickness of the flat
 //					region of the N'th layer
 //				func_interN: the function used to describe
 //					the interface of the N'th layer
 //				nu_interN: the coefficient for the func_interN
 //				thick_interN: the thickness of the interface
 //					of the N'th layer
 //				Note: the layer number starts to increase
 //					from the bottom (substrate) to the top.
 //		</text>
 //[FIXED]=  <text>rad_core0.width; thick_inter0.width</text>
 //[NON_FITTABLE_PARAMS]= <text>n_shells;func_inter0;func_inter1;func_inter2;func_inter3;func_inter4;func_inter5;func_inter5;func_inter7;func_inter8;func_inter9;func_inter10 </text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
	/// number of shells
	//  [DEFAULT]=n_shells=1
	int n_shells;
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
	double scale;
    ///	thick_inter0 [A]
    //  [DEFAULT]=thick_inter0=50.0 [A]
	double thick_inter0;
	///	func_inter0
	//  [DEFAULT]=func_inter0= 0
	double func_inter0;
	///	sld_core0 [1/A^(2)]
	//  [DEFAULT]=sld_core0= 2.07e-6 [1/A^(2)]
	double sld_core0;
	///	sld_solv [1/A^(2)]
	//  [DEFAULT]=sld_solv= 1.0e-6 [1/A^(2)]
	double sld_solv;
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

    //  [DEFAULT]=thick_inter1=50.0 [A]
    double thick_inter1;
    //  [DEFAULT]=thick_inter2=50.0 [A]
    double thick_inter2;
    //  [DEFAULT]=thick_inter3=50.0 [A]
    double thick_inter3;
    //  [DEFAULT]=thick_inter4=50.0 [A]
    double thick_inter4;
    //  [DEFAULT]=thick_inter5=50.0 [A]
    double thick_inter5;
    //  [DEFAULT]=thick_inter6=50.0 [A]
    double thick_inter6;
    //  [DEFAULT]=thick_inter7=50.0 [A]
    double thick_inter7;
    //  [DEFAULT]=thick_inter8=50.0 [A]
    double thick_inter8;
    //  [DEFAULT]=thick_inter9=50.0 [A]
    double thick_inter9;
    //  [DEFAULT]=thick_inter10=50.0 [A]
    double thick_inter10;

    //  [DEFAULT]=thick_flat1=100 [A]
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

    //  [DEFAULT]=nu_inter1=2.5
    double nu_inter1;
    //  [DEFAULT]=nu_inter2=2.5
    double nu_inter2;
    //  [DEFAULT]=nu_inter3=2.5
    double nu_inter3;
    //  [DEFAULT]=nu_inter4=2.5
    double nu_inter4;
    //  [DEFAULT]=nu_inter5=2.5
    double nu_inter5;
    //  [DEFAULT]=nu_inter6=2.5
    double nu_inter6;
    //  [DEFAULT]=nu_inter7=2.5
    double nu_inter7;
    //  [DEFAULT]=nu_inter8=2.5
    double nu_inter8;
    //  [DEFAULT]=nu_inter9=2.5
    double nu_inter9;
    //  [DEFAULT]=nu_inter10=2.5
    double nu_inter10;

    //  [DEFAULT]=npts_inter=35.0
    double npts_inter;
    //  [DEFAULT]=nu_inter0=2.5
    double nu_inter0;
    //  [DEFAULT]=rad_core0=50.0 [A]
    double rad_core0;
} SphereSLDParameters;

double sphere_sld_kernel(double dq[], double q);

/// 1D scattering function
double sphere_sld_analytical_1D(SphereSLDParameters *pars, double q);

/// 2D scattering function
double sphere_sld_analytical_2D(SphereSLDParameters *pars, double q, double phi);
double sphere_sld_analytical_2DXY(SphereSLDParameters *pars, double qx, double qy);

#endif

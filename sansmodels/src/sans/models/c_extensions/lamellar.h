#if !defined(lamellar_h)
#define lamellar_h
/** Structure definition for lamellar parameters
 * [PYTHONCLASS] = LamellarModel
 * [DISP_PARAMS] = bi_thick
   [DESCRIPTION] = <text>[Dilute Lamellar Form Factor](from a lyotropic lamellar phase)
		I(q)= 2*pi*P(q)/(delta *q^(2)), where
		P(q)=2*(contrast/q)^(2)*(1-cos(q*delta))^(2))
		bi_thick = bilayer thickness
		sld_bi = SLD of bilayer
		sld_sol = SLD of solvent
		background = Incoherent background
		scale = scale factor

 </text>
[FIXED]= <text>bi_thick.width</text>
 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// delta bilayer thickness [A]
    //  [DEFAULT]=bi_thick=50.0 [A]
    double bi_thick;
    /// SLD of bilayer [1/A^(2)]
    //  [DEFAULT]=sld_bi=1.0e-6 [1/A^(2)]
    double sld_bi;
    /// SLD of solvent [1/A^(2)]
    //  [DEFAULT]=sld_sol=6.3e-6 [1/A^(2)]
    double sld_sol;
	/// Incoherent Background [1/cm] 0.00
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;


} LamellarParameters;

/// kernel
double lamellar_kernel(double dp[], double q);
/// 1D scattering function
double lamellar_analytical_1D(LamellarParameters *pars, double q);

/// 2D scattering function
double lamellar_analytical_2D(LamellarParameters *pars, double q, double phi);
double lamellar_analytical_2DXY(LamellarParameters *pars, double qx, double qy);
double lamellar_analytical_2D_scaled(LamellarParameters *pars, double q, double q_x, double q_y);

#endif

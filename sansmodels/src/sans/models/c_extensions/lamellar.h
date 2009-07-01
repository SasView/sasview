#if !defined(lamellar_h)
#define lamellar_h
/** Structure definition for lamellar parameters
 * [PYTHONCLASS] = LamellarModel
 * [DISP_PARAMS] =  delta
   [DESCRIPTION] = <text> I(q)= 2*pi*P(q)/(delta *q^(2))
						where:
						P(q)=2*(contrast/q)^(2)*(1-cos(q*delta)*e^(1/2*(q*sigma)^(2))
				   </text>
	[FIXED]= delta.width 
	[ORIENTATION_PARAMS]= 
 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// delta bilayer thickness [A]
    //  [DEFAULT]=delta=50.0 [A]
    double delta;
    /// variation in bilayer thickness 
    //  [DEFAULT]=sigma=0.15
    double sigma;
    /// Contrast [1/A²]
    //  [DEFAULT]=contrast=5.3e-6 [1/A²]
    double contrast;
	/// Incoherent Background [1/cm] 0.00
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;
   

} LamellarParameters;



/// 1D scattering function
double lamellar_analytical_1D(LamellarParameters *pars, double q);

/// 2D scattering function
double lamellar_analytical_2D(LamellarParameters *pars, double q, double phi);
double lamellar_analytical_2DXY(LamellarParameters *pars, double qx, double qy);
double lamellar_analytical_2D_scaled(LamellarParameters *pars, double q, double q_x, double q_y);

#endif

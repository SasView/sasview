#if !defined(lamellarFF_HG_h)
#define lamellarFF_HG_h
/** Structure definition for lamellar parameters
 * [PYTHONCLASS] = LamellarFFHGModel
 * [DISP_PARAMS] =  t_length, h_thickness
   [DESCRIPTION] = <text> 
					NOTE: The total bilayer thickness = 2(h_thickness + t_length)
					The meaning of the multiplicative scale factor is not well-defined, but should be on the
					order of the volume fraction of solution occupied by the lamellar crystallites. Please see
					the original references for clarification.
				   </text>
	[FIXED]= t_length.width, h_thickness.width
	[ORIENTATION_PARAMS]= 
 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// tail length [A]
    //  [DEFAULT]=t_length=15.0 [A]
    double t_length;
    /// head thickness 
    //  [DEFAULT]=h_thickness=10.0 [A]
    double h_thickness;
	/// tail scrattering density length[1/A²]
    //  [DEFAULT]=sld_tail=4e-7 [1/A²]
    double sld_tail;
    /// head group scrattering density length[1/A²]
    //  [DEFAULT]=sld_head=3e-6 [1/A²]
    double sld_head;
	 /// solvent scrattering density length[1/A²]
    //  [DEFAULT]=sld_solvent=6e-6 [1/A²]
    double sld_solvent;
	/// Incoherent Background [1/cm] 0.00
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;
   
} LamellarFF_HGParameters;



/// 1D scattering function
double lamellarFF_HG_analytical_1D(LamellarFF_HGParameters *pars, double q);

/// 2D scattering function
double lamellarFF_HG_analytical_2D(LamellarFF_HGParameters *pars, double q, double phi);
double lamellarFF_HG_analytical_2DXY(LamellarFF_HGParameters *pars, double qx, double qy);
double lamellarFF_HG_analytical_2D_scaled(LamellarFF_HGParameters *pars, double q, double q_x, double q_y);

#endif

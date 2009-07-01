/*
	TODO: Add 2D model
*/

#if !defined(lamellarPS_HG_h)
#define lamellarPS_HG_h
/** Structure definition for concentrated lamellar form factor parameters
 * [PYTHONCLASS] = LamellarPSHGModel
 * [DISP_PARAMS] = deltaT,deltaH
   [DESCRIPTION] = <text> Calculates the scattered intensity from a concentrated lamellar phase</text>
   [FIXED]= deltaT.with;deltaH.with
   [ORIENTATION_PARAMS]= 

 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    /// repeat spacing of the lamellar [A]
    //  [DEFAULT]=spacing=40 [A]
    double spacing;
	///  tail thickness [A]
    //  [DEFAULT]=deltaT=10 [A]
    double deltaT;
	///  head thickness [A]
    //  [DEFAULT]=deltaH=2.0 [A]
    double deltaH;
    /// scattering density length of tails [1/A²]
    //  [DEFAULT]=sld_tail=4e-7 [1/A²]
    double sld_tail;
	/// scattering density length of head [1/A²]
    //  [DEFAULT]=sld_head=2e-6 [1/A²]
    double sld_head;
	/// scattering density length of solvent [1/A²]
    //  [DEFAULT]=sld_solvent=6e-6 [1/A²]
    double sld_solvent;
	 /// Number of lamellar plates
    //  [DEFAULT]=n_plates=30
    double n_plates;
    /// caille parameters
    //  [DEFAULT]=caille=0.001
    double caille;
	/// Incoherent Background [1/cm] 
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
   
} LamellarPSHGParameters;



/// 1D scattering function
double lamellarPS_HG_analytical_1D(LamellarPSHGParameters *pars, double q);

/// 2D scattering function
double lamellarPS_HG_analytical_2D(LamellarPSHGParameters *pars, double q, double phi);
double lamellarPS_HG_analytical_2DXY(LamellarPSHGParameters *pars, double qx, double qy);
double lamellarPS_HG_analytical_2D_scaled(LamellarPSHGParameters *pars, double q, double q_x, double q_y);

#endif

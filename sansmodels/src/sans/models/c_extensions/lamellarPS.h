/*
	TODO: Add 2D model
*/

#if !defined(lamellarPS_h)
#define lamellarPS_h
/** Structure definition for concentrated lamellar form factor parameters
 * [PYTHONCLASS] = LamellarPSModel
 * [DISP_PARAMS] = delta
   [DESCRIPTION] = <text> Calculates the scattered intensity from a lyotropic lamellar phase</text>
   [FIXED]= delta.with
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
double lamellarPS_analytical_2D_scaled(LamellarPSParameters *pars, double q, double q_x, double q_y);

#endif

#if !defined(micelleSphCore_h)
#define micelleSphCore_h
#include "parameters.hh"

/**
[PYTHONCLASS] = MicelleSphCoreModel
[DISP_PARAMS] = radius_core, radius_gyr
[DESCRIPTION] = <text>
                Model parameters:   
                ndensity : number density of micelles
                v_core: volume block in core
                v_corona: volume block in corona
                rho_solv: sld of solvent 
                rho_core: sld of core
                rho_corona: sld of corona
                radius_core: radius of core
                radius_gyr: radius of gyration of chains in corona 
                d_penetration: close to unity, mimics non-penetration of gaussian chains
                n_aggreg: aggregation number of the micelle
                background: incoherent background
                scale : scale factor
		</text>
[FIXED]= <text> radius_core.width; radius_gyr.width </text>
[ORIENTATION_PARAMS]= <text> </text>
**/

class MicelleSphCoreModel{
public:

    // Model parameters
  
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    Parameter scale;

    /// Number density of micelles [1/cm^(3)]
    //  [DEFAULT]=ndensity= 8.94e15 [1/cm^(3)]
    Parameter ndensity;

    /// Core volume [A]
    //  [DEFAULT]=v_core= 62624. [A^3]
    Parameter v_core;

    /// Corona volume [A^(3)]
    //  [DEFAULT]=v_corona= 61940. [A^(3)]
    Parameter v_corona;

    /// solvent scattering length density [1/A^(2)]
    //  [DEFAULT]=rho_solv= 6.4e-6 [1/A^(2)]
    Parameter rho_solv;

    /// core scattering length density [1/A^(2)]
    //  [DEFAULT]=rho_core= 3.4e-7 [1/A^(2)]
    Parameter rho_core;

    /// corona scattering length density [1/A^(2)]
    //  [DEFAULT]=rho_corona= 8.0e-7 [1/A^(2)]
    Parameter rho_corona;

    /// core radius [A]
    //  [DEFAULT]=radius_core= 45.0 [A]
    Parameter radius_core;

    /// radius of gyration of chains in corona[A]
    //  [DEFAULT]=radius_gyr= 20.0 [A]
    Parameter radius_gyr;

    /// d factor to mimic non-penetration of Gaussian chains, close to unity 
    //  [DEFAULT]=d_penetration= 1.0 
    Parameter d_penetration;

    /// aggregation number of the micelle 
    //  [DEFAULT]=n_aggreg= 6.0 
    Parameter n_aggreg;

    /// Incoherent Background [1/cm]
    //  [DEFAULT]=background=0 [1/cm]
    Parameter background;

    //Constructor
    MicelleSphCoreModel();
    
    // Operators to get I(Q)
    double operator()(double q);
    double operator()(double qx, double qy);
    double calculate_ER();
    double calculate_VR();
    double evaluate_rphi(double q, double phi);
};
#endif

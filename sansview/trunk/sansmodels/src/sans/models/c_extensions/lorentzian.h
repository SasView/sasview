#if !defined(lorentzian_h)
#define lorentzian_h

/** Structure definition for Lorentzian parameters.
 * The Lorentzian is normalized to the 'scale' parameter.
 *  
 * f(x)=scale * 1/pi 0.5gamma / [ (x-x_0)^2 + (0.5gamma)^2 ]
 * 
 * [PYTHONCLASS] = Lorentzian
 */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Width
    //  [DEFAULT]=gamma=1.0
    double gamma;
    /// Center of the Lorentzian distribution
    //  [DEFAULT]=center=0.0 
    double center;
} LorentzianParameters;

/// 1D lorentzian function
double lorentzian_analytical_1D(LorentzianParameters *pars, double x);

/// 2D lorentzian function
double lorentzian_analytical_2D(LorentzianParameters *pars, double x, double phi);
double lorentzian_analytical_2DXY(LorentzianParameters *pars, double x, double y);

#endif

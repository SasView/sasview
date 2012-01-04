#if !defined(logNormal_h)
#define logNormal_h

/** Structure definition for Gaussian parameters.
 * The Log normal is normalized to the 'scale' parameter.
 *  
 * f(x)=scale * 1/(sigma*math.sqrt(2pi))e^(-1/2*((math.log(x)-mu)/sigma)^2)
 *
 * [PYTHONCLASS] = LogNormal
 * [DESCRIPTION] = <text>f(x)=scale * 1/(sigma*math.sqrt(2pi))e^(-1/2*((math.log(x)-mu)/sigma)^2)</text>
 */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Standard deviation
    //  [DEFAULT]=sigma=1 
    double sigma;
    /// Center of the Log Normal distribution
    //  [DEFAULT]=center=0.0 
    double center;
} LogNormalParameters;

/// 1D scattering function
double logNormal_analytical_1D(LogNormalParameters *pars, double x);

/// 2D scattering function
double logNormal_analytical_2D(LogNormalParameters *pars, double x, double phi);
double logNormal_analytical_2DXY(LogNormalParameters *pars, double x, double y);

#endif

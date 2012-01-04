#if !defined(gaussian_h)
#define gaussian_h

/** Structure definition for Gaussian parameters.
 * The Gaussian is normalized to the 'scale' parameter.
 *  
 * f(x)=scale * 1/(sigma^2*2pi)e^(-(x-mu)^2/2sigma^2)
 * 
 * [PYTHONCLASS] = Gaussian
 * [DESCRIPTION] = <text>f(x)=scale * 1/(sigma^2*2pi)e^(-(x-mu)^2/2sigma^2)</text>
 */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Standard deviation
    //  [DEFAULT]=sigma=1 
    double sigma;
    /// Center of the Gaussian distribution
    //  [DEFAULT]=center=0.0 
    double center;
} GaussianParameters;

/// 1D scattering function
double gaussian_analytical_1D(GaussianParameters *pars, double x);

/// 2D scattering function
double gaussian_analytical_2D(GaussianParameters *pars, double x, double phi);
double gaussian_analytical_2DXY(GaussianParameters *pars, double x, double y);

#endif

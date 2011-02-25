#if !defined(schulz_h)
#define schulz_h

/** Structure definition for Schulz parameters.
 * The Schulz is normalized to the 'scale' parameter.
 *  
 * f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 *					math.exp(-R*(z+1))/(center*gamma(z+1)
 *		z= math.pow[(1/(sigma/center),2]-1
 *		R= x/center
 * 
 * [PYTHONCLASS] = Schulz
 * [DESCRIPTION] = <text> f(x)=scale * math.pow(z+1, z+1)*math.pow((R), z)*
 					math.exp(-R*(z+1))/(center*gamma(z+1)
 		            z= math.pow[(1/(sigma/center),2]-1
 					R= x/center</text>
 */
typedef struct {
    /// Scale factor 
    //  [DEFAULT]=scale=1.0
    double scale;
    /// Standard deviation
    //  [DEFAULT]=sigma=1 
    double sigma;
    /// Center of the Schulz distribution
    //  [DEFAULT]=center=0.0 
    double center;
} SchulzParameters;

/// 1D scattering function
double schulz_analytical_1D(SchulzParameters *pars, double x);

/// 2D scattering function
double schulz_analytical_2D(SchulzParameters *pars, double x, double phi);
double schulz_analytical_2DXY(SchulzParameters *pars, double x, double y);

#endif

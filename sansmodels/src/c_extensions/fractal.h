#if !defined(fractal_h)
#define fractal_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = FractalModel
 //[DISP_PARAMS] = radius
 //[DESCRIPTION] =<text> The scattering intensity  I(x) = P(|x|)*S(|x|) + background, where
 //       p(x)= scale * V * delta^(2)* F(x*radius)^(2)
 //       F(x) = 3*[sin(x)-x cos(x)]/x**3
 //       where delta = sldBlock -sldSolv.
 //       scale        =  scale factor * Volume fraction
 //       radius       =  Block radius
 //       fractal_dim  =  Fractal dimension
 //       cor_length  =  Correlation Length
 //       sldBlock    =  SDL block
 //       sldSolv  =  SDL solvent
 //       background   =  background
 //		</text>
 //[FIXED]= <text> radius.width </text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 0.05
    double scale;

    ///	Radius of gyration [A]
    //  [DEFAULT]=radius=5.0 [A]
    double radius;

    ///	Fractal dimension
    //  [DEFAULT]=fractal_dim=2.0
    double fractal_dim;

    ///	Correlation Length [A]
    //  [DEFAULT]=cor_length=100.0 [A]
    double cor_length;

    ///	SDL block [1/A^(2)]
    //  [DEFAULT]=sldBlock=2.0e-6 [1/A^(2)]
    double sldBlock;

    ///	SDL solvent [1/A^(2)]
    //  [DEFAULT]=sldSolv= 6.35e-6 [1/A^(2)]
    double sldSolv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;
} FractalParameters;



/// 1D scattering function
//double fractal_analytical_1D(FractalParameters *pars, double q);

/// 2D scattering function
//double fractal_analytical_2D(FractalParameters *pars, double q, double phi);
//double fractal_analytical_2DXY(FractalParameters *pars, double qx, double qy);

#endif

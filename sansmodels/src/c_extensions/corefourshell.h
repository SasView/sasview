#if !defined(corefourshell_h)
#define corefourshell_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = CoreFourShellModel
 //[DISP_PARAMS] = rad_core0, thick_shell1,thick_shell2,thick_shell3,thick_shell4
 //[DESCRIPTION] =<text> Calculates the scattering intensity from a core-4 shell structure.
 // 			scale = scale factor * volume fraction
 //				rad_core0: the radius of the core
 //				sld_core0: the SLD of the core
 //				thick_shelli: the thickness of the i'th shell from the core
 //				sld_shelli: the SLD of the i'th shell from the core
 //				sld_solv: the SLD of the solvent
 //				background: incoherent background
 //		</text>
 //[FIXED]=<text>  thick_shell4.width; thick_shell1.width;thick_shell2.width;thick_shell3.width;rad_core0.width </text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Radius of the core0 [A]
    //  [DEFAULT]=rad_core0=60. [A]
    double rad_core0;

    ///	sld of core0 [1/A^(2)]
    //  [DEFAULT]=sld_core0= 6.4e-6 [1/A^(2)]
    double sld_core0;

    ///	thickness of the shell1 [A]
     //  [DEFAULT]=thick_shell1=10.0 [A]
    double thick_shell1;

     ///	sld of shell1 [1/A^(2)]
     //  [DEFAULT]=sld_shell1= 1.0e-6 [1/A^(2)]
     double sld_shell1;

     ///	thickness of the shell2 [A]
      //  [DEFAULT]=thick_shell2=10.0 [A]
     double thick_shell2;

      ///	sld of shell2 [1/A^(2)]
      //  [DEFAULT]=sld_shell2= 2.0e-6 [1/A^(2)]
      double sld_shell2;

      ///	thickness of the shell3 [A]
       //  [DEFAULT]=thick_shell3=10.0 [A]
      double thick_shell3;

       ///	sld of shell3 [1/A^(2)]
       //  [DEFAULT]=sld_shell3= 3.0e-6 [1/A^(2)]
       double sld_shell3;

       ///	thickness of the shell4 [A]
        //  [DEFAULT]=thick_shell4=10.0 [A]
       double thick_shell4;

        ///	sld of shell4 [1/A^(2)]
        //  [DEFAULT]=sld_shell4= 4.0e-6 [1/A^(2)]
        double sld_shell4;

    ///	sld_solv[1/A^(2)]
    //  [DEFAULT]=sld_solv= 6.4e-6 [1/A^(2)]
    double sld_solv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.001 [1/cm]
	double background;
} CoreFourShellParameters;



/// 1D scattering function
//double corefourshell_analytical_1D(CoreFourShellParameters *pars, double q);

/// 2D scattering function
//double corefourshell_analytical_2D(CoreFourShellParameters *pars, double q, double phi);
//double corefourshell_analytical_2DXY(CoreFourShellParameters *pars, double qx, double qy);

#endif

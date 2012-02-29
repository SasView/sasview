#if !defined(o_h)
#define onion_h
#include "parameters.hh"

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = OnionModel
 //[DISP_PARAMS] = rad_core0, thick_shell1,thick_shell2,thick_shell3,thick_shell4, thick_shell5,thick_shell6,thick_shell7,thick_shell8,thick_shell9,thick_shell10
 //[DESCRIPTION] =<text>Form factor of mutishells normalized by the volume. Here each shell is described
 //						 by an exponential function;
 //							I)
 //							For A_shell != 0,
 //							f(r) = B*exp(A_shell*(r-r_in)/thick_shell)+C
 //                         where
 //								B=(sld_out-sld_in)/(exp(A_shell)-1)
 //								C=sld_in-B.
 //							Note that in the above case,
 //								the function becomes a linear function
 //								as A_shell --> 0+ or 0-.
 //							II)
 //							For the exact point of A_shell == 0,
 //							f(r) = sld_in ,i.e., it crosses over flat function
 //							Note that the 'sld_out' becaomes NULL in this case.
 //
 //				background:background,
 //				rad_core0: radius of sphere(core)
 //				thick_shell#:the thickness of the shell#
 //				sld_core0: the SLD of the sphere
 //				sld_solv: the SLD of the solvent
 //				sld_shell: the SLD of the shell#
 //				A_shell#: the coefficient in the exponential function
 //		</text>
 //[FIXED]=  <text>rad_core0.width;thick_shell1.width;thick_shell2.width;thick_shell3.width;thick_shell4.width;thick_shell5.width;thick_shell6.width;thick_shell7.width;thick_shell8.width;thick_shell9.width;thick_shell10.width</text>
 //[ORIENTATION_PARAMS]= <text> </text>

class OnionModel{
public:
    // Model parameters
    /// number of shells
    //  [DEFAULT]=n_shells=1
    Parameter n_shells;
      /// Scale factor
      //  [DEFAULT]=scale= 1.0
    Parameter scale;
      /// Radius of sphere [A]
      //  [DEFAULT]=rad_core0=200.0 [A]
    Parameter rad_core0;
    /// sld_core [1/A^(2)]
    //  [DEFAULT]=sld_core0= 1.0e-6 [1/A^(2)]
    Parameter sld_core0;
    /// sld_solv [1/A^(2)]
    //  [DEFAULT]=sld_solv= 6.4e-6 [1/A^(2)]
    Parameter sld_solv;
    /// Incoherent Background [1/cm]
    //  [DEFAULT]=background=0 [1/cm]
    Parameter background;

    //  [DEFAULT]=sld_out_shell1=2.0e-06 [1/A^(2)]
    Parameter sld_out_shell1;
    //  [DEFAULT]=sld_out_shell2=2.5e-06 [1/A^(2)]
    Parameter sld_out_shell2;
    //  [DEFAULT]=sld_out_shell3=3.0e-06 [1/A^(2)]
    Parameter sld_out_shell3;
    //  [DEFAULT]=sld_out_shell4=3.5e-06 [1/A^(2)]
    Parameter sld_out_shell4;
    //  [DEFAULT]=sld_out_shell5=4.0e-06 [1/A^(2)]
    Parameter sld_out_shell5;
    //  [DEFAULT]=sld_out_shell6=4.5e-06 [1/A^(2)]
    Parameter sld_out_shell6;
    //  [DEFAULT]=sld_out_shell7=5.0e-06 [1/A^(2)]
    Parameter sld_out_shell7;
    //  [DEFAULT]=sld_out_shell8=5.5e-06 [1/A^(2)]
    Parameter sld_out_shell8;
    //  [DEFAULT]=sld_out_shell9=6.0e-06 [1/A^(2)]
    Parameter sld_out_shell9;
    //  [DEFAULT]=sld_out_shell10=6.2e-06 [1/A^(2)]
    Parameter sld_out_shell10;

    //  [DEFAULT]=sld_in_shell1=1.7e-06 [1/A^(2)]
    Parameter sld_in_shell1;
    //  [DEFAULT]=sld_in_shell2=2.2e-06 [1/A^(2)]
    Parameter sld_in_shell2;
    //  [DEFAULT]=sld_in_shell3=2.7e-06 [1/A^(2)]
    Parameter sld_in_shell3;
    //  [DEFAULT]=sld_in_shell4=3.2e-06 [1/A^(2)]
    Parameter sld_in_shell4;
    //  [DEFAULT]=sld_in_shell5=3.7e-06 [1/A^(2)]
    Parameter sld_in_shell5;
    //  [DEFAULT]=sld_in_shell6=4.2e-06 [1/A^(2)]
    Parameter sld_in_shell6;
    //  [DEFAULT]=sld_in_shell7=4.7e-06 [1/A^(2)]
    Parameter sld_in_shell7;
    //  [DEFAULT]=sld_in_shell8=5.2e-06 [1/A^(2)]
    Parameter sld_in_shell8;
    //  [DEFAULT]=sld_in_shell9=5.7e-06 [1/A^(2)]
    Parameter sld_in_shell9;
    //  [DEFAULT]=sld_in_shell10=6.0e-06 [1/A^(2)]
    Parameter sld_in_shell10;

    //  [DEFAULT]=A_shell1=1.0
    Parameter A_shell1;
    //  [DEFAULT]=A_shell2=1.0
    Parameter A_shell2;
    //  [DEFAULT]=A_shell3=1.0
    Parameter A_shell3;
    //  [DEFAULT]=A_shell4=1.0
    Parameter A_shell4;
    //  [DEFAULT]=A_shell5=1.0
    Parameter A_shell5;
    //  [DEFAULT]=A_shell6=1.0
    Parameter A_shell6;
    //  [DEFAULT]=A_shell7=1.0
    Parameter A_shell7;
    //  [DEFAULT]=A_shell8=1.0
    Parameter A_shell8;
    //  [DEFAULT]=A_shell9=1.0
    Parameter A_shell9;
    //  [DEFAULT]=A_shell10=1.0
    Parameter A_shell10;

    //  [DEFAULT]=thick_shell1=50.0 [A]
    Parameter thick_shell1;
    //  [DEFAULT]=thick_shell2=50.0 [A]
    Parameter thick_shell2;
    //  [DEFAULT]=thick_shell3=50.0 [A]
    Parameter thick_shell3;
    //  [DEFAULT]=thick_shell4=50.0 [A]
    Parameter thick_shell4;
    //  [DEFAULT]=thick_shell5=50.0 [A]
    Parameter thick_shell5;
    //  [DEFAULT]=thick_shell6=50.0 [A]
    Parameter thick_shell6;
    //  [DEFAULT]=thick_shell7=50.0 [A]
    Parameter thick_shell7;
    //  [DEFAULT]=thick_shell8=50.0 [A]
    Parameter thick_shell8;
    //  [DEFAULT]=thick_shell9=50.0 [A]
    Parameter thick_shell9;
    //  [DEFAULT]=thick_shell10=50.0 [A]
    Parameter thick_shell10;

    //  [DEFAULT]=func_shell1=2
    Parameter func_shell1;
    //  [DEFAULT]=func_shell2=2
    Parameter func_shell2;
    //  [DEFAULT]=func_shell3=2
    Parameter func_shell3;
    //  [DEFAULT]=func_shell4=2
    Parameter func_shell4;
    //  [DEFAULT]=func_shell5=2
    Parameter func_shell5;
    //  [DEFAULT]=func_shell6=2
    Parameter func_shell6;
    //  [DEFAULT]=func_shell7=2
    Parameter func_shell7;
    //  [DEFAULT]=func_shell8=2
    Parameter func_shell8;
    //  [DEFAULT]=func_shell9=2
    Parameter func_shell9;
    //  [DEFAULT]=func_shell10=2
    Parameter func_shell10;

  // Constructor
  OnionModel();

  // Operators to get I(Q)
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};

#endif

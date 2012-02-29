#if !defined(sld_cal_h)
#define sld_cal_h
#include "parameters.hh"

/**
 * To calculate the sld value
* [PYTHONCLASS] = SLDCalFunc
* [DISP_PARAMS] = npts_inter
  [DESCRIPTION] =<text>To calculate sld values
 				</text>
	[FIXED]= <text>
			</text>

 **/

class SLDCalFunc{
public:
  // Model parameters
  /// fun_type
  //  [DEFAULT]=fun_type=0
  Parameter fun_type;

  /// npts_inter
  //  [DEFAULT]=npts_inter= 21
  Parameter npts_inter;

  /// shell_num
  //  [DEFAULT]=shell_num= 0
  Parameter shell_num;

  /// nu_inter
  //  [DEFAULT]=nu_inter= 2.5
  Parameter nu_inter;

  /// sld_left [1/A^(2)]
  //  [DEFAULT]=sld_left= 0 [1/A^(2)]
  Parameter sld_left;

  /// sld_right [1/A^(2)]
  //  [DEFAULT]=sld_right= 0 [1/A^(2)]
  Parameter sld_right;

  // Constructor
  SLDCalFunc();

  // Operators to get SLD
  double operator()(double q);
  double operator()(double qx, double qy);
  double calculate_ER();
  double calculate_VR();
  double evaluate_rphi(double q, double phi);
};



#endif

#if !defined(sld_cal_h)
#define sld_cal_h

/**
 * To calculate the sld value
* [PYTHONCLASS] = SLDCalFunc
* [DISP_PARAMS] = npts_inter
  [DESCRIPTION] =<text>To calculate sld values
 				</text>
	[FIXED]= <text>
			</text>

 **/
typedef struct {
    ///	fun_type
    //  [DEFAULT]=fun_type=0
    double fun_type;

    /// npts_inter
    //  [DEFAULT]=npts_inter= 21
    double npts_inter;

    /// shell_num
    //  [DEFAULT]=shell_num= 0
    double shell_num;

    /// nu_inter
    //  [DEFAULT]=nu_inter= 2.5
    double nu_inter;

    /// sld_left [1/A^(2)]
    //  [DEFAULT]=sld_left= 0 [1/A^(2)]
    double sld_left;

    /// sld_right [1/A^(2)]
    //  [DEFAULT]=sld_right= 0 [1/A^(2)]
    double sld_right;

} SLDCalParameters;



/// 1D function
double sld_cal_analytical_1D(SLDCalParameters *pars, double q);

/// 2D function
double sld_cal_analytical_2D(SLDCalParameters *pars, double q, double phi);
double sld_cal_analytical_2DXY(SLDCalParameters *pars, double qx, double qy);

#endif

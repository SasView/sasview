/**
 * SLD Calculator
 * @author: Jae Hie Cho / UTK
 */

#include "sld_cal.h"
#include "libmultifunc/librefl.h"
#include <math.h>


/**
 * Function to calculate sld
 * @param pars: parameters
 * @param x: independent param-value
 * @return: sld value
 */
double sld_cal_analytical_1D(SLDCalParameters *pars, double x) {
	double fun, nsl, n_s, fun_coef, sld_l, sld_r, sld_out;

	fun = pars->fun_type;
	nsl = pars->npts_inter;
	n_s = pars->shell_num;
	fun_coef = pars->nu_inter;
	sld_l = pars-> sld_left;
	sld_r = pars-> sld_right;

	int fun_type = floor(fun);

	sld_out = intersldfunc(fun_type, nsl, n_s, fun_coef, sld_l, sld_r);

	return sld_out;
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters
 * @param q: q-value
 * @return: function value
 */
double sld_cal_analytical_2D(SLDCalParameters *pars, double x, double phi) {
	return sld_cal_analytical_1D(pars,x);
}

double sld_cal_analytical_2DXY(SLDCalParameters *pars, double xx, double xy){
	return sld_cal_analytical_1D(pars,sqrt(xx*xx+xy*xy));
}

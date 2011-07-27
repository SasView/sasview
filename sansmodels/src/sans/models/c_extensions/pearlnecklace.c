/**
 * pearl necklace model
 */
#include <math.h>
#include "pearlnecklace.h"
#include "libmultifunc/libfunc.h"
#include <stdio.h>
#include <stdlib.h>


double pearl_necklace_kernel(double dp[], double q) {
	// fit parameters
	double scale = dp[0];
	double radius = dp[1];
	double edge_separation = dp[2];
	double thick_string = dp[3];
	double num_pearls = dp[4];
	double sld_pearl = dp[5];
	double sld_string = dp[6];
	double sld_solv = dp[7];
	double background = dp[8];

	//relative slds
	double contrast_pearl = sld_pearl - sld_solv;
	double contrast_string = sld_string - sld_solv;

	// number of string segments
	double num_strings = num_pearls - 1.0;

	//Pi
	double pi = 4.0*atan(1.0);

	// each volumes
	double string_vol = edge_separation * pi * pow((thick_string / 2.0), 2);
	double pearl_vol = 4.0 /3.0 * pi * pow(radius, 3);

	//total volume
	double tot_vol;
	tot_vol = num_strings * string_vol;
	tot_vol += num_pearls * pearl_vol;

	//each masses
	double m_r= contrast_string * string_vol;
	double m_s= contrast_pearl * pearl_vol;

	//sine functions of a pearl
	double psi;
	psi = sin(q*radius);
	psi -= q * radius * cos(q * radius);
	psi /= pow((q * radius), 3);
	psi *= 3.0;

	// Note take only 20 terms in Si series: 10 terms may be enough though.
	double gamma;
	gamma = Si(q* edge_separation);
	gamma /= (q* edge_separation);
	double beta;
	beta = Si(q * (edge_separation + radius));
	beta -= Si(q * radius);
	beta /= (q* edge_separation);

	//form factors
	double sss; //pearls
	double srr; //strings
	double srs; //cross
	// center to center distance between the neighboring pearls
	double A_s = edge_separation + 2.0 * radius;

	// form factor for num_pearls
	sss = 1.0 - pow(sinc(q*A_s), num_pearls );
	sss /= pow((1.0-sinc(q*A_s)), 2);
	sss *= -sinc(q*A_s);
	sss -= num_pearls/2.0;
	sss += num_pearls/(1.0-sinc(q*A_s));
	sss *= 2.0 * pow((m_s*psi), 2);

	// form factor for num_strings (like thin rods)
	double srr_1;
	srr_1 = -pow(sinc(q*edge_separation/2.0), 2);

	srr_1 += 2.0 * gamma;
	srr_1 *= num_strings;
	double srr_2;
	srr_2 = 2.0/(1.0-sinc(q*A_s));
	srr_2 *= num_strings;
	srr_2 *= pow(beta, 2);
	double srr_3;
	srr_3 = 1.0 - pow(sinc(q*A_s), num_strings);
	srr_3 /= pow((1.0-sinc(q*A_s)), 2);
	srr_3 *= pow(beta, 2);
	srr_3 *= -2.0;

	// total srr
	srr = srr_1 + srr_2 + srr_3;
	srr *= pow(m_r, 2);

	// form factor for correlations
	srs = 1.0;
	srs -= pow(sinc(q*A_s), num_strings);
	srs /= pow((1.0-sinc(q*A_s)), 2);
	srs *= -sinc(q*A_s);
	srs += (num_strings/(1.0-sinc(q*A_s)));
	srs *= 4.0;
	srs *= (m_r * m_s * beta * psi);

	double form_factor;
	form_factor = sss + srr + srs;
	form_factor /= (tot_vol * 1.0e-8); // norm by volume and A^-1 to cm^-1

	// scale and background
	form_factor *= scale;
	form_factor += background;
    return (form_factor);
}

/**
 * Function to evaluate pearlnecklace function
 * @param pars: parameters of pearlnecklace
 * @param q: q-value
 * @return: function value
 */

double pearl_necklace_analytical_1D(PeralNecklaceParameters *pars, double q) {
	double dp[9];

	dp[0] = pars->scale;
	dp[1] = pars->radius;
	dp[2] = pars->edge_separation;
	dp[3] = pars->thick_string;
	dp[4] = pars->num_pearls;
	dp[5] = pars->sld_pearl;
	dp[6] = pars->sld_string;
	dp[7] = pars->sld_solv;
	dp[8] = pars->background;

	return pearl_necklace_kernel(dp, q);
}

/**
 * Function to evaluate pearl_necklace function
 * @param pars: parameters of PeralNecklace
 * @param q: q-value
 * @return: function value
 */
double pearl_necklace_analytical_2D(PeralNecklaceParameters *pars, double q, double phi) {
	return pearl_necklace_analytical_1D(pars,q);
}

double pearl_necklace_analytical_2DXY(PeralNecklaceParameters *pars, double qx, double qy){
	return pearl_necklace_analytical_1D(pars,sqrt(qx*qx+qy*qy));
}


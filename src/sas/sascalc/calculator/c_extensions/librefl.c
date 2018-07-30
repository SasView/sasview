// The original code, of which work was not DANSE funded,
// was provided by J. Cho.
// And modified to fit sansmodels/sansview: JC

#include <math.h>
#include "librefl.h"
#include <stdio.h>
#include <stdlib.h>
#if defined(_MSC_VER)
#define NEED_ERF
#endif



#if defined(NEED_ERF)
/* erf.c  - public domain implementation of error function erf(3m)

reference - Haruhiko Okumura: C-gengo niyoru saishin algorithm jiten
            (New Algorithm handbook in C language) (Gijyutsu hyouron
            sha, Tokyo, 1991) p.227 [in Japanese]                 */


#ifdef _WIN32
# include <float.h>
# if !defined __MINGW32__ || defined __NO_ISOCEXT
#  ifndef isnan
#   define isnan(x) _isnan(x)
#  endif
#  ifndef isinf
#   define isinf(x) (!_finite(x) && !_isnan(x))
#  endif
#  ifndef finite
#   define finite(x) _finite(x)
#  endif
# endif
#endif

static double q_gamma(double, double, double);

/* Incomplete gamma function
   1 / Gamma(a) * Int_0^x exp(-t) t^(a-1) dt  */
static double p_gamma(double a, double x, double loggamma_a)
{
    int k;
    double result, term, previous;

    if (x >= 1 + a) return 1 - q_gamma(a, x, loggamma_a);
    if (x == 0)     return 0;
    result = term = exp(a * log(x) - x - loggamma_a) / a;
    for (k = 1; k < 1000; k++) {
        term *= x / (a + k);
        previous = result;  result += term;
        if (result == previous) return result;
    }
    fprintf(stderr, "erf.c:%d:p_gamma() could not converge.", __LINE__);
    return result;
}

/* Incomplete gamma function
   1 / Gamma(a) * Int_x^inf exp(-t) t^(a-1) dt  */
static double q_gamma(double a, double x, double loggamma_a)
{
    int k;
    double result, w, temp, previous;
    double la = 1, lb = 1 + x - a;  /* Laguerre polynomial */

    if (x < 1 + a) return 1 - p_gamma(a, x, loggamma_a);
    w = exp(a * log(x) - x - loggamma_a);
    result = w / lb;
    for (k = 2; k < 1000; k++) {
        temp = ((k - 1 - a) * (lb - la) + (k + x) * lb) / k;
        la = lb;  lb = temp;
        w *= (k - 1 - a) / k;
        temp = w / (la * lb);
        previous = result;  result += temp;
        if (result == previous) return result;
    }
    fprintf(stderr, "erf.c:%d:q_gamma() could not converge.", __LINE__);
    return result;
}

#define LOG_PI_OVER_2 0.572364942924700087071713675675 /* log_e(PI)/2 */

double erf(double x)
{
    if (!finite(x)) {
        if (isnan(x)) return x;      /* erf(NaN)   = NaN   */
        return (x>0 ? 1.0 : -1.0);   /* erf(+-inf) = +-1.0 */
    }
    if (x >= 0) return   p_gamma(0.5, x * x, LOG_PI_OVER_2);
    else        return - p_gamma(0.5, x * x, LOG_PI_OVER_2);
}

double erfc(double x)
{
    if (!finite(x)) {
        if (isnan(x)) return x;      /* erfc(NaN)   = NaN      */
        return (x>0 ? 0.0 : 2.0);    /* erfc(+-inf) = 0.0, 2.0 */
    }
    if (x >= 0) return  q_gamma(0.5, x * x, LOG_PI_OVER_2);
    else        return  1 + p_gamma(0.5, x * x, LOG_PI_OVER_2);
}
#endif // NEED_ERF

void cassign(Cplx *x, double real, double imag)
{
	x->re = real;
	x->im = imag;
}


void cplx_add(Cplx *z, Cplx x, Cplx y)
{
	z->re = x.re + y.re;
	z->im = x.im + y.im;
}

void rcmult(Cplx *z, double x, Cplx y)
{
	z->re = x*y.re;
	z->im = x*y.im;
}

void cplx_sub(Cplx *z, Cplx x, Cplx y)
{
	z->re = x.re - y.re;
	z->im = x.im - y.im;
}


void cplx_mult(Cplx *z, Cplx x, Cplx y)
{
	z->re = x.re*y.re - x.im*y.im;
	z->im = x.re*y.im + x.im*y.re;
}

void cplx_div(Cplx *z, Cplx x, Cplx y)
{
	z->re = (x.re*y.re + x.im*y.im)/(y.re*y.re + y.im*y.im);
	z->im = (x.im*y.re - x.re*y.im)/(y.re*y.re + y.im*y.im);
}

void cplx_exp(Cplx *z, Cplx b)
{
	double br,bi;
	br=b.re;
	bi=b.im;
	z->re = exp(br)*cos(bi);
	z->im = exp(br)*sin(bi);
}


void cplx_sqrt(Cplx *c, Cplx z)    //see Schaum`s Math Handbook p. 22, 6.6 and 6.10
{
	double zr,zi,x,y,r,w;

	zr=z.re;
	zi=z.im;

	if (zr==0.0 && zi==0.0)
	{
		c->re=0.0;
		c->im=0.0;
	} else {
		x=fabs(zr);
		y=fabs(zi);
		if (x>y)
		{
			r=y/x;
			w=sqrt(x)*sqrt(0.5*(1.0+sqrt(1.0+r*r)));
		} else {
			r=x/y;
			w=sqrt(y)*sqrt(0.5*(r+sqrt(1.0+r*r)));
		}
		if (zr >=0.0)
		{
			c->re=w;
			c->im=zi/(2.0*w);
		} else {
			c->im=(zi >= 0) ? w : -w;
			c->re=zi/(2.0*c->im);
		}
	}
}

void cplx_cos(Cplx *z, Cplx b)
{
	// cos(b) = (e^bi + e^-bi)/2
	//        = (e^b.im e^-i bi.re) + e^-b.im e^i b.re)/2
	//        = (e^b.im cos(-b.re) + e^b.im sin(-b.re) i)/2 + (e^-b.im cos(b.re) + e^-b.im sin(b.re) i)/2
	//        = e^b.im cos(b.re)/2 - e^b.im sin(b.re)/2 i + 1/e^b.im cos(b.re)/2 + 1/e^b.im sin(b.re)/2 i
	//        = (e^b.im + 1/e^b.im)/2 cos(b.re) + (-e^b.im + 1/e^b.im)/2 sin(b.re) i
	//        = cosh(b.im) cos(b.re) - sinh(b.im) sin(b.re) i
	double exp_b_im = exp(b.im);
	z->re = 0.5*(+exp_b_im + 1.0/exp_b_im) * cos(b.re);
	z->im = -0.5*(exp_b_im - 1.0/exp_b_im) * sin(b.re);
}

// normalized and modified erf
//   |
// 1 +                __  - - - -
//   |             _
//	 |            _
//   |        __
// 0 + - - -
//   |-------------+------------+--
//   0           center       n_sub    --->
//                                     ind
//
// n_sub = total no. of bins(or sublayers)
// ind = x position: 0 to max
// nu = max x to integration
double err_mod_func(double n_sub, double ind, double nu)
{
  double center, func;
  if (nu == 0.0)
		nu = 1e-14;
	if (n_sub == 0.0)
		n_sub = 1.0;


	//ind = (n_sub-1.0)/2.0-1.0 +ind;
	center = n_sub/2.0;
	// transform it so that min(ind) = 0
	ind -= center;
	// normalize by max limit
	ind /= center;
	// divide by sqrt(2) to get Gaussian func
	nu /= sqrt(2.0);
	ind *= nu;
	// re-scale and normalize it so that max(erf)=1, min(erf)=0
	func = erf(ind)/erf(nu)/2.0;
	// shift it by +0.5 in y-direction so that min(erf) = 0
	func += 0.5;

	return func;
}
double linearfunc(double n_sub, double ind, double nu)
{
  double bin_size, func;
	if (n_sub == 0.0)
		n_sub = 1.0;

	bin_size = 1.0/n_sub;  //size of each sub-layer
	// rescale
	ind *= bin_size;
	func = ind;

	return func;
}
// use the right hand side from the center of power func
double power_r(double n_sub, double ind, double nu)
{
  double bin_size,func;
	if (nu == 0.0)
		nu = 1e-14;
	if (n_sub == 0.0)
		n_sub = 1.0;

	bin_size = 1.0/n_sub;  //size of each sub-layer
	// rescale
	ind *= bin_size;
	func = pow(ind, nu);

	return func;
}
// use the left hand side from the center of power func
double power_l(double n_sub, double ind, double nu)
{
  double bin_size, func;
	if (nu == 0.0)
		nu = 1e-14;
	if (n_sub == 0.0)
		n_sub = 1.0;

	bin_size = 1.0/n_sub;  //size of each sub-layer
	// rescale
	ind *= bin_size;
	func = 1.0-pow((1.0-ind),nu);

	return func;
}
// use 1-exp func from x=0 to x=1
double exp_r(double n_sub, double ind, double nu)
{
  double bin_size, func;
	if (nu == 0.0)
		nu = 1e-14;
	if (n_sub == 0.0)
		n_sub = 1.0;

	bin_size = 1.0/n_sub;  //size of each sub-layer
	// rescale
	ind *= bin_size;
	// modify func so that func(0) =0 and func(max)=1
	func = 1.0-exp(-nu*ind);
	// normalize by its max
	func /= (1.0-exp(-nu));

	return func;
}

// use the left hand side mirror image of exp func
double exp_l(double n_sub, double ind, double nu)
{
  double bin_size, func;
	if (nu == 0.0)
		nu = 1e-14;
	if (n_sub == 0.0)
		n_sub = 1.0;

	bin_size = 1.0/n_sub;  //size of each sub-layer
	// rescale
	ind *= bin_size;
	// modify func
	func = exp(-nu*(1.0-ind))-exp(-nu);
	// normalize by its max
	func /= (1.0-exp(-nu));

	return func;
}

// To select function called
// At nu = 0 (singular point), call line function
double intersldfunc(int fun_type, double n_sub, double i, double nu, double sld_l, double sld_r)
{
	double sld_i, func;
	// this condition protects an error from the singular point
	if (nu == 0.0){
		nu = 1e-13;
	}
	// select func
	switch(fun_type){
		case 1 :
			func = power_r(n_sub, i, nu);
			break;
		case 2 :
			func = power_l(n_sub, i, nu);
			break;
		case 3 :
			func = exp_r(n_sub, i, nu);
			break;
		case 4 :
			func = exp_l(n_sub, i, nu);
			break;
		case 5 :
			func = linearfunc(n_sub, i, nu);
			break;
		default:
			func = err_mod_func(n_sub, i, nu);
			break;
	}
	// compute sld
	if (sld_r>sld_l){
		sld_i = (sld_r-sld_l)*func+sld_l; //sld_cal(sld[i],sld[i+1],n_sub,dz,thick);
	}
	else if (sld_r<sld_l){
		func = 1.0-func;
		sld_i = (sld_l-sld_r)*func+sld_r; //sld_cal(sld[i],sld[i+1],n_sub,dz,thick);
	}
	else{
		sld_i = sld_r;
	}
	return sld_i;
}


// used by refl.c
double interfunc(int fun_type, double n_sub, double i, double sld_l, double sld_r)
{
	double sld_i, func;
	switch(fun_type){
		case 0 :
			func = err_mod_func(n_sub, i, 2.5);
			break;
		default:
			func = linearfunc(n_sub, i, 1.0);
			break;
	}
	if (sld_r>sld_l){
		sld_i = (sld_r-sld_l)*func+sld_l; //sld_cal(sld[i],sld[i+1],n_sub,dz,thick);
	}
	else if (sld_r<sld_l){
		func = 1.0-func;
		sld_i = (sld_l-sld_r)*func+sld_r; //sld_cal(sld[i],sld[i+1],n_sub,dz,thick);
	}
	else{
		sld_i = sld_r;
	}
	return sld_i;
}

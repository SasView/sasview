// by jcho

#include <math.h>

#include "libfunc.h"

#include <stdio.h>



//used in Si func

int factorial(int i) {

	int k, j;
	if (i<2){
		return 1;
	}

	k=1;

	for(j=1;j<i;j++) {
		k=k*(j+1);
	}

	return k;

}



// Used in pearl nec model

// Sine integral function: approximated within 1%!!!

// integral of sin(x)/x up to namx term nmax=6 looks the best.

double Si(double x)

{
	int i;
	int nmax=6;
	double out;
	long double power;
	double pi = 4.0*atan(1.0);

	if (x >= pi*6.2/4.0){
		double out_sin = 0.0;
		double out_cos = 0.0;
		out = pi/2.0;

		for (i=0; i<nmax-2; i+=1) {
			out_cos += pow(-1.0, i) * (double)factorial(2*i) / pow(x, 2*i+1);
			out_sin += pow(-1.0, i) * (double)factorial(2*i+1) / pow(x, 2*i+2);
		}

		out -= cos(x) * out_cos;
		out -= sin(x) * out_sin;
		return out;
	}

	out = 0.0;

	for (i=0; i<nmax; i+=1)	{
		if (i==0) {
			out += x;
			continue;
		}

		power = pow(x,(2 * i + 1));
		out += (double)pow(-1, i) * power / ((2.0 * (double)i + 1.0) * (double)factorial(2 * i + 1));

		//printf ("Si=%g %g %d\n", x, out, i);
	}

	return out;
}



double sinc(double x)
{
  if (x==0.0){
    return 1.0;
  }
  return sin(x)/x;
}


double gamln(double xx) {

    double x,y,tmp,ser;
    static double cof[6]={76.18009172947146,-86.50532032941677,
    24.01409824083091,-1.231739572450155,
    0.1208650973866179e-2,-0.5395239384953e-5};
    int j;

    y=x=xx;
    tmp=x+5.5;
    tmp -= (x+0.5)*log(tmp);
    ser=1.000000000190015;
    for (j=0;j<=5;j++) ser += cof[j]/++y;
    return -tmp+log(2.5066282746310005*ser/x);
}

// calculate magnetic sld and return total sld
// bn : contrast (not just sld of the layer)
// m0: max mag of M; mtheta: angle from x-z plane;
// mphi: angle (anti-clock-wise)of x-z projection(M) from x axis
// spinfraci: the fraction of UP among UP+Down (before sample)
// spinfracf: the fraction of UP among UP+Down (after sample and before detector)
// spintheta: angle (anti-clock-wise) between neutron spin(up) and x axis
// Note: all angles are in degrees.
polar_sld cal_msld(int isangle, double qx, double qy, double bn,
				double m01, double mtheta1, double mphi1,
				double spinfraci, double spinfracf, double spintheta)
{
	//locals
	double q_x = qx;
	double q_y = qy;
	double sld = bn;
	int is_angle = isangle;
	double pi = 4.0*atan(1.0);
	double s_theta = spintheta * pi/180.0;
	double m_max = m01;
	double m_phi = mphi1;
	double m_theta = mtheta1;
	double in_spin = spinfraci;
	double out_spin = spinfracf;

	double m_perp = 0.0;
	double m_perp_z = 0.0;
	double m_perp_y = 0.0;
	double m_perp_x = 0.0;
	double m_sigma_x = 0.0;
	double m_sigma_z = 0.0;
	double m_sigma_y = 0.0;
	//double b_m = 0.0;
	double q_angle = 0.0;
	double mx = 0.0;
	double my = 0.0;
	double mz = 0.0;
	polar_sld p_sld;
	p_sld.uu = sld;
	p_sld.dd = sld;
	p_sld.re_ud = 0.0;
	p_sld.im_ud = 0.0;
	p_sld.re_du = 0.0;
	p_sld.im_du = 0.0;

	//No mag means no further calculation
	if (isangle>0){
		if (m_max < 1.0e-32){
			p_sld.uu = sqrt(sqrt(in_spin * out_spin)) * p_sld.uu;
			p_sld.dd = sqrt(sqrt((1.0 - in_spin) * (1.0 - out_spin))) * p_sld.dd;
			return p_sld;
		}
	}
	else{
		if (fabs(m_max)< 1.0e-32 && fabs(m_phi)< 1.0e-32 && fabs(m_theta)< 1.0e-32){
			p_sld.uu = sqrt(sqrt(in_spin * out_spin)) * p_sld.uu;
			p_sld.dd = sqrt(sqrt((1.0 - in_spin) * (1.0 - out_spin))) * p_sld.dd;
			return p_sld;
		}
	}

	//These are needed because of the precision of inputs
	if (in_spin < 0.0) in_spin = 0.0;
	if (in_spin > 1.0) in_spin = 1.0;
	if (out_spin < 0.0) out_spin = 0.0;
	if (out_spin > 1.0) out_spin = 1.0;

	if (q_x == 0.0) q_angle = pi / 2.0;
	else q_angle = atan(q_y/q_x);
	if (q_y < 0.0 && q_x < 0.0) q_angle -= pi;
	else if (q_y > 0.0 && q_x < 0.0) q_angle += pi;

	q_angle = pi/2.0 - q_angle;
	if (q_angle > pi) q_angle -= 2.0 * pi;
	else if (q_angle < -pi) q_angle += 2.0 * pi;

	if (fabs(q_x) < 1.0e-16 && fabs(q_y) < 1.0e-16){
		m_perp = 0.0;
		}
	else {
		m_perp = m_max;
		}
	if (is_angle > 0){
		m_phi *= pi/180.0;
		m_theta *= pi/180.0;
		mx = m_perp * cos(m_theta) * cos(m_phi);
		my = m_perp * sin(m_theta);
		mz = -(m_perp * cos(m_theta) * sin(m_phi));
	}
	else{
		mx = m_perp;
		my = m_phi;
		mz = m_theta;
	}
	//ToDo: simplify these steps
	// m_perp1 -m_perp2
	m_perp_x = (mx) *  cos(q_angle);
	m_perp_x -= (my) * sin(q_angle);
	m_perp_y = m_perp_x;
	m_perp_x *= cos(-q_angle);
	m_perp_y *= sin(-q_angle);
	m_perp_z = mz;

	m_sigma_x = (m_perp_x * cos(-s_theta) - m_perp_y * sin(-s_theta));
	m_sigma_y = (m_perp_x * sin(-s_theta) + m_perp_y * cos(-s_theta));
	m_sigma_z = (m_perp_z);

	//Find b
	p_sld.uu -= m_sigma_x;
	p_sld.dd += m_sigma_x;
	p_sld.re_ud = m_sigma_y;
	p_sld.re_du = m_sigma_y;
	p_sld.im_ud = m_sigma_z;
	p_sld.im_du = -m_sigma_z;

	p_sld.uu = sqrt(sqrt(in_spin * out_spin)) * p_sld.uu;
	p_sld.dd = sqrt(sqrt((1.0 - in_spin) * (1.0 - out_spin))) * p_sld.dd;

	p_sld.re_ud = sqrt(sqrt(in_spin * (1.0 - out_spin))) * p_sld.re_ud;
	p_sld.im_ud = sqrt(sqrt(in_spin * (1.0 - out_spin))) * p_sld.im_ud;
	p_sld.re_du = sqrt(sqrt((1.0 - in_spin) * out_spin)) * p_sld.re_du;
	p_sld.im_du = sqrt(sqrt((1.0 - in_spin) * out_spin)) * p_sld.im_du;

	return p_sld;
}


/** Modifications below by kieranrcampbell@gmail.com
    Institut Laue-Langevin, July 2012
**/

/**
   Implements eq 6.2.5 (small gamma) of Numerical Recipes in C, essentially
   the incomplete gamma function multiplied by the gamma function.
   Required for implementation of fast error function (erf)
**/


#define ITMAX 100
#define EPS 3.0e-7
#define FPMIN 1.0e-30

void gser(float *gamser, float a, float x, float *gln) {
  int n;
  float sum,del,ap;

  *gln = gamln(a);
  if(x <= 0.0) {
    if (x < 0.0) printf("Error: x less than 0 in routine gser");
    *gamser = 0.0;
    return;
  } else {
    ap = a;
    del = sum = 1.0/a;

    for(n=1;n<=ITMAX;n++) {
      ++ap;
      del *= x/ap;
      sum += del;
      if(fabs(del) < fabs(sum)*EPS) {
	*gamser = sum * exp(-x + a * log(x) - (*gln));
	return;
      }
    }
    printf("a too large, ITMAX too small in routine gser");
    return;

  }


}

/**
   Implements the incomplete gamma function Q(a,x) evaluated by its continued fraction
   representation
**/

void gcf(float *gammcf, float a, float x, float *gln) {
  int i;
  float an,b,c,d,del,h;

  *gln = gamln(a);
  b = x+1.0-a;
  c = 1.0/FPMIN;
  d = 1.0/b;
  h=d;
  for (i=1;i <= ITMAX; i++) {
    an = -i*(i-a);
    b += 2.0;
    d = an*d + b;
    if (fabs(d) < FPMIN) d = FPMIN;
    c = b+an/c;
    if (fabs(c) < FPMIN) c = FPMIN;
    d = 1.0/d;
    del = d*c;
    h += del;
    if (fabs(del-1.0) < EPS) break;
  }
  if (i > ITMAX) printf("a too large, ITMAX too small in gcf");
  *gammcf = exp(-x+a*log(x)-(*gln))*h;
  return;
}


/**
   Represents incomplete error function, P(a,x)
**/
float gammp(float a, float x) {
  float gamser,gammcf,gln;
  if(x < 0.0 || a <= 0.0) printf("Invalid arguments in routine gammp");
  if (x < (a+1.0)) {
    gser(&gamser,a,x,&gln);
    return gamser;
  } else {
    gcf(&gammcf,a,x,&gln);
    return 1.0 - gammcf;
  }
}

/**
    Implementation of the error function, erf(x)
**/

float erff(float x) {
  return x < 0.0 ? -gammp(0.5,x*x) : gammp(0.5,x*x);
}


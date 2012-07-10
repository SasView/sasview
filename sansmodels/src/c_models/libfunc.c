// by jcho

#include <math.h>

#include "libmultifunc/libfunc.h"

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


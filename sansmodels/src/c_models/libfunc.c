// by jcho
#include <math.h>
#include "libmultifunc/libfunc.h"
#include <stdio.h>

//used in Si func
int factorial(int i)
{
	int k, j;
	if (i<2){
		return 1;
	}
	k=1;
	for(j=1;j<i;j++)
	{
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
		for (i=0; i<nmax-2; i+=1){
			out_cos += pow(-1.0, i) * (double)factorial(2*i) / pow(x, 2*i+1);
			out_sin += pow(-1.0, i) * (double)factorial(2*i+1) / pow(x, 2*i+2);
		}
		out -= cos(x) * out_cos;
		out -= sin(x) * out_sin;
		return out;
	}
	out = 0.0;
	for (i=0; i<nmax; i+=1)
	{
		if (i==0){
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

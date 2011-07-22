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
//integral of sin(x)/x up to namx term nmax>10 looks fine.
double Si(double x, int nmax )
{
	int i;
	double out;
	long double power;
	if (x > 5.0){
		double pi = 4.0*atan(1.0);
		return pi/2.0;
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

double sin_x(double x)
{
	if (x==0){
		return 1.0;
	}
	return sin(x)/x;
}

/* This program is public domain. */

#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <math.h>
#ifdef SGI
#include <ieeefp.h>
#endif
#if defined(_MSC_VER)
double erf(double x)
{
    // constants
    double a1 =  0.254829592;
    double a2 = -0.284496736;
    double a3 =  1.421413741;
    double a4 = -1.453152027;
    double a5 =  1.061405429;
    double p  =  0.3275911;

    // Save the sign of x
    int sign = 1;

    double t = 1.0;
    double y = 1.0;
    if (x < 0)
        sign = -1;
    x = fabs(x);

    // A&S formula 7.1.26
    t = 1.0/(1.0 + p*x);
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*exp(-x*x);

    return sign*y;
}
#endif

/* What to do at the endpoints --- USE_TRUNCATED_NORMALIZATION will
 * avoid the assumption that the data is zero where it hasn't been
 * measured.
 */
#define USE_TRUNCATED_NORMALIZATION

/* Computed using extended precision with Octave's symbolic toolbox. */
#define PI4          12.56637061435917295385
#define PI_180        0.01745329251994329576
#define LN256         5.54517744447956247533
#define SQRT2         1.41421356237309504880
#define SQRT2PI       2.50662827463100050241

/* Choose the resolution limit based on relative contribution to resolution
 * rather than absolute contribution.  So if we ignore everything below,
 * e.g. 0.1% of the peak, that limit occurs when G(x)/G(0) = 0.001 for
 * gaussian G of width sima, or when x = sqrt(-2 sigma^2 log(0.001)). */
#define LOG_RESLIMIT -6.90775527898213703123

/** \file 
The resolution function returns the convolution of the reflectometry
curve with a Q-dependent gaussian.

We provide the following function:
   resolution(Nin, Qin, Rin, N, Q, dQ, R)  returns convolution

where
   Nin is the number of theory points
   Qin,Rin are the computed theory points
   N is the number of Q points to calculate
   Q are the locations of the measured data points
   dQ are the width (sigma) of the convolution at each measured point
   R is the returned convolution.

Note that FWHM = sqrt(8 ln 2) dQ, so scale dQ appropriately.

The contribution of Q to a resolution of width dQo at point Qo is:

   p(Q) = 1/sqrt(2 pi dQo^2) exp ( (Q-Qo)^2/(2 dQo^2) )

We are approximating the convolution at Qo using a numerical
approximation to the integral over the measured points.  For 
efficiency, the integral is limited to p(Q_i)/p(0)>=0.001.  

Note that the function we are convoluting is falling off as Q^4.
That means the correct convolution should uniformly sample across
the entire width of the Gaussian.  This is not possible at the
end points unless you calculate the reflectivity beyond what is
strictly needed for the data. For a given dQ and step size,
you need enough steps that the following is true:

    (n*step)^2 > -2 dQ^2 * ln 0.001

The choice of sampling density is particularly important near the 
critical edge.  This is where the resolution calculation has the 
largest effect on the reflectivity curve. In one particular model, 
calculating every 0.001 rather than every 0.02 changed one value 
above the critical edge by 15%.  This is likely to be a problem for 
any system with a well defined critical edge.  The solution is to
compute the theory function over a finer mesh where the derivative
is changing rapidly.  For the critical edge, I have found a sampling
density of 0.005 to be good enough.

For systems involving thick layers, the theory function oscillates 
rapidly around the measured points.  This is a problem when the
period of the oscillation, 2 pi/d for total sample depth d, is on
the order of the width of the resolution function. This is true even 
for gradually changing profiles in materials with very high roughness
values.  In these systems, the theory function should be oversampled
around the measured points Q.  With a single thick layer, oversampling
can be limited to just one period.  With multiple thick layers,
oscillations will show interference patterns and it will be necessary 
to oversample uniformly between the measured points.  When oversampled
spacing is less than about 2 pi/7 d, it is possible to see aliasing
effects.  

FIXME is it better to use random sampling or strictly
regular spacing when you are undersampling?

===============================================================
*/

#undef USE_TRAPEZOID_RULE
#ifdef USE_TRAPEZOID_RULE
#warning This code does strange things with small sigma and large spacing
/* FIXME trapezoid performs very badly for large spacing unless
   we normalize to the unit width.  For very small sigma, the gaussian
   is a spike, but we are approximating it by a triangle so it is
   not surprising it works so poorly.  A slightly better solution is
   to use the inner limits rather than the outer limits, but this will
   still break down if the Q spacing is approximately equal to limit. 
   Best is to not use trapezoid.
*/

/* Trapezoid rule for numerical integration of convolution */
double 
convolve_point(const double Qin[], const double Rin[], int k, int n,
        double Qo, double limit, double sigma)
{
  const double two_sigma_sq = 2. * sigma * sigma;
  double z, Glo, RGlo, R, norm;
  
  z = Qo - Qin[k];
  Glo = exp(-z*z/two_sigma_sq);
  RGlo = Rin[k]*Glo;
  norm = R = 0.;
  while (++k < n) {
    /* Compute the next endpoint */
    const double zhi = Qo - Qin[k];
    const double Ghi = exp(-zhi*zhi/two_sigma_sq);
    const double RGhi = Rin[k] * Ghi;
    const double halfstep = 0.5*(Qin[k] - Qin[k-1]);
    
    /* Add the trapezoidal area. */
    norm += halfstep * (Ghi + Glo);
    R += halfstep * (RGhi + RGlo);
    
    /* Save the endpoint for next trapezoid. */
    Glo = Ghi;
    RGlo = RGhi;
    
    /* Check if we've calculated far enough */
    if (Qin[k] >= Qo+limit) break;
  }

  /* Scale to area of the linear spline distribution we actually used. */
  return R / norm;

  /* Scale to gaussian of unit area */
  /* Fails badly for small sigma or large Q steps---do not use. */
  /* return R / sigma*SQRT2PI; */
}

#else /* !USE_TRAPEZOID_RULE */

/* Analytic convolution of gaussian with linear spline */
/* More expensive but more reliable */
double 
convolve_point(const double Qin[], const double Rin[], int k, int n,
               double Qo, double limit, double sigma)
{
  const double two_sigma_sq = 2. * sigma * sigma;
  double z, Glo, erflo, erfmin, R;
  double zhi, Ghi, erfhi, m, b;
  
  z = Qo - Qin[k];
  Glo = exp(-z*z/two_sigma_sq);
  erfmin = erflo = erf(-z/(SQRT2*sigma));
  R = 0.;
  /* printf("%5.3f: (%5.3f,%11.5g)",Qo,Qin[k],Rin[k]); */
  while (++k < n) {
  	/* No additional contribution from duplicate points. */
  	if (Qin[k] == Qin[k-1]) continue;
 
    /* Compute the next endpoint */
    zhi = Qo - Qin[k];
    Ghi = exp(-zhi*zhi/two_sigma_sq);
    erfhi = erf(-zhi/(SQRT2*sigma));
    m = (Rin[k]-Rin[k-1])/(Qin[k]-Qin[k-1]);
    b = Rin[k] - m * Qin[k];

    /* Add the integrals. */
    R += 0.5*(m*Qo+b)*(erfhi-erflo) - sigma/SQRT2PI*m*(Ghi-Glo);

    /* Debug computation failures. */
    /*
    if isnan(R) {
    	printf("NaN from %d: zhi=%g, Ghi=%g, erfhi=%g, m=%g, b=%g\n",
    	       k,zhi,Ghi,erfhi,m,b);
    }
    */
    
    /* Save the endpoint for next trapezoid. */
    Glo = Ghi;
    erflo = erfhi;
    
    /* Check if we've calculated far enough */
    if (Qin[k] >= Qo+limit) break;
  }
  /* printf(" (%5.3f,%11.5g)",Qin[k<n?k:n-1],Rin[k<n?k:n-1]); */

#ifdef USE_TRUNCATED_NORMALIZATION
  /* Normalize by the area of the truncated gaussian */
  /* At this point erflo = erfmax */
  /* printf ("---> %11.5g\n",2*R/(erflo-erfmin)); */
  return 2 * R / (erflo - erfmin);
#else
  /* Return unnormalized (we used a gaussian of unit area) */
  /* printf ("---> %11.5g\n",R); */
  return R;
#endif
}

#endif /* !USE_TRAPEZOID_RULE */

void
resolution(int Nin, const double Qin[], const double Rin[],
           int N, const double Q[], const double dQ[], double R[])
{
  int lo,out;
  double sigma, Qo, limit;

  /* FIXME fails if Qin are not sorted; slow if Q not sorted */
  assert(Nin>1);

  /* Scan through all Q values to be calculated */
  lo = 0;
  for (out=0; out < N; out++) {
    /* width of resolution window for Q is w = 2 dQ^2. */
    sigma = dQ[out];
    Qo = Q[out];
    limit = sqrt(-2.*sigma*sigma* LOG_RESLIMIT);

    /* if (out%20==0) printf("%d: Q,dQ = %g,%g\n",out,Qo,sigma); */

    /* Line up the left edge of the convolution window */
    /* It is probably forward from the current position, */
    /* but if the next dQ is a lot higher than the current */
    /* dQ or if the Q are not sorted, then it may be before */
    /* the current position. */
    /* FIXME verify that the convolution window is just right */
    while (lo < Nin-1 && Qin[lo] < Qo-limit) lo++;
    while (lo > 0 && Qin[lo] > Qo-limit) lo--;

    /* Special handling to avoid 0/0 for w=0. */
    if (sigma > 0.) {
      R[out] = convolve_point(Qin,Rin,lo,Nin,Qo,limit,sigma);
    } else if (lo < Nin-1) {
      /* Linear interpolation */
      double m = (Rin[lo+1]-Rin[lo])/(Qin[lo+1]-Qin[lo]);
      double b = Rin[lo] - m*Qin[lo];
      R[out] = m*Qo + b;
    } else if (lo > 0) {
      /* Linear extrapolation */
      double m = (Rin[lo]-Rin[lo-1])/(Qin[lo]-Qin[lo-1]);
      double b = Rin[lo] - m*Qin[lo];
      R[out] = m*Qo + b;
    } else {
      /* Can't happen because there is more than one point in Qin. */
      assert(Nin>1);
    }
  }

}

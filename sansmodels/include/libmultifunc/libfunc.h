#if !defined(o_h)
#define libfunc_h

int factorial(int i);

double Si(double x);

double sinc(double x);

double gamln(double x);

void gser(float *gamser, float a, float x, float *gln);

void gcf(float *gammcf, float a, float x, float *gln);

float gammp(float a,float x);

float erff(float x);

#endif

#if !defined(o_h)
#define libfunc_h
typedef struct {
	double uu;
	double dd;
	double re_ud;
	double im_ud;
	double re_du;
	double im_du;
} polar_sld;

int factorial(int i);

double Si(double x);

double sinc(double x);

double gamln(double x);

polar_sld cal_msld(int isangle, double qx, double qy, double bn, double m01, double mtheta1, 
			double mphi1, double spinfraci, double spinfracf, double spintheta);

void gser(float *gamser, float a, float x, float *gln);

void gcf(float *gammcf, float a, float x, float *gln);

float gammp(float a,float x);

float erff(float x);

#endif

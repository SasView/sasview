#if !defined(librefl_h)
#define librefl_h

typedef struct {
	double re;
	double im;
} complex;

typedef struct {
	complex a;
	complex b;
	complex c;
	complex d;
} matrix;

complex cassign(double real, double imag);

complex cplx_add(complex x,complex y);

complex rcmult(double x,complex y);

complex cplx_sub(complex x,complex y);

complex cplx_mult(complex x,complex y);

complex cplx_div(complex x,complex y);

complex cplx_exp(complex b);

complex cplx_sqrt(complex z);

complex cplx_cos(complex b);

double intersldfunc(int fun_type, double n_sub, double i, double nu, double sld_l, double sld_r);
double interfunc(int fun_type, double n_sub, double i, double sld_l, double sld_r);
double linePq(int fun_type, double thick, double sld_in, double sld_out,double r, double q);
#endif

#if !defined(librefl_h)
#define librefl_h

typedef struct {
	double re;
	double im;
} Cplx;

typedef struct {
	Cplx a;
	Cplx b;
	Cplx c;
	Cplx d;
} matrix;

void cassign(Cplx*, double real, double imag);

void cplx_add(Cplx*, Cplx x,Cplx y);

void rcmult(Cplx*, double x,Cplx y);

void cplx_sub(Cplx*, Cplx x,Cplx y);

void cplx_mult(Cplx*, Cplx x,Cplx y);

void cplx_div(Cplx*, Cplx x,Cplx y);

void cplx_exp(Cplx*, Cplx b);

void cplx_sqrt(Cplx*, Cplx z);

void cplx_cos(Cplx*, Cplx b);

double intersldfunc(int fun_type, double n_sub, double i, double nu, double sld_l, double sld_r);
double interfunc(int fun_type, double n_sub, double i, double sld_l, double sld_r);
double linePq(int fun_type, double thick, double sld_in, double sld_out,double r, double q);
#endif

#if !defined(invertor_h)
#define invertor_h

/**
 * Internal data structure for P(r) inversion
 */
typedef struct {
	/// Maximum distance between any two points in the system
    double d_max;
    /// q data
    double *x;
    /// I(q) data
    double *y;
    /// dI(q) data
    double *err;
    /// Number of q points
    int npoints;
    /// Number of I(q) points
    int ny;
    /// Number of dI(q) points
    int nerr;
    /// Alpha value
    double alpha;
    /// Minimum q to include in inversion
    double q_min;
    /// Maximum q to include in inversion
    double q_max;
    /// Flag for whether or not to evalute a constant background while inverting
    int est_bck;
    /// Slit height in units of q [A-1]
    double slit_height;
    /// Slit width in units of q [A-1]
    double slit_width;
} Invertor_params;

void invertor_dealloc(Invertor_params *pars);

void invertor_init(Invertor_params *pars);

double pr_sphere(double R, double r);
double ortho(double d_max, int n, double r);
double ortho_transformed(double d_max, int n, double q);
double ortho_derived(double d_max, int n, double r);
double iq(double *c, double d_max, int n_c, double q);
double pr(double *c, double d_max, int n_c, double r);
double dprdr(double *pars, double d_max, int n_c, double r);
double reg_term(double *pars, double d_max, int n_c, int nslice);
double int_p2(double *pars, double d_max, int n_c, int nslice);
void pr_err(double *pars, double *err, double d_max, int n_c,
		double r, double *pr_value, double *pr_value_err);
int npeaks(double *pars, double d_max, int n_c, int nslice);
double positive_integral(double *pars, double d_max, int n_c, int nslice);
double positive_errors(double *pars, double *err, double d_max, int n_c, int nslice);
double rg(double *pars, double d_max, int n_c, int nslice);
double int_pr(double *pars, double d_max, int n_c, int nslice);
double ortho_transformed_smeared(double d_max, int n, double heigth, double width, double q, int npts);
double iq_smeared(double *pars, double d_max, int n_c, double height, double width, double q, int npts);

#endif

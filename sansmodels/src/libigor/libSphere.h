// header for SphereFit.c

/* IGOR Fit Functions */
double MultiShell(double dp[], double q);
double PolyMultiShell(double dp[], double q);
double SphereForm(double dp[], double q);
double CoreShellForm(double dp[], double q);
double PolyCoreForm(double dp[], double q);
double PolyCoreShellRatio(double dp[], double q);
double VesicleForm(double dp[], double q);
double SchulzSpheres(double dp[], double q);
double PolyRectSpheres(double dp[], double q);
double PolyHardSphereIntensity(double dp[], double q);
double BimodalSchulzSpheres(double dp[], double q);
double GaussPolySphere(double dp[], double q);
double LogNormalPolySphere(double dp[], double q);
double BinaryHS(double dp[], double q);
double BinaryHS_PSF11(double dp[], double q);
double BinaryHS_PSF12(double dp[], double q);
double BinaryHS_PSF22(double dp[], double q);

//function prototypes
double F_func(double qr);
double MultiShellGuts(double q,double rcore,double ts,double tw,double rhocore,double rhoshel,int num);
double fnt2(double yy, double zz);
double fnt3(double yy, double pp, double zz);
double SchulzSphere_Fn(double scale, double ravg, double pd, double rho, double rhos, double x);
int ashcroft(double qval, double r2, double nf2, double aa, double phi, double *s11, double *s22, double *s12);

static double SchulzPoint(double x, double avg, double zz);
static double gammln(double xx);
static double Gauss_distr(double sig, double avg, double pt);
static double LogNormal_distr(double sig, double mu, double pt);

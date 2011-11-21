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
double OneShell(double dp[], double q);
double TwoShell(double dp[], double q);
double ThreeShell(double dp[], double q);
double FourShell(double dp[], double q);
double PolyOneShell(double dp[], double q);
double PolyTwoShell(double dp[], double q);
double PolyThreeShell(double dp[], double q);
double PolyFourShell(double dp[], double q);
double BCC_ParaCrystal(double dp[], double q);
double FCC_ParaCrystal(double dp[], double q);
double SC_ParaCrystal(double dp[], double q);
double FuzzySpheres(double dp[], double q);

//function prototypes
double F_func(double qr);
double MultiShellGuts(double q,double rcore,double ts,double tw,double rhocore,double rhoshel,int num);
double fnt2(double yy, double zz);
double fnt3(double yy, double pp, double zz);
double SchulzSphere_Fn(double scale, double ravg, double pd, double rho, double rhos, double x);
int ashcroft(double qval, double r2, double nf2, double aa, double phi, double *s11, double *s22, double *s12);
double BCC_Integrand(double w[], double qq, double xx, double yy);
double BCCeval(double Theta, double Phi, double temp1, double temp3);
double SphereForm_Paracrystal(double radius, double delrho, double x);
double FCC_Integrand(double w[], double qq, double xx, double yy);
double FCCeval(double Theta, double Phi, double temp1, double temp3);
double SC_Integrand(double w[], double qq, double xx, double yy);
double SCeval(double Theta, double Phi, double temp3, double temp4, double temp5);



static double
gammln(double xx) {
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

static double
LogNormal_distr(double sig, double mu, double pt)
{
	double retval,pi;

	pi = 4.0*atan(1.0);
	retval = (1.0/ (sig*pt*sqrt(2.0*pi)) )*exp( -0.5*(log(pt) - mu)*(log(pt) - mu)/sig/sig );
	return(retval);
}

static double
Gauss_distr(double sig, double avg, double pt)
{
	double retval,Pi;

	Pi = 4.0*atan(1.0);
	retval = (1.0/ (sig*sqrt(2.0*Pi)) )*exp(-(avg-pt)*(avg-pt)/sig/sig/2.0);
	return(retval);
}

static double SchulzPoint(double x, double avg, double zz) {
    double dr;
    dr = zz*log(x) - gammln(zz+1.0)+(zz+1.0)*log((zz+1.0)/avg)-(x/avg*(zz+1.0));
    return (exp(dr));
};


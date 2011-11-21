// header for TwoPhaseFit.c

//function prototypes
/* IGOR Fit Functions */
double TeubnerStreyModel(double dp[], double q);
double Power_Law_Model(double dp[], double q);
double Peak_Lorentz_Model(double dp[], double q);
double Peak_Gauss_Model(double dp[], double q);
double Lorentz_Model(double dp[], double q);
double Fractal(double dp[], double q);
double DAB_Model(double dp[], double q);
double OneLevel(double dp[], double q);
double TwoLevel(double dp[], double q);
double ThreeLevel(double dp[], double q);
double FourLevel(double dp[], double q);
double BroadPeak(double dp[], double q);
double CorrLength(double dp[], double q);
double TwoLorentzian(double dp[], double q);
double TwoPowerLaw(double dp[], double q);
double PolyGaussCoil(double dp[], double q);
double GaussLorentzGel(double dp[], double q);
double GaussianShell(double dp[], double q);


/* internal functions */
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



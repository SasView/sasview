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

/* internal functions */
static double gammln(double xx);


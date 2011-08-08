// header for SphereFit.c

/* IGOR Fit Functions */
double HardSphereStruct(double dp[], double q);
double SquareWellStruct(double dp[], double q);
double StickyHS_Struct(double dp[], double q);
double HayterPenfoldMSA(double dp[], double q);
double DiamCyl(double a, double b);
double DiamEllip(double a, double b);

static double gMSAWave[17]={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17};

//function prototypes
double sqhcal(double qq);
int sqfun(int ix, int ir);
int sqcoef(int ir);
// header for SphereFit.c

/* IGOR Fit Functions */
double HardSphereStruct(double dp[], double q);
double SquareWellStruct(double dp[], double q);
double StickyHS_Struct(double dp[], double q);
double HayterPenfoldMSA(double dp[], double q);
double DiamCyl(double a, double b);
double DiamEllip(double a, double b);

//function prototypes
double sqhcal(double qq, double gMSAWave[]);
int sqfun(int ix, int ir, double gMSAWave[]);
int sqcoef(int ir, double gMSAWave[]);

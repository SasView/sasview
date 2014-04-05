/*
	libCylinderFit.h -- equates for CylinderFit XOP
*/
#if defined(_MSC_VER)
#include "winFuncs.h"
#endif

/* Prototypes */
/* IGOR Fit Functions */
double CylinderForm(double dp[], double q);
double EllipCyl76(double dp[], double q);
double EllipCyl20(double dp[], double q);
double TriaxialEllipsoid(double dp[], double q);
double Parallelepiped(double dp[], double q);
double HollowCylinder(double dp[], double q);
double EllipsoidForm(double dp[], double q);
double Cyl_PolyRadius(double dp[], double q);
double Cyl_PolyLength(double dp[], double q);
double CoreShellCylinder(double dp[], double q);
double OblateForm(double dp[], double q);
double ProlateForm(double dp[], double q);
double FlexExclVolCyl(double dp[], double q);
double FlexCyl_PolyLen(double dp[], double q);
double FlexCyl_PolyRad(double dp[], double q);
double FlexCyl_Ellip(double dp[], double q);
double PolyCoShCylinder(double dp[], double q);
double StackedDiscs(double dp[], double q);
double LamellarFF(double dp[], double q);
double LamellarFF_HG(double dp[], double q);
double LamellarPS(double dp[], double q);
double LamellarPS_HG(double dp[], double q);
double Lamellar_ParaCrystal(double dp[], double q);
double Spherocylinder(double dp[], double q);
double ConvexLens(double dp[], double q);
double Dumbbell(double dp[], double q);
double CappedCylinder(double dp[], double q);
double Barbell(double dp[], double q);
double PolyCoreBicelle(double dp[], double q);
double CSParallelepiped(double dp[], double q);
double RectangularPrism(double dp[], double q);
double RectangularHollowPrismInfThinWalls(double dp[], double q);
double RectangularHollowPrism(double dp[], double q);

/* internal functions */
double CylKernel(double qq, double rr,double h, double theta);
double NR_BessJ1(double x);
double EllipCylKernel(double qq, double ra,double nu, double theta);
double TriaxialKernel(double q, double aa, double bb, double cc, double dx, double dy);
double PPKernel(double aa, double mu, double uu);
double HolCylKernel(double qq, double rcore, double rshell, double length, double dum);
double EllipsoidKernel(double qq, double a, double va, double dum);
double Cyl_PolyRadKernel(double q, double radius, double length, double zz, double delrho, double dumRad);
double SchulzPoint_cpr(double dumRad, double radius, double zz);
double Cyl_PolyLenKernel(double q, double radius, double len_avg, double zz, double delrho, double dumLen);
double CoreShellCylKernel(double qq, double rcore, double thick, double rhoc, double rhos, double rhosolv, double length, double dum);
double gfn4(double xx, double crmaj, double crmin, double trmaj, double trmin, double delpc, double delps, double qq);
double gfn2(double xx, double crmaj, double crmin, double trmaj, double trmin, double delpc, double delps, double qq);
double FlePolyLen_kernel(double q, double radius, double length, double lb, double zz, double delrho, double zi);
double FlePolyRad_kernel(double q, double ravg, double Lc, double Lb, double zz, double delrho, double zi);
double EllipticalCross_fn(double qq, double a, double b);
double CScyl(double qq, double rad, double radthick, double facthick, double rhoc, double rhos, double rhosolv, double length, double dum);
double CSCylIntegration(double qq, double rad, double radthick, double facthick, double rhoc, double rhos, double rhosolv, double length);
double Stackdisc_kern(double qq, double rcore, double rhoc, double rhol, double rhosolv, double length, double thick, double dum, double gsd, double d, double N);
double paraCryst_sn(double ww, double qval, double davg, long nl, double an);
double paraCryst_an(double ww, double qval, double davg, long nl);
double SphCyl_kernel(double w[], double x, double tt, double Theta);
double ConvLens_kernel(double w[], double x, double tt, double theta);
double Dumb_kernel(double w[], double x, double tt, double theta);
double BicelleKernel(double qq, double rad, double radthick, double facthick, double rhoc, double rhoh, double rhor, double rhosolv, double length, double dum);
double BicelleIntegration(double qq, double rad, double radthick, double facthick, double rhoc, double rhoh, double rhor, double rhosolv, double length);
double CSPPKernel(double dp[], double mu, double uu);



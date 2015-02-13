/*
 *  libSASAnalysis.h
 *  SASAnalysis
 *
 *  Created by Andrew Jackson on 4/24/07.
 *  Copyright 2007 __MyCompanyName__. All rights reserved.
 *
 */

#include "libCylinder.h"
#include "libSphere.h"
#include "libStructureFactor.h"
#include "libTwoPhase.h"

/*This should not be necessary AJJ May 09*/
/* IGOR Fit Functions */
/*
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
//
double Lamellar_ParaCrystal(double dp[], double q);
double Spherocylinder(double dp[], double q);
double ConvexLens(double dp[], double q);
double Dumbbell(double dp[], double q);
double CappedCylinder(double dp[], double q);
double Barbell(double dp[], double q);
double PolyCoreBicelle(double dp[], double q);
*/

/* internal functions */
/*
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
double BicelleKernel(double qq, double rad, double radthick, double facthick, double rhoc, double rhoh, double rhor, double rhosolv, double length, double dum);
double BicelleIntegration(double qq, double rad, double radthick, double facthick, double rhoc, double rhoh, double rhor, double rhosolv, double length);
*/


//
/* IGOR Fit Functions */
/*
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
//
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

//function prototypes
double F_func(double qr);
double MultiShellGuts(double q,double rcore,double ts,double tw,double rhocore,double rhoshel,int num);
double fnt2(double yy, double zz);
double fnt3(double yy, double pp, double zz);
double SchulzSphere_Fn(double scale, double ravg, double pd, double rho, double rhos, double x);
int ashcroft(double qval, double r2, double nf2, double aa, double phi, double *s11, double *s22, double *s12);


////
double HardSphereStruct(double dp[], double q);
double SquareWellStruct(double dp[], double q);
double StickyHS_Struct(double dp[], double q);
double HayterPenfoldMSA(double dp[], double q);
double DiamCyl(double a, double b);
double DiamEllip(double a, double b);
double sqhcal(double qq);
int sqfun(int ix, int ir);
int sqcoef(int ir);
*/
////
/* IGOR Fit Functions */
/*
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
//
double BroadPeak(double dp[], double q);
double CorrLength(double dp[], double q);
double TwoLorentzian(double dp[], double q);
double TwoPowerLaw(double dp[], double q);
double PolyGaussCoil(double dp[], double q);
double GaussLorentzGel(double dp[], double q);
double GaussianShell(double dp[], double q);
*/

// since the XOP and the library are separate chunks of compiled code
// it is imperative to set ALL the structure alignments to be two-byte
// rather than leave it to the whim of the compiler
/* SRK08
#include "XOPStructureAlignmentTwoByte.h"

typedef struct {
    double scale;
    double radius;
    double length;
    double contrast;
	double background;    
    double cyl_theta;
    double cyl_phi;    
} CylinderParameters;

typedef struct {
    double scale;
    double radius;
    double length;
    double contrast;
	double background;
    double cyl_theta;
    double cyl_phi; 
    double sigma_theta;
    double sigma_phi;
    double sigma_radius;
} SmearCylinderParameters;

#include "XOPStructureAlignmentReset.h"

/// 1D scattering function
double cylinder_analytical_1D(CylinderParameters *pars, double q);
/// 2D scattering function
double cylinder_analytical_2D(CylinderParameters *pars, double q, double phi);
/// 1D scattering function
double smeared_cylinder_analytical_1D(SmearCylinderParameters *pars, double q);
/// 2D scattering function
double dist_cylinder_2D(double pars[], double q, double phi);
double smeared_cylinder_analytical_2D(SmearCylinderParameters *pars, double q, double phi);
double smeared_cylinder_dist( double x, double mean, double sigma );
*/
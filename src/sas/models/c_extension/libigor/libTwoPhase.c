/*	TwoPhaseFit.c

*/

#include "StandardHeaders.h"			// Include ANSI headers, Mac headers
#include "libTwoPhase.h"

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

// scattering from the Teubner-Strey model for microemulsions - hardly needs to be an XOP...
double
TeubnerStreyModel(double dp[], double q)
{
	double inten,q2,q4;		//my local names
	
	q2 = q*q;
	q4 = q2*q2;
	
	inten = 1.0/(dp[0]+dp[1]*q2+dp[2]*q4);
	inten += dp[3];  
	return(inten);
}

double
Power_Law_Model(double dp[], double q)
{
	double qval;
	double inten,A,m,bgd;		//my local names
	
	qval= q;
	
	A = dp[0];
	m = dp[1];
	bgd = dp[2];
	inten = A*pow(qval,-m) + bgd;
	return(inten);
}


double
Peak_Lorentz_Model(double dp[], double q)
{
	double qval;
	double inten,I0, qpk, dq,bgd;		//my local names
	qval= q;
	
	I0 = dp[0];
	qpk = dp[1];
	dq = dp[2];
	bgd = dp[3];
	inten = I0/(1.0 + pow( (qval-qpk)/dq,2) ) + bgd;
	
	return(inten);
}

double
Peak_Gauss_Model(double dp[], double q)
{
	double qval;
	double inten,I0, qpk, dq,bgd;		//my local names
	
	qval= q;
	
	I0 = dp[0];
	qpk = dp[1];
	dq = dp[2];
	bgd = dp[3];
	inten = I0*exp(-0.5*pow((qval-qpk)/dq,2))+ bgd;
	
	return(inten);
}

double
Lorentz_Model(double dp[], double q)
{
	double qval;
	double inten,I0, L,bgd;		//my local names
	
	qval= q;
	
	I0 = dp[0];
	L = dp[1];
	bgd = dp[2];
	inten = I0/(1.0 + (qval*L)*(qval*L)) + bgd;
	
	return(inten);
}

double
Fractal(double dp[], double q)
{
	double x,pi;
	double r0,Df,corr,phi,sldp,sldm,bkg;
	double pq,sq,ans;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	phi = dp[0];		// volume fraction of building block spheres...
	r0 = dp[1];		//  radius of building block
	Df = dp[2];		//  fractal dimension
	corr = dp[3];		//  correlation length of fractal-like aggregates
	sldp = dp[4];		// SLD of building block
	sldm = dp[5];		// SLD of matrix or solution
	bkg = dp[6];		//  flat background 
	
	//calculate P(q) for the spherical subunits, units cm-1 sr-1
	pq = 1.0e8*phi*4.0/3.0*pi*r0*r0*r0*(sldp-sldm)*(sldp-sldm)*pow((3*(sin(x*r0) - x*r0*cos(x*r0))/pow((x*r0),3)),2);
	
	//calculate S(q)
	sq = Df*exp(gammln(Df-1.0))*sin((Df-1.0)*atan(x*corr));
	sq /= pow((x*r0),Df) * pow((1.0 + 1.0/(x*corr)/(x*corr)),((Df-1.0)/2.0));
	sq += 1.0;
	//combine and return
	ans = pq*sq + bkg;
	
	return(ans);
}

// 6 JUL 2009 SRK changed definition of Izero scale factor to be uncorrelated with range
//
double
DAB_Model(double dp[], double q)
{
	double qval,inten;
	double Izero, range, incoh;
	
	qval= q;
	Izero = dp[0];
	range = dp[1];
	incoh = dp[2]; 
	
	inten = (Izero*range*range*range)/pow((1.0 + (qval*range)*(qval*range)),2) + incoh;
	
	return(inten);
}

// G. Beaucage's Unified Model (1-4 levels)
//
double
OneLevel(double dp[], double q)
{
	double x,ans,erf1;
	double G1,Rg1,B1,Pow1,bkg,scale;
	
	x=q;
	scale = dp[0];
	G1 = dp[1];
	Rg1 = dp[2];
	B1 = dp[3];
	Pow1 = dp[4];
	bkg = dp[5];
	
	erf1 = erf( (x*Rg1/sqrt(6.0)));
	
	ans = G1*exp(-x*x*Rg1*Rg1/3.0);
	ans += B1*pow((erf1*erf1*erf1/x),Pow1);
	
	if(x == 0) {
		ans = G1;
	}
	
	ans *= scale;
	ans += bkg;
	return(ans);
}

// G. Beaucage's Unified Model (1-4 levels)
//
double
TwoLevel(double dp[], double q)
{
	double x;
	double ans,G1,Rg1,B1,G2,Rg2,B2,Pow1,Pow2,bkg;
	double erf1,erf2,scale;
	
	x=q;
	
	scale = dp[0];
	G1 = dp[1];	//equivalent to I(0)
	Rg1 = dp[2];
	B1 = dp[3];
	Pow1 = dp[4];
	G2 = dp[5];
	Rg2 = dp[6];
	B2 = dp[7];
	Pow2 = dp[8];
	bkg = dp[9];
	
	erf1 = erf( (x*Rg1/sqrt(6.0)) );
	erf2 = erf( (x*Rg2/sqrt(6.0)) );
	//Print erf1
	
	ans = G1*exp(-x*x*Rg1*Rg1/3.0);
	ans += B1*exp(-x*x*Rg2*Rg2/3.0)*pow((erf1*erf1*erf1/x),Pow1);
	ans += G2*exp(-x*x*Rg2*Rg2/3.0);
	ans += B2*pow((erf2*erf2*erf2/x),Pow2);

	if(x == 0) {
		ans = G1+G2;
	}
	
	ans *= scale;
	ans += bkg;
	
	return(ans);
}

// G. Beaucage's Unified Model (1-4 levels)
//
double
ThreeLevel(double dp[], double q)
{
	double x;
	double ans,G1,Rg1,B1,G2,Rg2,B2,Pow1,Pow2,bkg;
	double G3,Rg3,B3,Pow3,erf3;
	double erf1,erf2,scale;
	
	x=q;
	
	scale = dp[0];
	G1 = dp[1];	//equivalent to I(0)
	Rg1 = dp[2];
	B1 = dp[3];
	Pow1 = dp[4];
	G2 = dp[5];
	Rg2 = dp[6];
	B2 = dp[7];
	Pow2 = dp[8];
	G3 = dp[9];
	Rg3 = dp[10];
	B3 = dp[11];
	Pow3 = dp[12];
	bkg = dp[13];
	
	erf1 = erf( (x*Rg1/sqrt(6.0)) );
	erf2 = erf( (x*Rg2/sqrt(6.0)) );
	erf3 = erf( (x*Rg3/sqrt(6.0)) );
	//Print erf1
	
	ans = G1*exp(-x*x*Rg1*Rg1/3.0) + B1*exp(-x*x*Rg2*Rg2/3.0)*pow((erf1*erf1*erf1/x),Pow1);
	ans += G2*exp(-x*x*Rg2*Rg2/3.0) + B2*exp(-x*x*Rg3*Rg3/3.0)*pow((erf2*erf2*erf2/x),Pow2);
	ans += G3*exp(-x*x*Rg3*Rg3/3.0) + B3*pow((erf3*erf3*erf3/x),Pow3);

	if(x == 0) {
		ans = G1+G2+G3;
	}
	
	ans *= scale;
	ans += bkg;
	
	return(ans);
}

// G. Beaucage's Unified Model (1-4 levels)
//
double
FourLevel(double dp[], double q)
{
	double x;
	double ans,G1,Rg1,B1,G2,Rg2,B2,Pow1,Pow2,bkg;
	double G3,Rg3,B3,Pow3,erf3;
	double G4,Rg4,B4,Pow4,erf4;
	double erf1,erf2,scale;
	
	x=q;
	
	scale = dp[0];
	G1 = dp[1];	//equivalent to I(0)
	Rg1 = dp[2];
	B1 = dp[3];
	Pow1 = dp[4];
	G2 = dp[5];
	Rg2 = dp[6];
	B2 = dp[7];
	Pow2 = dp[8];
	G3 = dp[9];
	Rg3 = dp[10];
	B3 = dp[11];
	Pow3 = dp[12];
	G4 = dp[13];
	Rg4 = dp[14];
	B4 = dp[15];
	Pow4 = dp[16];
	bkg = dp[17];
	
	erf1 = erf( (x*Rg1/sqrt(6.0)) );
	erf2 = erf( (x*Rg2/sqrt(6.0)) );
	erf3 = erf( (x*Rg3/sqrt(6.0)) );
	erf4 = erf( (x*Rg4/sqrt(6.0)) );
	
	ans = G1*exp(-x*x*Rg1*Rg1/3.0) + B1*exp(-x*x*Rg2*Rg2/3.0)*pow((erf1*erf1*erf1/x),Pow1);
	ans += G2*exp(-x*x*Rg2*Rg2/3.0) + B2*exp(-x*x*Rg3*Rg3/3.0)*pow((erf2*erf2*erf2/x),Pow2);
	ans += G3*exp(-x*x*Rg3*Rg3/3.0) + B3*exp(-x*x*Rg4*Rg4/3.0)*pow((erf3*erf3*erf3/x),Pow3);
	ans += G4*exp(-x*x*Rg4*Rg4/3.0) + B4*pow((erf4*erf4*erf4/x),Pow4);

	if(x == 0) {
		ans = G1+G2+G3+G4;
	}
	
	ans *= scale;
	ans += bkg;
	
    return(ans);
}

double
BroadPeak(double dp[], double q)
{
	// variables are:							
	//[0] Porod term scaling
	//[1] Porod exponent
	//[2] Lorentzian term scaling
	//[3] Lorentzian screening length [A]
	//[4] peak location [1/A]
	//[5] Lorentzian exponent
	//[6] background
	
	double aa,nn,cc,LL,Qzero,mm,bgd,inten,qval;
	qval= q;
	aa = dp[0];
	nn = dp[1];
	cc = dp[2]; 
	LL = dp[3]; 
	Qzero = dp[4]; 
	mm = dp[5]; 
	bgd = dp[6]; 
	
	inten = aa/pow(qval,nn);
	inten += cc/(1.0 + pow((fabs(qval-Qzero)*LL),mm) );
	inten += bgd;
	
	return(inten);
}

double
CorrLength(double dp[], double q)
{
	// variables are:							
	//[0] Porod term scaling
	//[1] Porod exponent
	//[2] Lorentzian term scaling
	//[3] Lorentzian screening length [A]
	//[4] Lorentzian exponent
	//[5] background
	
	double aa,nn,cc,LL,mm,bgd,inten,qval;
	qval= q;
	aa = dp[0];
	nn = dp[1];
	cc = dp[2]; 
	LL = dp[3]; 
	mm = dp[4]; 
	bgd = dp[5]; 
	
	inten = aa/pow(qval,nn);
	inten += cc/(1.0 + pow((qval*LL),mm) );
	inten += bgd;
	
	return(inten);
}

double
TwoLorentzian(double dp[], double q)
{
	// variables are:							
	//[0] Lorentzian term scaling
	//[1] Lorentzian screening length [A]
	//[2] Lorentzian exponent
	//[3] Lorentzian #2 term scaling
	//[4] Lorentzian #2 screening length [A]
	//[5] Lorentzian #2 exponent
	//[6] background
		
	double aa,LL1,nn,cc,LL2,mm,bgd,inten,qval;
	qval= q;
	aa = dp[0];
	LL1 = dp[1];
	nn = dp[2]; 
	cc = dp[3]; 
	LL2 = dp[4]; 
	mm = dp[5]; 
	bgd= dp[6];
	
	inten = aa/(1.0 + pow((qval*LL1),nn) );
	inten += cc/(1.0 + pow((qval*LL2),mm) );
	inten += bgd;
	
	return(inten);
}

double
TwoPowerLaw(double dp[], double q)
{
	//[0] Coefficient
	//[1] (-) Power @ low Q
	//[2] (-) Power @ high Q
	//[3] crossover Q-value
	//[4] incoherent background
		
	double A, m1,m2,qc,bgd,scale,inten,qval;
	qval= q;
	A = dp[0];
	m1 = dp[1];
	m2 = dp[2]; 
	qc = dp[3]; 
	bgd = dp[4]; 
	
	if(qval<=qc){
		inten = A*pow(qval,-1.0*m1);
	} else {
		scale = A*pow(qc,-1.0*m1) / pow(qc,-1.0*m2);
		inten = scale*pow(qval,-1.0*m2);
	}
	
	inten += bgd;
	
	return(inten);
}

double
PolyGaussCoil(double dp[], double x)
{
	//w[0] = scale
	//w[1] = radius of gyration [�]
	//w[2] = polydispersity, ratio of Mw/Mn
	//w[3] = bkg [cm-1]
		
	double scale,bkg,Rg,uval,Mw_Mn,inten,xi;

	scale = dp[0];
	Rg = dp[1];
	Mw_Mn = dp[2]; 
	bkg = dp[3]; 
	
	uval = Mw_Mn - 1.0;
	if(uval == 0.0) {
		uval = 1e-6;		//avoid divide by zero error
	}
	
	xi = Rg*Rg*x*x/(1.0+2.0*uval);
	
	if(xi < 1e-3) {
		return(scale+bkg);		//limiting value
	}
	
	inten = 2.0*(pow((1.0+uval*xi),(-1.0/uval))+xi-1.0);
	inten /= (1.0+uval)*xi*xi;

	inten *= scale;
	//add in the background
	inten += bkg;	
	return(inten);
}

double
GaussLorentzGel(double dp[], double x)
{
	//[0] Gaussian scale factor
	//[1] Gaussian (static) screening length
	//[2] Lorentzian (fluctuation) scale factor
	//[3] Lorentzian screening length
	//[4] incoherent background
		
	double Ig0,gg,Il0,ll,bgd,inten;

	Ig0 = dp[0];
	gg = dp[1];
	Il0 = dp[2]; 
	ll = dp[3];
	bgd = dp[4]; 
	
	inten = Ig0*exp(-1.0*x*x*gg*gg/2.0) + Il0/(1.0 + (x*ll)*(x*ll)) + bgd;
	
	return(inten);
}


double
GaussianShell(double w[], double x)
{
	// variables are:							
	//[0] scale
	//[1] radius (�)
	//[2] thick (�) (thickness parameter - this is the std. dev. of the Gaussian width of the shell)
	//[3] polydispersity of the radius
	//[4] sld shell (�-2)
	//[5] sld solvent
	//[6] background (cm-1)
	
	double scale,rad,delrho,bkg,del,thick,pd,sig,pi;
	double t1,t2,t3,t4,retval,exfact,vshell,vexcl,sldShell,sldSolvent;
	scale = w[0];
	rad = w[1];
	thick = w[2];
	pd = w[3];
	sldShell = w[4];
	sldSolvent = w[5];
	bkg = w[6];
	
	delrho = w[4] - w[5];
	sig = pd*rad;
	
	pi = 4.0*atan(1.0);
	
	///APPROXIMATION (see eqn 4 - but not a bad approximation)
	// del is the equivalent shell thickness with sharp boundaries, centered at mean radius
	del = thick*sqrt(2.0*pi);
	
	// calculate the polydisperse shell volume and the excluded volume
	vshell=4.0*pi/3.0*( pow((rad+del/2.0),3) - pow((rad-del/2.0),3) ) *(1.0+pd*pd);
	vexcl=4.0*pi/3.0*( pow((rad+del/2.0),3) ) *(1.0+pd*pd);
	
	//intensity, eqn 9(a-d)
	exfact = exp(-2.0*sig*sig*x*x);
	
	t1 = 0.5*x*x*thick*thick*thick*thick*(1.0+cos(2.0*x*rad)*exfact);
	t2 = x*thick*thick*(rad*sin(2.0*x*rad) + 2.0*x*sig*sig*cos(2.0*x*rad))*exfact;
	t3 = 0.5*rad*rad*(1.0-cos(2.0*x*rad)*exfact);
	t4 = 0.5*sig*sig*(1.0+4.0*x*rad*sin(2.0*x*rad)*exfact+cos(2.0*x*rad)*(4.0*sig*sig*x*x-1.0)*exfact);
	
	retval = t1+t2+t3+t4;
	retval *= exp(-1.0*x*x*thick*thick);
	retval *= (del*del/x/x);
	retval *= 16.0*pi*pi*delrho*delrho*scale;
	retval *= 1.0e8;
	
	//NORMALIZED by the AVERAGE shell volume, since scale is the volume fraction of material
//	retval /= vshell
	retval /= vexcl;
	//re-normalize by polydisperse sphere volume, Gaussian distribution
	retval /= (1.0+3.0*pd*pd);
	
	retval += bkg;
	
	return(retval);
}



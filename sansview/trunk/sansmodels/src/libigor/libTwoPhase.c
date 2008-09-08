/*	TwoPhaseFit.c

*/

#include "StandardHeaders.h"			// Include ANSI headers, Mac headers
#include "libTwoPhase.h"

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

double
DAB_Model(double dp[], double q)
{
	double qval,inten;
	double Izero, range, incoh;
	
	qval= q;
	Izero = dp[0];
	range = dp[1];
	incoh = dp[2]; 
	
	inten = Izero/pow((1.0 + (qval*range)*(qval*range)),2) + incoh;
	
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
	
	ans *= scale;
	ans += bkg;
	
    return(ans);
}


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



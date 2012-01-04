/*	SimpleFit.c

A simplified project designed to act as a template for your curve fitting function.
The fitting function is a simple polynomial. It works but is of no practical use.
*/

#include "StandardHeaders.h"			// Include ANSI headers, Mac headers
#include "GaussWeights.h"
#include "libSphere.h"


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


// scattering from a sphere - hardly needs to be an XOP...
double
SphereForm(double dp[], double q)
{
	double scale,radius,delrho,bkg,sldSph,sldSolv;		//my local names
	double bes,f,vol,f2,pi,qr;

	pi = 4.0*atan(1.0);
	scale = dp[0];
	radius = dp[1];
	sldSph = dp[2];
	sldSolv = dp[3];
	bkg = dp[4];
	
	delrho = sldSph - sldSolv;
	//handle qr==0 separately
	qr = q*radius;
	if(qr == 0.0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	
	vol = 4.0*pi/3.0*radius*radius*radius;
	f = vol*bes*delrho;		// [=] A-1
							// normalize to single particle volume, convert to 1/cm
	f2 = f * f / vol * 1.0e8;		// [=] 1/cm
	
	return(scale*f2+bkg);	//scale, and add in the background
}

// scattering from a monodisperse core-shell sphere - hardly needs to be an XOP...
double
CoreShellForm(double dp[], double q)
{
	double x,pi;
	double scale,rcore,thick,rhocore,rhoshel,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	scale = dp[0];
	rcore = dp[1];
	thick = dp[2];
	rhocore = dp[3];
	rhoshel = dp[4];
	rhosolv = dp[5];
	bkg = dp[6];
	// core first, then add in shell
	qr=x*rcore;
	contr = rhocore-rhoshel;
	if(qr == 0.0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell
	qr=x*(rcore+thick);
	contr = rhoshel-rhosolv;
	if(qr == 0.0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*pow((rcore+thick),3);
	f += vol*bes*contr;

	// normalize to particle volume and rescale from [A-1] to [cm-1]
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}

// scattering from a unilamellar vesicle - hardly needs to be an XOP...
// same functional form as the core-shell sphere, but more intuitive for a vesicle
double
VesicleForm(double dp[], double q)
{
	double x,pi;
	double scale,rcore,thick,rhocore,rhoshel,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	pi = 4.0*atan(1.0);
	x= q;
	
	scale = dp[0];
	rcore = dp[1];
	thick = dp[2];
	rhocore = dp[3];
	rhosolv = rhocore;
	rhoshel = dp[4];
	bkg = dp[5];
	// core first, then add in shell
	qr=x*rcore;
	contr = rhocore-rhoshel;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell
	qr=x*(rcore+thick);
	contr = rhoshel-rhosolv;
	if(qr == 0.0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*pow((rcore+thick),3);
	f += vol*bes*contr;

	// normalize to the particle volume and rescale from [A-1] to [cm-1]
	//note that for the vesicle model, the volume is ONLY the shell volume
	vol = 4.0*pi/3.0*(pow((rcore+thick),3)-pow(rcore,3));
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}


// scattering from a core shell sphere with a (Schulz) polydisperse core and constant shell thickness
//
double
PolyCoreForm(double dp[], double q)
{
	double pi;
	double scale,corrad,sig,zz,del,drho1,drho2,form,bkg;		//my local names
	double d, g ,h;
	double qq, x, y, c1, c2, c3, c4, c5, c6, c7, c8, c9, t1, t2, t3;
	double t4, t5, tb, cy, sy, tb1, tb2, tb3, c2y, zp1, zp2;
	double zp3,vpoly;
	double s2y, arg1, arg2, arg3, drh1, drh2;
	
	pi = 4.0*atan(1.0);
	qq= q;
	scale = dp[0];
	corrad = dp[1];
	sig = dp[2];
	del = dp[3];
	drho1 = dp[4]-dp[5];		//core-shell
	drho2 = dp[5]-dp[6];		//shell-solvent
	bkg = dp[7];
	
	zz = (1.0/sig)*(1.0/sig) - 1.0;   
	
	h=qq;
	
	drh1 = drho1;
	drh2 = drho2;
	g = drh2 * -1. / drh1;
	zp1 = zz + 1.;
	zp2 = zz + 2.;
	zp3 = zz + 3.;
	vpoly = 4*pi/3*zp3*zp2/zp1/zp1*pow((corrad+del),3);
	
	
	// remember that h is the passed in value of q for the calculation
	y = h *del;
	x = h *corrad;
	d = atan(x * 2. / zp1);
	arg1 = zp1 * d;
	arg2 = zp2 * d;
	arg3 = zp3 * d;
	sy = sin(y);
	cy = cos(y);
	s2y = sin(y * 2.);
	c2y = cos(y * 2.);
	c1 = .5 - g * (cy + y * sy) + g * g * .5 * (y * y + 1.);
	c2 = g * y * (g - cy);
	c3 = (g * g + 1.) * .5 - g * cy;
	c4 = g * g * (y * cy - sy) * (y * cy - sy) - c1;
	c5 = g * 2. * sy * (1. - g * (y * sy + cy)) + c2;
	c6 = c3 - g * g * sy * sy;
	c7 = g * sy - g * .5 * g * (y * y + 1.) * s2y - c5;
	c8 = c4 - .5 + g * cy - g * .5 * g * (y * y + 1.) * c2y;
	c9 = g * sy * (1. - g * cy);
	
	tb = log(zp1 * zp1 / (zp1 * zp1 + x * 4. * x));
	tb1 = exp(zp1 * .5 * tb);
	tb2 = exp(zp2 * .5 * tb);
	tb3 = exp(zp3 * .5 * tb);
	
	t1 = c1 + c2 * x + c3 * x * x * zp2 / zp1;
	t2 = tb1 * (c4 * cos(arg1) + c7 * sin(arg1));
	t3 = x * tb2 * (c5 * cos(arg2) + c8 * sin(arg2));
	t4 = zp2 / zp1 * x * x * tb3 * (c6 * cos(arg3) + c9 * sin(arg3));
	t5 = t1 + t2 + t3 + t4;
	form = t5 * 16. * pi * pi * drh1 * drh1 / pow(qq,6);
	//	normalize by the average volume !!! corrected for polydispersity
	// and convert to cm-1
	form /= vpoly;
	form *= 1.0e8;
	//Scale
	form *= scale;
	// then add in the background
	form += bkg;
	
	return(form);
}

// scattering from a uniform sphere with a (Schulz) size distribution
// structure factor effects are explicitly and correctly included.
//
double
PolyHardSphereIntensity(double dp[], double q)
{
	double pi;
	double rad,z2,phi,cont,bkg,sigma;		//my local names
	double mu,mu1,d1,d2,d3,d4,d5,d6,capd,rho;
	double ll,l1,bb,cc,chi,chi1,chi2,ee,t1,t2,t3,pp;
	double ka,zz,v1,v2,p1,p2;
	double h1,h2,h3,h4,e1,yy,y1,s1,s2,s3,hint1,hint2;
	double capl,capl1,capmu,capmu1,r3,pq;
	double ka2,r1,heff;
	double hh,k,slds,sld;
	
	pi = 4.0*atan(1.0);
	k= q;
	
	rad = dp[0];		// radius (A)
	z2 = dp[1];		//polydispersity (0<z2<1)
	phi = dp[2];		// volume fraction (0<phi<1)
	slds = dp[3];
	sld = dp[4];
	cont = (slds - sld)*1.0e4;		// contrast (odd units)
	bkg = dp[5];
	sigma = 2*rad;
	
	zz=1.0/(z2*z2)-1.0;
	bb = sigma/(zz+1.0);
	cc = zz+1.0;
	
	//*c   Compute the number density by <r-cubed>, not <r> cubed*/
	r1 = sigma/2.0;
	r3 = r1*r1*r1;
	r3 *= (zz+2.0)*(zz+3.0)/((zz+1.0)*(zz+1.0));
	rho=phi/(1.3333333333*pi*r3);
	t1 = rho*bb*cc;
	t2 = rho*bb*bb*cc*(cc+1.0);
	t3 = rho*bb*bb*bb*cc*(cc+1.0)*(cc+2.0);
	capd = 1.0-pi*t3/6.0;
	//************
	v1=1.0/(1.0+bb*bb*k*k);
	v2=1.0/(4.0+bb*bb*k*k);
	pp=pow(v1,(cc/2.0))*sin(cc*atan(bb*k));
	p1=bb*cc*pow(v1,((cc+1.0)/2.0))*sin((cc+1.0)*atan(bb*k));
	p2=cc*(cc+1.0)*bb*bb*pow(v1,((cc+2.0)/2.0))*sin((cc+2.0)*atan(bb*k));
	mu=pow(2,cc)*pow(v2,(cc/2.0))*sin(cc*atan(bb*k/2.0));
	mu1=pow(2,(cc+1.0))*bb*cc*pow(v2,((cc+1.0)/2.0))*sin((cc+1.0)*atan(k*bb/2.0));
	s1=bb*cc;
	s2=cc*(cc+1.0)*bb*bb;
	s3=cc*(cc+1.0)*(cc+2.0)*bb*bb*bb;
	chi=pow(v1,(cc/2.0))*cos(cc*atan(bb*k));
	chi1=bb*cc*pow(v1,((cc+1.0)/2.0))*cos((cc+1.0)*atan(bb*k));
	chi2=cc*(cc+1.0)*bb*bb*pow(v1,((cc+2.0)/2.0))*cos((cc+2.0)*atan(bb*k));
	ll=pow(2,cc)*pow(v2,(cc/2.0))*cos(cc*atan(bb*k/2.0));
	l1=pow(2,(cc+1.0))*bb*cc*pow(v2,((cc+1.0)/2.0))*cos((cc+1.0)*atan(k*bb/2.0));
	d1=(pi/capd)*(2.0+(pi/capd)*(t3-(rho/k)*(k*s3-p2)));
	d2=pow((pi/capd),2)*(rho/k)*(k*s2-p1);
	d3=(-1.0)*pow((pi/capd),2)*(rho/k)*(k*s1-pp);
	d4=(pi/capd)*(k-(pi/capd)*(rho/k)*(chi1-s1));
	d5=pow((pi/capd),2)*((rho/k)*(chi-1.0)+0.5*k*t2);
	d6=pow((pi/capd),2)*(rho/k)*(chi2-s2);
	
	e1=pow((pi/capd),2)*pow((rho/k/k),2)*((chi-1.0)*(chi2-s2)-(chi1-s1)*(chi1-s1)-(k*s1-pp)*(k*s3-p2)+pow((k*s2-p1),2));
	ee=1.0-(2.0*pi/capd)*(1.0+0.5*pi*t3/capd)*(rho/k/k/k)*(k*s1-pp)-(2.0*pi/capd)*rho/k/k*((chi1-s1)+(0.25*pi*t2/capd)*(chi2-s2))-e1;
	y1=pow((pi/capd),2)*pow((rho/k/k),2)*((k*s1-pp)*(chi2-s2)-2.0*(k*s2-p1)*(chi1-s1)+(k*s3-p2)*(chi-1.0));
	yy = (2.0*pi/capd)*(1.0+0.5*pi*t3/capd)*(rho/k/k/k)*(chi+0.5*k*k*s2-1.0)-(2.0*pi*rho/capd/k/k)*(k*s2-p1+(0.25*pi*t2/capd)*(k*s3-p2))-y1;    
	
	capl=2.0*pi*cont*rho/k/k/k*(pp-0.5*k*(s1+chi1));
	capl1=2.0*pi*cont*rho/k/k/k*(p1-0.5*k*(s2+chi2));
	capmu=2.0*pi*cont*rho/k/k/k*(1.0-chi-0.5*k*p1);
	capmu1=2.0*pi*cont*rho/k/k/k*(s1-chi1-0.5*k*p2);
	
	h1=capl*(capl*(yy*d1-ee*d6)+capl1*(yy*d2-ee*d4)+capmu*(ee*d1+yy*d6)+capmu1*(ee*d2+yy*d4));
	h2=capl1*(capl*(yy*d2-ee*d4)+capl1*(yy*d3-ee*d5)+capmu*(ee*d2+yy*d4)+capmu1*(ee*d3+yy*d5));
	h3=capmu*(capl*(ee*d1+yy*d6)+capl1*(ee*d2+yy*d4)+capmu*(ee*d6-yy*d1)+capmu1*(ee*d4-yy*d2));
	h4=capmu1*(capl*(ee*d2+yy*d4)+capl1*(ee*d3+yy*d5)+capmu*(ee*d4-yy*d2)+capmu1*(ee*d5-yy*d3));
	
	//*  This part computes the second integral in equation (1) of the paper.*/
	
	hint1 = -2.0*(h1+h2+h3+h4)/(k*k*k*(ee*ee+yy*yy));
	
	//*  This part computes the first integral in equation (1).  It also
	// generates the KC approximated effective structure factor.*/
	
	pq=4.0*pi*cont*(sin(k*sigma/2.0)-0.5*k*sigma*cos(k*sigma/2.0));
	hint2=8.0*pi*pi*rho*cont*cont/(k*k*k*k*k*k)*(1.0-chi-k*p1+0.25*k*k*(s2+chi2));
	
	ka=k*(sigma/2.0);
	//
	hh=hint1+hint2;		// this is the model intensity
						//
	heff=1.0+hint1/hint2;
	ka2=ka*ka;
	//*
	//  heff is PY analytical solution for intensity divided by the 
	//   form factor.  happ is the KC approximated effective S(q)
	 
	 //*******************
	 //  add in the background then return the intensity value
	 
	 return(hh+bkg);	//scale, and add in the background
}

// scattering from a uniform sphere with a (Schulz) size distribution, bimodal population
// NO CROSS TERM IS ACCOUNTED FOR == DILUTE SOLUTION!!
//
double
BimodalSchulzSpheres(double dp[], double q)
{
	double x,pq;
	double scale,ravg,pd,bkg,rho,rhos;		//my local names
	double scale2,ravg2,pd2,rho2;		//my local names
	
	x= q;
	
	scale = dp[0];
	ravg = dp[1];
	pd = dp[2];
	rho = dp[3];
	scale2 = dp[4];
	ravg2 = dp[5];
	pd2 = dp[6];
	rho2 = dp[7];
	rhos = dp[8];
	bkg = dp[9];
	
	pq = SchulzSphere_Fn( scale,  ravg,  pd,  rho,  rhos, x);
	pq += SchulzSphere_Fn( scale2,  ravg2,  pd2,  rho2,  rhos, x);
	// add in the background
	pq += bkg;
	
	return (pq);
}

// scattering from a uniform sphere with a (Schulz) size distribution
//
double
SchulzSpheres(double dp[], double q)
{
	double x,pq;
	double scale,ravg,pd,bkg,rho,rhos;		//my local names
	
	x= q;
	
	scale = dp[0];
	ravg = dp[1];
	pd = dp[2];
	rho = dp[3];
	rhos = dp[4];
	bkg = dp[5];
	pq = SchulzSphere_Fn( scale,  ravg,  pd,  rho,  rhos, x);
	// add in the background
	pq += bkg;
	
	return(pq);
}

// calculates everything but the background
double
SchulzSphere_Fn(double scale, double ravg, double pd, double rho, double rhos, double x)
{
	double zp1,zp2,zp3,zp4,zp5,zp6,zp7,vpoly;
	double aa,at1,at2,rt1,rt2,rt3,t1,t2,t3;
	double v1,v2,v3,g1,pq,pi,delrho,zz;
	double i_zero,Rg2,zp8;
	
	pi = 4.0*atan(1.0);
	delrho = rho-rhos;
	zz = (1.0/pd)*(1.0/pd) - 1.0;   
	
	zp1 = zz + 1.0;
	zp2 = zz + 2.0;
	zp3 = zz + 3.0;
	zp4 = zz + 4.0;
	zp5 = zz + 5.0;
	zp6 = zz + 6.0;
	zp7 = zz + 7.0;
	//
	
	//small QR limit - use Guinier approx
	zp8 = zz+8.0;
	if(x*ravg < 0.1) {
		i_zero = scale*delrho*delrho*1.e8*4.*pi/3.*pow(ravg,3);
		i_zero *= zp6*zp5*zp4/zp1/zp1/zp1;		//6th moment / 3rd moment
		Rg2 = 3.*zp8*zp7/5./(zp1*zp1)*ravg*ravg;
		pq = i_zero*exp(-x*x*Rg2/3.);
		//pq += bkg;		//unlike the Igor code, the backgorund is added in the wrapper (above)
		return(pq);
	}
	//

	aa = (zz+1.0)/x/ravg;
	
	at1 = atan(1.0/aa);
	at2 = atan(2.0/aa);
	//
	//  calculations are performed to avoid  large # errors
	// - trick is to propogate the a^(z+7) term through the g1
	// 
	t1 = zp7*log10(aa) - zp1/2.0*log10(aa*aa+4.0);
	t2 = zp7*log10(aa) - zp3/2.0*log10(aa*aa+4.0);
	t3 = zp7*log10(aa) - zp2/2.0*log10(aa*aa+4.0);
	//	print t1,t2,t3
	rt1 = pow(10,t1);
	rt2 = pow(10,t2);
	rt3 = pow(10,t3);
	v1 = pow(aa,6) - rt1*cos(zp1*at2);
	v2 = zp1*zp2*( pow(aa,4) + rt2*cos(zp3*at2) );
	v3 = -2.0*zp1*rt3*sin(zp2*at2);
	g1 = (v1+v2+v3);
	
	pq = log10(g1) - 6.0*log10(zp1) + 6.0*log10(ravg);
	pq = pow(10,pq)*8.0*pi*pi*delrho*delrho;
	
	//
	// beta factor is not used here, but could be for the 
	// decoupling approximation
	// 
	//	g11 = g1
	//	gd = -zp7*log(aa)
	//	g1 = log(g11) + gd
	//                       
	//	t1 = zp1*at1
	//	t2 = zp2*at1
	//	g2 = sin( t1 ) - zp1/sqrt(aa*aa+1)*cos( t2 )
	//	g22 = g2*g2
	//	beta = zp1*log(aa) - zp1*log(aa*aa+1) - g1 + log(g22) 
	//	beta = 2*alog(beta)
	
	//re-normalize by the average volume
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*ravg*ravg*ravg;
	pq /= vpoly;
	//scale, convert to cm^-1
	pq *= scale * 1.0e8;
    
    return(pq);
}

// scattering from a uniform sphere with a rectangular size distribution
//
double
PolyRectSpheres(double dp[], double q)
{
	double pi,x;
	double scale,rad,pd,cont,bkg;		//my local names
	double inten,h1,qw,qr,width,sig,averad3,Rg2,slds,sld;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	scale = dp[0];
	rad = dp[1];		// radius (A)
	pd = dp[2];		//polydispersity of rectangular distribution
	slds = dp[3];
	sld = dp[4];
	cont = slds - sld;		// contrast (A^-2)
	bkg = dp[5];
	
	// as usual, poly = sig/ravg
	// for the rectangular distribution, sig = width/sqrt(3)
	// width is the HALF- WIDTH of the rectangular distrubution
	
	sig = pd*rad;
	width = sqrt(3.0)*sig;
	
	//x is the q-value
	qw = x*width;
	qr = x*rad;
	
	// as for the numerical inatabilities at low QR, the function is calculating the sines and cosines
	// just fine - the problem seems to be that the 
	// leading terms nearly cancel with the last term (the -6*qr... term), to within machine
	// precision - the difference is on the order of 10^-20
	// so just use the limiting Guiner value
	if(qr<0.1) {
		h1 = scale*cont*cont*1.e8*4.*pi/3.0*pow(rad,3);
		h1 *= 	(1. + 15.*pow(pd,2) + 27.*pow(pd,4) +27./7.*pow(pd,6) );				//6th moment
		h1 /= (1.+3.*pd*pd);	//3rd moment
		Rg2 = 3.0/5.0*rad*rad*( 1.+28.*pow(pd,2)+126.*pow(pd,4)+108.*pow(pd,6)+27.*pow(pd,8) );
		Rg2 /= (1.+15.*pow(pd,2)+27.*pow(pd,4)+27./7.*pow(pd,6));
		h1 *= exp(-1./3.*Rg2*x*x);
		h1 += bkg;
		return(h1);
	}
	
	// normal calculation
	h1 = -0.5*qw + qr*qr*qw + (qw*qw*qw)/3.0;
	h1 -= 5.0/2.0*cos(2.0*qr)*sin(qw)*cos(qw);
	h1 += 0.5*qr*qr*cos(2.0*qr)*sin(2.0*qw);
	h1 += 0.5*qw*qw*cos(2.0*qr)*sin(2.0*qw);
	h1 += qw*qr*sin(2.0*qr)*cos(2.0*qw);
	h1 += 3.0*qw*(cos(qr)*cos(qw))*(cos(qr)*cos(qw));
	h1+= 3.0*qw*(sin(qr)*sin(qw))*(sin(qr)*sin(qw));
	h1 -= 6.0*qr*cos(qr)*sin(qr)*cos(qw)*sin(qw);
	
	// calculate P(q) = <f^2>
	inten = 8.0*pi*pi*cont*cont/width/pow(x,7)*h1;
	
	// beta(q) would be calculated as 2/width/x/h1*h2*h2
	// with 
	// h2 = 2*sin(x*rad)*sin(x*width)-x*rad*cos(x*rad)*sin(x*width)-x*width*sin(x*rad)*cos(x*width)
	
	// normalize to the average volume
	// <R^3> = ravg^3*(1+3*pd^2)
	// or... "zf"  = (1 + 3*p^2), which will be greater than one
	
	averad3 =  rad*rad*rad*(1.0+3.0*pd*pd);
	inten /= 4.0*pi/3.0*averad3;
	//resacle to 1/cm
	inten *= 1.0e8;
	//scale the result
	inten *= scale;
	// then add in the background
	inten += bkg;
	
	return(inten);
}


// scattering from a uniform sphere with a Gaussian size distribution
//
double
GaussPolySphere(double dp[], double q)
{
	double pi,x;
	double scale,rad,pd,sig,rho,rhos,bkg,delrho;		//my local names
	double va,vb,zi,yy,summ,inten;
	int nord=20,ii;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	scale=dp[0];
	rad=dp[1];
	pd=dp[2];
	sig=pd*rad;
	rho=dp[3];
	rhos=dp[4];
	delrho=rho-rhos;
	bkg=dp[5];
	
	va = -4.0*sig + rad;
	if (va<0.0) {
		va=0.0;		//to avoid numerical error when  va<0 (-ve q-value)
	}
	vb = 4.0*sig +rad;
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss20Z[ii]*(vb-va) + vb + va )/2.0;
		// calculate sphere scattering
		//return(3*(sin(qr) - qr*cos(qr))/(qr*qr*qr)); pass qr
		yy = F_func(x*zi)*(4.0*pi/3.0*zi*zi*zi)*delrho;
		yy *= yy;
		yy *= Gauss20Wt[ii] *  Gauss_distr(sig,rad,zi);
		
		summ += yy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	inten = (vb-va)/2.0*summ;
	
	//re-normalize by polydisperse sphere volume
	inten /= (4.0*pi/3.0*rad*rad*rad)*(1.0+3.0*pd*pd);
	
	inten *= 1.0e8;
	inten *= scale;
	inten += bkg;
	
    return(inten);	//scale, and add in the background
}

// scattering from a uniform sphere with a LogNormal size distribution
//
double
LogNormalPolySphere(double dp[], double q)
{
	double pi,x;
	double scale,rad,sig,rho,rhos,bkg,delrho,mu,r3;		//my local names
	double va,vb,zi,yy,summ,inten;
	int nord=76,ii;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	scale=dp[0];
	rad=dp[1];		//rad is the median radius
	mu = log(dp[1]);
	sig=dp[2];
	rho=dp[3];
	rhos=dp[4];
	delrho=rho-rhos;
	bkg=dp[5];
	
	va = -3.5*sig + mu;
	va = exp(va);
	if (va<0.0) {
		va=0.0;		//to avoid numerical error when  va<0 (-ve q-value)
	}
	vb = 3.5*sig*(1.0+sig) +mu;
	vb = exp(vb);
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss76Z[ii]*(vb-va) + vb + va )/2.0;
		// calculate sphere scattering
		//return(3*(sin(qr) - qr*cos(qr))/(qr*qr*qr)); pass qr
		yy = F_func(x*zi)*(4.0*pi/3.0*zi*zi*zi)*delrho;
		yy *= yy;
		yy *= Gauss76Wt[ii] *  LogNormal_distr(sig,mu,zi);
		
		summ += yy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	inten = (vb-va)/2.0*summ;
	
	//re-normalize by polydisperse sphere volume
	r3 = exp(3.0*mu + 9.0/2.0*sig*sig);		// <R^3> directly
	inten /= (4.0*pi/3.0*r3);		//polydisperse volume
	
	inten *= 1.0e8;
	inten *= scale;
	inten += bkg;
	
	return(inten);
}

/*
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
*/

// scattering from a core shell sphere with a (Schulz) polydisperse core and constant ratio (shell thickness)/(core radius)
// - the polydispersity is of the WHOLE sphere
//
double
PolyCoreShellRatio(double dp[], double q)
{
	double pi,x;
	double scale,corrad,thick,shlrad,pp,drho1,drho2,sig,zz,bkg;		//my local names
	double sld1,sld2,sld3,zp1,zp2,zp3,vpoly;
	double pi43,c1,c2,form,volume,arg1,arg2;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	scale = dp[0];
	corrad = dp[1];
	thick = dp[2];
	sig = dp[3];
	sld1 = dp[4];
	sld2 = dp[5];
	sld3 = dp[6];
	bkg = dp[7];
	
	zz = (1.0/sig)*(1.0/sig) - 1.0;   
	shlrad = corrad + thick;
	drho1 = sld1-sld2;		//core-shell
	drho2 = sld2-sld3;		//shell-solvent
	zp1 = zz + 1.;
	zp2 = zz + 2.;
	zp3 = zz + 3.;
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*pow((corrad+thick),3);
	
	// the beta factor is not calculated
 	// the calculated form factor <f^2> has units [length^2]
 	// and must be multiplied by number density [l^-3] and the correct unit
 	// conversion to get to absolute scale
	
	pi43=4.0/3.0*pi;
 	pp=corrad/shlrad;
 	volume=pi43*shlrad*shlrad*shlrad;
 	c1=drho1*volume;
 	c2=drho2*volume;
	
	arg1 = x*shlrad*pp;
	arg2 = x*shlrad;
	
	form=pow(pp,6)*c1*c1*fnt2(arg1,zz);
	form += c2*c2*fnt2(arg2,zz);
	form += 2.0*c1*c2*fnt3(arg2,pp,zz);
	
	//convert the result to [cm^-1]
	
	//scale the result
	// - divide by the polydisperse volume, mult by 10^8
	form  /= vpoly;
	form *= 1.0e8;
	form *= scale;
	
	//add in the background
	form += bkg;
	
	return(form);
}

//cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
//c
//c      function fnt2(y,z)
//c
double
fnt2(double yy, double zz)
{
	double z1,z2,z3,u,ww,term1,term2,term3,ans;
	
	z1=zz+1.0;
	z2=zz+2.0;
	z3=zz+3.0;
	u=yy/z1;
	ww=atan(2.0*u);
	term1=cos(z1*ww)/pow((1.0+4.0*u*u),(z1/2.0));
	term2=2.0*yy*sin(z2*ww)/pow((1.0+4.0*u*u),(z2/2.0));
	term3=1.0+cos(z3*ww)/pow((1.0+4.0*u*u),(z3/2.0));
	ans=(4.50/z1/pow(yy,6))*(z1*(1.0-term1-term2)+yy*yy*z2*term3);
	
	return(ans);
}

//cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
//c
//c      function fnt3(y,p,z)
//c
double
fnt3(double yy, double pp, double zz)
{     	
	double z1,z2,z3,yp,yn,up,un,vp,vn,term1,term2,term3,term4,term5,term6,ans;
	
	z1=zz+1.0;
	z2=zz+2.0;
	z3=zz+3.0;
	yp=(1.0+pp)*yy;
	yn=(1.0-pp)*yy;
	up=yp/z1;
	un=yn/z1;
	vp=atan(up);
	vn=atan(un);
	term1=cos(z1*vn)/pow((1.0+un*un),(z1/2.0));
	term2=cos(z1*vp)/pow((1.0+up*up),(z1/2.0));
	term3=cos(z3*vn)/pow((1.0+un*un),(z3/2.0));
	term4=cos(z3*vp)/pow((1.0+up*up),(z3/2.0));
	term5=yn*sin(z2*vn)/pow((1.0+un*un),(z2/2.0));
	term6=yp*sin(z2*vp)/pow((1.0+up*up),(z2/2.0));
	ans=4.5/z1/pow(yy,6);
	ans *=(z1*(term1-term2)+yy*yy*pp*z2*(term3+term4)+z1*(term5-term6));
	
	return(ans);
}

// scattering from a a binary population of hard spheres, 3 partial structure factors
// are properly accounted for...
//	 Input (fitting) variables are:
//	larger sphere radius(angstroms) = guess[0]
// 	smaller sphere radius (A) = w[1]
//	number fraction of larger spheres = guess[2]
//	total volume fraction of spheres = guess[3]
//	size ratio, alpha(0<a<1) = derived
//	SLD(A-2) of larger particle = guess[4]
//	SLD(A-2) of smaller particle = guess[5]
//	SLD(A-2) of the solvent = guess[6]
//	background = guess[7]
double
BinaryHS(double dp[], double q)
{
	double x,pi;
	double r2,r1,nf2,phi,aa,rho2,rho1,rhos,inten,bgd;		//my local names
	double psf11,psf12,psf22;
	double phi1,phi2,phr,a3;
	double v1,v2,n1,n2,qr1,qr2,b1,b2,sc1,sc2;
	int err;
	
	pi = 4.0*atan(1.0);
	x= q;
	r2 = dp[0];
	r1 = dp[1];
	phi2 = dp[2];
	phi1 = dp[3];
	rho2 = dp[4];
	rho1 = dp[5];
	rhos = dp[6];
	bgd = dp[7];
	
	
	phi = phi1 + phi2;
	aa = r1/r2;
	//calculate the number fraction of larger spheres (eqn 2 in reference)
	a3=aa*aa*aa;
	phr=phi2/phi;
	nf2 = phr*a3/(1.0-phr+phr*a3);
	// calculate the PSF's here
	err = ashcroft(x,r2,nf2,aa,phi,&psf11,&psf22,&psf12);
	
	// /* do form factor calculations  */
	
	v1 = 4.0*pi/3.0*r1*r1*r1;
	v2 = 4.0*pi/3.0*r2*r2*r2;
	
	n1 = phi1/v1;
	n2 = phi2/v2;
	
	qr1 = r1*x;
	qr2 = r2*x;

	if (qr1 == 0){
		sc1 = 1.0/3.0;
	}else{
		sc1 = (sin(qr1)-qr1*cos(qr1))/qr1/qr1/qr1;
	}
	if (qr2 == 0){
		sc2 = 1.0/3.0;
	}else{
		sc2 = (sin(qr2)-qr2*cos(qr2))/qr2/qr2/qr2;
	}
	b1 = r1*r1*r1*(rho1-rhos)*4.0*pi*sc1;
	b2 = r2*r2*r2*(rho2-rhos)*4.0*pi*sc2;
	inten = n1*b1*b1*psf11;
	inten += sqrt(n1*n2)*2.0*b1*b2*psf12;
	inten += n2*b2*b2*psf22;
	///* convert I(1/A) to (1/cm)  */
	inten *= 1.0e8;
	
	inten += bgd;
	
	return(inten);
}

double
BinaryHS_PSF11(double dp[], double q)
{
	double x,pi;
	double r2,r1,nf2,phi,aa,rho2,rho1,rhos,bgd;		//my local names
	double psf11,psf12,psf22;
	double phi1,phi2,phr,a3;
	int err;
	
	pi = 4.0*atan(1.0);
	x= q;
	r2 = dp[0];
	r1 = dp[1];
	phi2 = dp[2];
	phi1 = dp[3];
	rho2 = dp[4];
	rho1 = dp[5];
	rhos = dp[6];
	bgd = dp[7];
	phi = phi1 + phi2;
	aa = r1/r2;
	//calculate the number fraction of larger spheres (eqn 2 in reference)
	a3=aa*aa*aa;
	phr=phi2/phi;
	nf2 = phr*a3/(1.0-phr+phr*a3);
	// calculate the PSF's here
	err = ashcroft(x,r2,nf2,aa,phi,&psf11,&psf22,&psf12);
	
    return(psf11);	//scale, and add in the background
}

double
BinaryHS_PSF12(double dp[], double q)
{
	double x,pi;
	double r2,r1,nf2,phi,aa,rho2,rho1,rhos,bgd;		//my local names
	double psf11,psf12,psf22;
	double phi1,phi2,phr,a3;
	int err;
	
	pi = 4.0*atan(1.0);
	x= q;
	r2 = dp[0];
	r1 = dp[1];
	phi2 = dp[2];
	phi1 = dp[3];
	rho2 = dp[4];
	rho1 = dp[5];
	rhos = dp[6];
	bgd = dp[7];
	phi = phi1 + phi2;
	aa = r1/r2;
	//calculate the number fraction of larger spheres (eqn 2 in reference)
	a3=aa*aa*aa;
	phr=phi2/phi;
	nf2 = phr*a3/(1.0-phr+phr*a3);
	// calculate the PSF's here
	err = ashcroft(x,r2,nf2,aa,phi,&psf11,&psf22,&psf12);
	
    return(psf12);	//scale, and add in the background
}

double
BinaryHS_PSF22(double dp[], double q)
{
	double x,pi;
	double r2,r1,nf2,phi,aa,rho2,rho1,rhos,bgd;		//my local names
	double psf11,psf12,psf22;
	double phi1,phi2,phr,a3;
	int err;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	r2 = dp[0];
	r1 = dp[1];
	phi2 = dp[2];
	phi1 = dp[3];
	rho2 = dp[4];
	rho1 = dp[5];
	rhos = dp[6];
	bgd = dp[7];
	phi = phi1 + phi2;
	aa = r1/r2;
	//calculate the number fraction of larger spheres (eqn 2 in reference)
	a3=aa*aa*aa;
	phr=phi2/phi;
	nf2 = phr*a3/(1.0-phr+phr*a3);
	// calculate the PSF's here
	err = ashcroft(x,r2,nf2,aa,phi,&psf11,&psf22,&psf12);
	
    return(psf22);	//scale, and add in the background
}

int
ashcroft(double qval, double r2, double nf2, double aa, double phi, double *s11, double *s22, double *s12)
{
	//	variable qval,r2,nf2,aa,phi,&s11,&s22,&s12
	
	//   calculate constant terms
	double s1,s2,v,a3,v1,v2,g11,g12,g22,wmv,wmv3,wmv4;
	double a1,a2i,a2,b1,b2,b12,gm1,gm12;
	double err=0.0,yy,ay,ay2,ay3,t1,t2,t3,f11,y2,y3,tt1,tt2,tt3;
	double c11,c22,c12,f12,f22,ttt1,ttt2,ttt3,ttt4,yl,y13;
	double t21,t22,t23,t31,t32,t33,t41,t42,yl3,wma3,y1;
	
	s2 = 2.0*r2;
	s1 = aa*s2;
	v = phi;
	a3 = aa*aa*aa;
	v1=((1.-nf2)*a3/(nf2+(1.-nf2)*a3))*v;
	v2=(nf2/(nf2+(1.-nf2)*a3))*v;
	g11=((1.+.5*v)+1.5*v2*(aa-1.))/(1.-v)/(1.-v);
	g22=((1.+.5*v)+1.5*v1*(1./aa-1.))/(1.-v)/(1.-v);
	g12=((1.+.5*v)+1.5*(1.-aa)*(v1-v2)/(1.+aa))/(1.-v)/(1.-v);
	wmv = 1/(1.-v);
	wmv3 = wmv*wmv*wmv;
	wmv4 = wmv*wmv3;
	a1=3.*wmv4*((v1+a3*v2)*(1.+v+v*v)-3.*v1*v2*(1.-aa)*(1.-aa)*(1.+v1+aa*(1.+v2))) + ((v1+a3*v2)*(1.+2.*v)+(1.+v+v*v)-3.*v1*v2*(1.-aa)*(1.-aa)-3.*v2*(1.-aa)*(1.-aa)*(1.+v1+aa*(1.+v2)))*wmv3;
	a2i=((v1+a3*v2)*(1.+v+v*v)-3.*v1*v2*(1.-aa)*(1.-aa)*(1.+v1+aa*(1.+v2)))*3*wmv4 + ((v1+a3*v2)*(1.+2.*v)+a3*(1.+v+v*v)-3.*v1*v2*(1.-aa)*(1.-aa)*aa-3.*v1*(1.-aa)*(1.-aa)*(1.+v1+aa*(1.+v2)))*wmv3;
	a2=a2i/a3;
	b1=-6.*(v1*g11*g11+.25*v2*(1.+aa)*(1.+aa)*aa*g12*g12);
	b2=-6.*(v2*g22*g22+.25*v1/a3*(1.+aa)*(1.+aa)*g12*g12);
	b12=-3.*aa*(1.+aa)*(v1*g11/aa/aa+v2*g22)*g12;
	gm1=(v1*a1+a3*v2*a2)*.5;
	gm12=2.*gm1*(1.-aa)/aa;
	//c  
	//c   calculate the direct correlation functions and print results
	//c
	//	do 20 j=1,npts
	
	yy=qval*s2;
	//c   calculate direct correlation functions
	//c   ----c11
	ay=aa*yy;
	ay2 = ay*ay;
	ay3 = ay*ay*ay;
	t1=a1*(sin(ay)-ay*cos(ay));
	t2=b1*(2.*ay*sin(ay)-(ay2-2.)*cos(ay)-2.)/ay;
	t3=gm1*((4.*ay*ay2-24.*ay)*sin(ay)-(ay2*ay2-12.*ay2+24.)*cos(ay)+24.)/ay3;
	f11=24.*v1*(t1+t2+t3)/ay3;
	
	//c ------c22
	y2=yy*yy;
	y3=yy*y2;
	tt1=a2*(sin(yy)-yy*cos(yy));
	tt2=b2*(2.*yy*sin(yy)-(y2-2.)*cos(yy)-2.)/yy;
	tt3=gm1*((4.*y3-24.*yy)*sin(yy)-(y2*y2-12.*y2+24.)*cos(yy)+24.)/ay3;
	f22=24.*v2*(tt1+tt2+tt3)/y3;
	
	//c   -----c12
	yl=.5*yy*(1.-aa);
	yl3=yl*yl*yl;
	wma3 = (1.-aa)*(1.-aa)*(1.-aa);
	y1=aa*yy;
	y13 = y1*y1*y1;
	ttt1=3.*wma3*v*sqrt(nf2)*sqrt(1.-nf2)*a1*(sin(yl)-yl*cos(yl))/((nf2+(1.-nf2)*a3)*yl3);
	t21=b12*(2.*y1*cos(y1)+(y1*y1-2.)*sin(y1));
	t22=gm12*((3.*y1*y1-6.)*cos(y1)+(y1*y1*y1-6.*y1)*sin(y1)+6.)/y1;
	t23=gm1*((4.*y13-24.*y1)*cos(y1)+(y13*y1-12.*y1*y1+24.)*sin(y1))/(y1*y1);
	t31=b12*(2.*y1*sin(y1)-(y1*y1-2.)*cos(y1)-2.);
	t32=gm12*((3.*y1*y1-6.)*sin(y1)-(y1*y1*y1-6.*y1)*cos(y1))/y1;
  	t33=gm1*((4.*y13-24.*y1)*sin(y1)-(y13*y1-12.*y1*y1+24.)*cos(y1)+24.)/(y1*y1);
	t41=cos(yl)*((sin(y1)-y1*cos(y1))/(y1*y1) + (1.-aa)/(2.*aa)*(1.-cos(y1))/y1);
	t42=sin(yl)*((cos(y1)+y1*sin(y1)-1.)/(y1*y1) + (1.-aa)/(2.*aa)*sin(y1)/y1);
	ttt2=sin(yl)*(t21+t22+t23)/(y13*y1);
	ttt3=cos(yl)*(t31+t32+t33)/(y13*y1);
	ttt4=a1*(t41+t42)/y1;
	f12=ttt1+24.*v*sqrt(nf2)*sqrt(1.-nf2)*a3*(ttt2+ttt3+ttt4)/(nf2+(1.-nf2)*a3);
	
	c11=f11;
	c22=f22;
	c12=f12;
	*s11=1./(1.+c11-(c12)*c12/(1.+c22));
	*s22=1./(1.+c22-(c12)*c12/(1.+c11)); 
	*s12=-c12/((1.+c11)*(1.+c22)-(c12)*(c12));   
	
	return(err);
}



/*
 // calculates the scattering from a spherical particle made up of a core (aqueous) surrounded
 // by N spherical layers, each of which is a PAIR of shells, solvent + surfactant since there
 //must always be a surfactant layer on the outside
 //
 // bragg peaks arise naturally from the periodicity of the sample
 // resolution smeared version gives he most appropriate view of the model
 
	Warning:
 The call to WaveData() below returns a pointer to the middle
 of an unlocked Macintosh handle. In the unlikely event that your
 calculations could cause memory to move, you should copy the coefficient
 values to local variables or an array before such operations.
 */
double
MultiShell(double dp[], double q)
{
	double x;
	double scale,rcore,tw,ts,rhocore,rhoshel,num,bkg;		//my local names
	int ii;
	double fval,voli,ri,sldi;
	double pi;
	
	pi = 4.0*atan(1.0);
	
	x= q;
	scale = dp[0];
	rcore = dp[1];
	ts = dp[2];
	tw = dp[3];
	rhocore = dp[4];
	rhoshel = dp[5];
	num = dp[6];
	bkg = dp[7];
	
	//calculate with a loop, two shells at a time
	
	ii=0;
	fval=0.0;
	
	do {
		ri = rcore + (double)ii*ts + (double)ii*tw;
		voli = 4.0*pi/3.0*ri*ri*ri;
		sldi = rhocore-rhoshel;
		fval += voli*sldi*F_func(ri*x);
		ri += ts;
		voli = 4.0*pi/3.0*ri*ri*ri;
		sldi = rhoshel-rhocore;
		fval += voli*sldi*F_func(ri*x);
		ii+=1;		//do 2 layers at a time
	} while(ii<=num-1);  //change to make 0 < num < 2 correspond to unilamellar vesicles (C. Glinka, 11/24/03)
	
	fval *= fval;		//square it
	fval /= voli;		//normalize by the overall volume
	fval *= scale*1.0e8;
	fval += bkg;
	
	return(fval);
}

/*
 // calculates the scattering from a POLYDISPERSE spherical particle made up of a core (aqueous) surrounded
 // by N spherical layers, each of which is a PAIR of shells, solvent + surfactant since there
 //must always be a surfactant layer on the outside
 //
 // bragg peaks arise naturally from the periodicity of the sample
 // resolution smeared version gives he most appropriate view of the model
 //
 // Polydispersity is of the total (outer) radius. This is converted into a distribution of MLV's
 // with integer numbers of layers, with a minimum of one layer... a vesicle... depending
 // on the parameters, the "distribution" of MLV's that is used may be truncated
 //
	Warning:
 The call to WaveData() below returns a pointer to the middle
 of an unlocked Macintosh handle. In the unlikely event that your
 calculations could cause memory to move, you should copy the coefficient
 values to local variables or an array before such operations.
 */
double
PolyMultiShell(double dp[], double q)
{
	double x;
	double scale,rcore,tw,ts,rhocore,rhoshel,bkg;		//my local names
	int ii,minPairs,maxPairs,first;
	double fval,ri,pi;
	double avg,pd,zz,lo,hi,r1,r2,d1,d2,distr;
	
	pi = 4.0*atan(1.0);	
	x= q;
	
	scale = dp[0];
	avg = dp[1];		// average (total) outer radius
	pd = dp[2];
	rcore = dp[3];
	ts = dp[4];
	tw = dp[5];
	rhocore = dp[6];
	rhoshel = dp[7];
	bkg = dp[8];
	
	zz = (1.0/pd)*(1.0/pd)-1.0;
	
	//max radius set to be 5 std deviations past mean
	hi = avg + pd*avg*5.0;
	lo = avg - pd*avg*5.0;
	
	maxPairs = trunc( (hi-rcore+tw)/(ts+tw) );
	minPairs = trunc( (lo-rcore+tw)/(ts+tw) );
	minPairs = (minPairs < 1) ? 1 : minPairs;	// need a minimum of one
	
	ii=minPairs;
	fval=0.0;
	d1 = 0.0;
	d2 = 0.0;
	r1 = 0.0;
	r2 = 0.0;
	distr = 0.0;
	first = 1.0;
	do {
		//make the current values old
		r1 = r2;
		d1 = d2;
		
		ri = (double)ii*(ts+tw) - tw + rcore;
		fval += SchulzPoint(ri,avg,zz) * MultiShellGuts(x, rcore, ts, tw, rhocore, rhoshel, ii) * (4*pi/3*ri*ri*ri);
		// get a running integration of the fraction of the distribution used, but not the first time
		r2 = ri;
		d2 = SchulzPoint(ri,avg,zz);
		if( !first ) {
			distr += 0.5*(d1+d2)*(r2-r1);		//cheap trapezoidal integration
		}
		ii+=1;
		first = 0;
	} while(ii<=maxPairs);
	
	fval /= 4.0*pi/3.0*avg*avg*avg;		//normalize by the overall volume
	fval /= distr;
	fval *= scale;
	fval += bkg;
	
	return(fval);
}

double
MultiShellGuts(double x,double rcore,double ts,double tw,double rhocore,double rhoshel,int num) {
	
    double ri,sldi,fval,voli,pi;
    int ii;
    
	pi = 4.0*atan(1.0);
    ii=0;
    fval=0.0;
    
    do {
        ri = rcore + (double)ii*ts + (double)ii*tw;
        voli = 4.0*pi/3.0*ri*ri*ri;
        sldi = rhocore-rhoshel;
        fval += voli*sldi*F_func(ri*x);
        ri += ts;
        voli = 4.0*pi/3.0*ri*ri*ri;
        sldi = rhoshel-rhocore;
        fval += voli*sldi*F_func(ri*x);
        ii+=1;		//do 2 layers at a time
    } while(ii<=num-1);  //change to make 0 < num < 2 correspond to unilamellar vesicles (C. Glinka, 11/24/03)
    
    fval *= fval;
    fval /= voli;
    fval *= 1.0e8;
    
    return(fval);	// this result still needs to be multiplied by scale and have background added
}

/*
static double
SchulzPoint(double x, double avg, double zz) {
	
    double dr;
    
    dr = zz*log(x) - gammln(zz+1.0)+(zz+1.0)*log((zz+1.0)/avg)-(x/avg*(zz+1.0));
    return (exp(dr));
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
*/

double
F_func(double qr) {
	double sc;
	if (qr == 0.0){
		sc = 1.0;
	}else{
		sc=(3.0*(sin(qr) - qr*cos(qr))/(qr*qr*qr));
	}
	return sc;
}

double
OneShell(double dp[], double q)
{
	// variables are:
	//[0] scale factor
	//[1] radius of core [�]
	//[2] SLD of the core	[�-2]
	//[3] thickness of the shell	[�]
	//[4] SLD of the shell
	//[5] SLD of the solvent
	//[6] background	[cm-1]
	
	double x,pi;
	double scale,rcore,thick,rhocore,rhoshel,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	scale = dp[0];
	rcore = dp[1];
	rhocore = dp[2];
	thick = dp[3];
	rhoshel = dp[4];
	rhosolv = dp[5];
	bkg = dp[6];
	
	// core first, then add in shell
	qr=x*rcore;
	contr = rhocore-rhoshel;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell
	qr=x*(rcore+thick);
	contr = rhoshel-rhosolv;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*pow((rcore+thick),3);
	f += vol*bes*contr;
	
	// normalize to particle volume and rescale from [�-1] to [cm-1]
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}

double
TwoShell(double dp[], double q)
{
	// variables are:
	//[0] scale factor
	//[1] radius of core [�]
	//[2] SLD of the core	[�-2]
	//[3] thickness of shell 1 [�]
	//[4] SLD of shell 1
	//[5] thickness of shell 2 [�]
	//[6] SLD of shell 2
	//[7] SLD of the solvent
	//[8] background	[cm-1]
	
	double x,pi;
	double scale,rcore,thick1,rhocore,rhoshel1,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	double rhoshel2,thick2;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	scale = dp[0];
	rcore = dp[1];
	rhocore = dp[2];
	thick1 = dp[3];
	rhoshel1 = dp[4];
	thick2 = dp[5];
	rhoshel2 = dp[6];	
	rhosolv = dp[7];
	bkg = dp[8];
		// core first, then add in shells
	qr=x*rcore;
	contr = rhocore-rhoshel1;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell (1)
	qr=x*(rcore+thick1);
	contr = rhoshel1-rhoshel2;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1)*(rcore+thick1)*(rcore+thick1);
	f += vol*bes*contr;
	//now the shell (2)
	qr=x*(rcore+thick1+thick2);
	contr = rhoshel2-rhosolv;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2)*(rcore+thick1+thick2)*(rcore+thick1+thick2);
	f += vol*bes*contr;
	
		
	// normalize to particle volume and rescale from [�-1] to [cm-1]
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}

double
ThreeShell(double dp[], double q)
{
	// variables are:
	//[0] scale factor
	//[1] radius of core [�]
	//[2] SLD of the core	[�-2]
	//[3] thickness of shell 1 [�]
	//[4] SLD of shell 1
	//[5] thickness of shell 2 [�]
	//[6] SLD of shell 2
	//[7] thickness of shell 3
	//[8] SLD of shell 3
	//[9] SLD of solvent
	//[10] background	[cm-1]
	
	double x,pi;
	double scale,rcore,thick1,rhocore,rhoshel1,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	double rhoshel2,thick2,rhoshel3,thick3;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	scale = dp[0];
	rcore = dp[1];
	rhocore = dp[2];
	thick1 = dp[3];
	rhoshel1 = dp[4];
	thick2 = dp[5];
	rhoshel2 = dp[6];	
	thick3 = dp[7];
	rhoshel3 = dp[8];	
	rhosolv = dp[9];
	bkg = dp[10];
	
		// core first, then add in shells
	qr=x*rcore;
	contr = rhocore-rhoshel1;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell (1)
	qr=x*(rcore+thick1);
	contr = rhoshel1-rhoshel2;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1)*(rcore+thick1)*(rcore+thick1);
	f += vol*bes*contr;
	//now the shell (2)
	qr=x*(rcore+thick1+thick2);
	contr = rhoshel2-rhoshel3;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2)*(rcore+thick1+thick2)*(rcore+thick1+thick2);
	f += vol*bes*contr;
	//now the shell (3)
	qr=x*(rcore+thick1+thick2+thick3);
	contr = rhoshel3-rhosolv;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2+thick3)*(rcore+thick1+thick2+thick3)*(rcore+thick1+thick2+thick3);
	f += vol*bes*contr;
		
	// normalize to particle volume and rescale from [�-1] to [cm-1]
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}

double
FourShell(double dp[], double q)
{
	// variables are:
	//[0] scale factor
	//[1] radius of core [�]
	//[2] SLD of the core	[�-2]
	//[3] thickness of shell 1 [�]
	//[4] SLD of shell 1
	//[5] thickness of shell 2 [�]
	//[6] SLD of shell 2
	//[7] thickness of shell 3
	//[8] SLD of shell 3
	//[9] thickness of shell 3
	//[10] SLD of shell 3
	//[11] SLD of solvent
	//[12] background	[cm-1]
	
	double x,pi;
	double scale,rcore,thick1,rhocore,rhoshel1,rhosolv,bkg;		//my local names
	double bes,f,vol,qr,contr,f2;
	double rhoshel2,thick2,rhoshel3,thick3,rhoshel4,thick4;
	
	pi = 4.0*atan(1.0);
	x=q;
	
	scale = dp[0];
	rcore = dp[1];
	rhocore = dp[2];
	thick1 = dp[3];
	rhoshel1 = dp[4];
	thick2 = dp[5];
	rhoshel2 = dp[6];	
	thick3 = dp[7];
	rhoshel3 = dp[8];
	thick4 = dp[9];
	rhoshel4 = dp[10];	
	rhosolv = dp[11];
	bkg = dp[12];
	
		// core first, then add in shells
	qr=x*rcore;
	contr = rhocore-rhoshel1;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*rcore*rcore*rcore;
	f = vol*bes*contr;
	//now the shell (1)
	qr=x*(rcore+thick1);
	contr = rhoshel1-rhoshel2;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1)*(rcore+thick1)*(rcore+thick1);
	f += vol*bes*contr;
	//now the shell (2)
	qr=x*(rcore+thick1+thick2);
	contr = rhoshel2-rhoshel3;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2)*(rcore+thick1+thick2)*(rcore+thick1+thick2);
	f += vol*bes*contr;
	//now the shell (3)
	qr=x*(rcore+thick1+thick2+thick3);
	contr = rhoshel3-rhoshel4;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2+thick3)*(rcore+thick1+thick2+thick3)*(rcore+thick1+thick2+thick3);
	f += vol*bes*contr;
	//now the shell (4)
	qr=x*(rcore+thick1+thick2+thick3+thick4);
	contr = rhoshel4-rhosolv;
	if(qr == 0){
		bes = 1.0;
	}else{
		bes = 3.0*(sin(qr)-qr*cos(qr))/(qr*qr*qr);
	}
	vol = 4.0*pi/3.0*(rcore+thick1+thick2+thick3+thick4)*(rcore+thick1+thick2+thick3+thick4)*(rcore+thick1+thick2+thick3+thick4);
	f += vol*bes*contr;
	
		
	// normalize to particle volume and rescale from [�-1] to [cm-1]
	f2 = f*f/vol*1.0e8;
	
	//scale if desired
	f2 *= scale;
	// then add in the background
	f2 += bkg;
	
	return(f2);
}

double
PolyOneShell(double dp[], double x)
{
	double scale,rcore,thick,rhocore,rhoshel,rhosolv,bkg,pd,zz;		//my local names
	double va,vb,summ,yyy,zi;
	double answer,zp1,zp2,zp3,vpoly,range,temp_1sf[7],pi;
	int nord=76,ii;
	
	pi = 4.0*atan(1.0);
	
	scale = dp[0];
	rcore = dp[1];
	pd = dp[2];
	rhocore = dp[3];
	thick = dp[4];
	rhoshel = dp[5];
	rhosolv = dp[6];
	bkg = dp[7];
		
	zz = (1.0/pd)*(1.0/pd)-1.0;		//polydispersity of the core only
	
	range = 8.0;			//std deviations for the integration
	va = rcore*(1.0-range*pd);
	if (va<0.0) {
		va=0.0;		//otherwise numerical error when pd >= 0.3, making a<0
	}
	if (pd>0.3) {
		range = range + (pd-0.3)*18.0;		//stretch upper range to account for skewed tail
	}
	vb = rcore*(1.0+range*pd);		// is this far enough past avg radius?
	
	//temp set scale=1 and bkg=0 for quadrature calc
	temp_1sf[0] = 1.0;
	temp_1sf[1] = dp[1];	//the core radius will be changed in the loop
	temp_1sf[2] = dp[3];
	temp_1sf[3] = dp[4];
	temp_1sf[4] = dp[5];
	temp_1sf[5] = dp[6];
	temp_1sf[6] = 0.0;
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss76Z[ii]*(vb-va) + vb + va )/2.0;
		temp_1sf[1] = zi;
		yyy = Gauss76Wt[ii] * SchulzPoint(zi,rcore,zz) * OneShell(temp_1sf,x);
		//un-normalize by volume
		yyy *= 4.0*pi/3.0*pow((zi+thick),3);
		summ += yyy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	answer = (vb-va)/2.0*summ;
   	
	//re-normalize by the average volume
	zp1 = zz + 1.0;
	zp2 = zz + 2.0;
	zp3 = zz + 3.0;
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*pow((rcore+thick),3);
	answer /= vpoly;
//scale
	answer *= scale;
// add in the background
	answer += bkg;
		
    return(answer);
}

double
PolyTwoShell(double dp[], double x)
{
	double scale,rcore,rhocore,rhosolv,bkg,pd,zz;		//my local names
	double va,vb,summ,yyy,zi;
	double answer,zp1,zp2,zp3,vpoly,range,temp_2sf[9],pi;
	int nord=76,ii;
	double thick1,thick2;
	double rhoshel1,rhoshel2;
	
	scale = dp[0];
	rcore = dp[1];
	pd = dp[2];
	rhocore = dp[3];
	thick1 = dp[4];
	rhoshel1 = dp[5];
	thick2 = dp[6];
	rhoshel2 = dp[7];
	rhosolv = dp[8];
	bkg = dp[9];
	
	pi = 4.0*atan(1.0);
		
	zz = (1.0/pd)*(1.0/pd)-1.0;		//polydispersity of the core only
	
	range = 8.0;			//std deviations for the integration
	va = rcore*(1.0-range*pd);
	if (va<0.0) {
		va=0.0;		//otherwise numerical error when pd >= 0.3, making a<0
	}
	if (pd>0.3) {
		range = range + (pd-0.3)*18.0;		//stretch upper range to account for skewed tail
	}
	vb = rcore*(1.0+range*pd);		// is this far enough past avg radius?
	
	//temp set scale=1 and bkg=0 for quadrature calc
	temp_2sf[0] = 1.0;
	temp_2sf[1] = dp[1];		//the core radius will be changed in the loop
	temp_2sf[2] = dp[3];
	temp_2sf[3] = dp[4];
	temp_2sf[4] = dp[5];
	temp_2sf[5] = dp[6];
	temp_2sf[6] = dp[7];
	temp_2sf[7] = dp[8];
	temp_2sf[8] = 0.0;
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss76Z[ii]*(vb-va) + vb + va )/2.0;
		temp_2sf[1] = zi;
		yyy = Gauss76Wt[ii] * SchulzPoint(zi,rcore,zz) * TwoShell(temp_2sf,x);
		//un-normalize by volume
		yyy *= 4.0*pi/3.0*pow((zi+thick1+thick2),3);
		summ += yyy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	answer = (vb-va)/2.0*summ;
   	
	//re-normalize by the average volume
	zp1 = zz + 1.0;
	zp2 = zz + 2.0;
	zp3 = zz + 3.0;
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*pow((rcore+thick1+thick2),3);
	answer /= vpoly;
//scale
	answer *= scale;
// add in the background
	answer += bkg;
		
    return(answer);
}

double
PolyThreeShell(double dp[], double x)
{
	double scale,rcore,rhocore,rhosolv,bkg,pd,zz;		//my local names
	double va,vb,summ,yyy,zi;
	double answer,zp1,zp2,zp3,vpoly,range,temp_3sf[11],pi;
	int nord=76,ii;
	double thick1,thick2,thick3;
	double rhoshel1,rhoshel2,rhoshel3;
	
	scale = dp[0];
	rcore = dp[1];
	pd = dp[2];
	rhocore = dp[3];
	thick1 = dp[4];
	rhoshel1 = dp[5];
	thick2 = dp[6];
	rhoshel2 = dp[7];
	thick3 = dp[8];
	rhoshel3 = dp[9];
	rhosolv = dp[10];
	bkg = dp[11];
	
	pi = 4.0*atan(1.0);
		
	zz = (1.0/pd)*(1.0/pd)-1.0;		//polydispersity of the core only
	
	range = 8.0;			//std deviations for the integration
	va = rcore*(1.0-range*pd);
	if (va<0) {
		va=0;		//otherwise numerical error when pd >= 0.3, making a<0
	}
	if (pd>0.3) {
		range = range + (pd-0.3)*18.0;		//stretch upper range to account for skewed tail
	}
	vb = rcore*(1.0+range*pd);		// is this far enough past avg radius?
	
	//temp set scale=1 and bkg=0 for quadrature calc
	temp_3sf[0] = 1.0;
	temp_3sf[1] = dp[1];		//the core radius will be changed in the loop
	temp_3sf[2] = dp[3];
	temp_3sf[3] = dp[4];
	temp_3sf[4] = dp[5];
	temp_3sf[5] = dp[6];
	temp_3sf[6] = dp[7];
	temp_3sf[7] = dp[8];
	temp_3sf[8] = dp[9];
	temp_3sf[9] = dp[10];
	temp_3sf[10] = 0.0;
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss76Z[ii]*(vb-va) + vb + va )/2.0;
		temp_3sf[1] = zi;
		yyy = Gauss76Wt[ii] * SchulzPoint(zi,rcore,zz) * ThreeShell(temp_3sf,x);
		//un-normalize by volume
		yyy *= 4.0*pi/3.0*pow((zi+thick1+thick2+thick3),3);
		summ += yyy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	answer = (vb-va)/2.0*summ;
   	
	//re-normalize by the average volume
	zp1 = zz + 1.0;
	zp2 = zz + 2.0;
	zp3 = zz + 3.0;
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*pow((rcore+thick1+thick2+thick3),3);
	answer /= vpoly;
//scale
	answer *= scale;
// add in the background
	answer += bkg;
		
    return(answer);
}

double
PolyFourShell(double dp[], double x)
{
	double scale,rcore,rhocore,rhosolv,bkg,pd,zz;		//my local names
	double va,vb,summ,yyy,zi;
	double answer,zp1,zp2,zp3,vpoly,range,temp_4sf[13],pi;
	int nord=76,ii;
	double thick1,thick2,thick3,thick4;
	double rhoshel1,rhoshel2,rhoshel3,rhoshel4;
	
	scale = dp[0];
	rcore = dp[1];
	pd = dp[2];
	rhocore = dp[3];
	thick1 = dp[4];
	rhoshel1 = dp[5];
	thick2 = dp[6];
	rhoshel2 = dp[7];
	thick3 = dp[8];
	rhoshel3 = dp[9];
	thick4 = dp[10];
	rhoshel4 = dp[11];
	rhosolv = dp[12];
	bkg = dp[13];
	
	pi = 4.0*atan(1.0);
		
	zz = (1.0/pd)*(1.0/pd)-1.0;		//polydispersity of the core only
	
	range = 8.0;			//std deviations for the integration
	va = rcore*(1.0-range*pd);
	if (va<0) {
		va=0;		//otherwise numerical error when pd >= 0.3, making a<0
	}
	if (pd>0.3) {
		range = range + (pd-0.3)*18.0;		//stretch upper range to account for skewed tail
	}
	vb = rcore*(1.0+range*pd);		// is this far enough past avg radius?
	
	//temp set scale=1 and bkg=0 for quadrature calc
	temp_4sf[0] = 1.0;
	temp_4sf[1] = dp[1];		//the core radius will be changed in the loop
	temp_4sf[2] = dp[3];
	temp_4sf[3] = dp[4];
	temp_4sf[4] = dp[5];
	temp_4sf[5] = dp[6];
	temp_4sf[6] = dp[7];
	temp_4sf[7] = dp[8];
	temp_4sf[8] = dp[9];
	temp_4sf[9] = dp[10];
	temp_4sf[10] = dp[11];
	temp_4sf[11] = dp[12];
	temp_4sf[12] = 0.0;
		
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss76Z[ii]*(vb-va) + vb + va )/2.0;
		temp_4sf[1] = zi;
		yyy = Gauss76Wt[ii] * SchulzPoint(zi,rcore,zz) * FourShell(temp_4sf,x);
		//un-normalize by volume
		yyy *= 4.0*pi/3.0*pow((zi+thick1+thick2+thick3+thick4),3);
		summ += yyy;		//add to the running total of the quadrature
   	}
	// calculate value of integral to return
	answer = (vb-va)/2.0*summ;
   	
	//re-normalize by the average volume
	zp1 = zz + 1.0;
	zp2 = zz + 2.0;
	zp3 = zz + 3.0;
	vpoly = 4.0*pi/3.0*zp3*zp2/zp1/zp1*pow((rcore+thick1+thick2+thick3+thick4),3);
	answer /= vpoly;
//scale
	answer *= scale;
// add in the background
	answer += bkg;
		
    return(answer);
}


/*	BCC_ParaCrystal  :  calculates the form factor of a Triaxial Ellipsoid at the given x-value p->x

Uses 150 pt Gaussian quadrature for both integrals

*/
double
BCC_ParaCrystal(double w[], double x)
{
	int i,j;
	double Pi;
	double scale,Dnn,gg,Rad,contrast,background,latticeScale,sld,sldSolv;		//local variables of coefficient wave
	int nordi=150;			//order of integration
	int nordj=150;
	double va,vb;		//upper and lower integration limits
	double summ,zi,yyy,answer;			//running tally of integration
	double summj,vaj,vbj,zij;			//for the inner integration
	
	Pi = 4.0*atan(1.0);
	va = 0.0;
	vb = 2.0*Pi;		//orintational average, outer integral
	vaj = 0.0;
	vbj = Pi;		//endpoints of inner integral
	
	summ = 0.0;			//initialize intergral
	
	scale = w[0];
	Dnn = w[1];					//Nearest neighbor distance A
	gg = w[2];					//Paracrystal distortion factor
	Rad = w[3];					//Sphere radius
	sld = w[4];
	sldSolv = w[5];
	background = w[6]; 
	
	contrast = sld - sldSolv;
	
	//Volume fraction calculated from lattice symmetry and sphere radius
	latticeScale = 2.0*(4.0/3.0)*Pi*(Rad*Rad*Rad)/pow(Dnn/sqrt(3.0/4.0),3);
	
	for(i=0;i<nordi;i++) {
		//setup inner integral over the ellipsoidal cross-section
		summj=0.0;
		zi = ( Gauss150Z[i]*(vb-va) + va + vb )/2.0;		//the outer dummy is phi
		for(j=0;j<nordj;j++) {
			//20 gauss points for the inner integral
			zij = ( Gauss150Z[j]*(vbj-vaj) + vaj + vbj )/2.0;		//the inner dummy is theta
			yyy = Gauss150Wt[j] * BCC_Integrand(w,x,zi,zij);
			summj += yyy;
		}
		//now calculate the value of the inner integral
		answer = (vbj-vaj)/2.0*summj;
		
		//now calculate outer integral
		yyy = Gauss150Wt[i] * answer;
		summ += yyy;
	}		//final scaling is done at the end of the function, after the NT_FP64 case
	
	answer = (vb-va)/2.0*summ;
	// Multiply by contrast^2
	answer *= SphereForm_Paracrystal(Rad,contrast,x)*scale*latticeScale;
	// add in the background
	answer += background;
	
	return answer;
}

// xx is phi (outer)
// yy is theta (inner)
double
BCC_Integrand(double w[], double qq, double xx, double yy) {
	
	double retVal,temp1,temp3,aa,Da,Dnn,gg,Pi;
	
	Dnn = w[1]; //Nearest neighbor distance A
	gg = w[2]; //Paracrystal distortion factor
	aa = Dnn;
	Da = gg*aa;
	
	Pi = 4.0*atan(1.0);
	temp1 = qq*qq*Da*Da;
	temp3 = qq*aa;	
	
	retVal = BCCeval(yy,xx,temp1,temp3);
	retVal /=4.0*Pi;
	
	return(retVal);
}

double
BCCeval(double Theta, double Phi, double temp1, double temp3) {

	double temp6,temp7,temp8,temp9,temp10;
	double result;
	
	temp6 = sin(Theta);
	temp7 = sin(Theta)*cos(Phi)+sin(Theta)*sin(Phi)+cos(Theta);
	temp8 = -1.0*sin(Theta)*cos(Phi)-sin(Theta)*sin(Phi)+cos(Theta);
	temp9 = -1.0*sin(Theta)*cos(Phi)+sin(Theta)*sin(Phi)-cos(Theta);
	temp10 = exp((-1.0/8.0)*temp1*((temp7*temp7)+(temp8*temp8)+(temp9*temp9)));
	result = pow(1.0-(temp10*temp10),3)*temp6/((1.0-2.0*temp10*cos(0.5*temp3*(temp7))+(temp10*temp10))*(1.0-2.0*temp10*cos(0.5*temp3*(temp8))+(temp10*temp10))*(1.0-2.0*temp10*cos(0.5*temp3*(temp9))+(temp10*temp10)));
	
	return (result);
}

double
SphereForm_Paracrystal(double radius, double delrho, double x) {					
	
	double bes,f,vol,f2,pi;
	pi = 4.0*atan(1.0);
	//
	//handle q==0 separately
	if(x==0) {
		f = 4.0/3.0*pi*radius*radius*radius*delrho*delrho*1.0e8;
		return(f);
	}
	
	bes = 3.0*(sin(x*radius)-x*radius*cos(x*radius))/(x*x*x)/(radius*radius*radius);
	vol = 4.0*pi/3.0*radius*radius*radius;
	f = vol*bes*delrho	;	// [=] �
	// normalize to single particle volume, convert to 1/cm
	f2 = f * f / vol * 1.0e8;		// [=] 1/cm
	
	return (f2);
}

/*	FCC_ParaCrystal  :  calculates the form factor of a Triaxial Ellipsoid at the given x-value p->x

Uses 150 pt Gaussian quadrature for both integrals

*/
double
FCC_ParaCrystal(double w[], double x)
{
	int i,j;
	double Pi;
	double scale,Dnn,gg,Rad,contrast,background,latticeScale,sld,sldSolv;		//local variables of coefficient wave
	int nordi=150;			//order of integration
	int nordj=150;
	double va,vb;		//upper and lower integration limits
	double summ,zi,yyy,answer;			//running tally of integration
	double summj,vaj,vbj,zij;			//for the inner integration
	
	Pi = 4.0*atan(1.0);
	va = 0.0;
	vb = 2.0*Pi;		//orintational average, outer integral
	vaj = 0.0;
	vbj = Pi;		//endpoints of inner integral
	
	summ = 0.0;			//initialize intergral
	
	scale = w[0];
	Dnn = w[1];					//Nearest neighbor distance A
	gg = w[2];					//Paracrystal distortion factor
	Rad = w[3];					//Sphere radius
	sld = w[4];
	sldSolv = w[5];
	background = w[6]; 
	
	contrast = sld - sldSolv;
	//Volume fraction calculated from lattice symmetry and sphere radius
	latticeScale = 4.0*(4.0/3.0)*Pi*(Rad*Rad*Rad)/pow(Dnn*sqrt(2.0),3);
	
	for(i=0;i<nordi;i++) {
		//setup inner integral over the ellipsoidal cross-section
		summj=0.0;
		zi = ( Gauss150Z[i]*(vb-va) + va + vb )/2.0;		//the outer dummy is phi
		for(j=0;j<nordj;j++) {
			//20 gauss points for the inner integral
			zij = ( Gauss150Z[j]*(vbj-vaj) + vaj + vbj )/2.0;		//the inner dummy is theta
			yyy = Gauss150Wt[j] * FCC_Integrand(w,x,zi,zij);
			summj += yyy;
		}
		//now calculate the value of the inner integral
		answer = (vbj-vaj)/2.0*summj;
		
		//now calculate outer integral
		yyy = Gauss150Wt[i] * answer;
		summ += yyy;
	}		//final scaling is done at the end of the function, after the NT_FP64 case
	
	answer = (vb-va)/2.0*summ;
	// Multiply by contrast^2
	answer *= SphereForm_Paracrystal(Rad,contrast,x)*scale*latticeScale;
	// add in the background
	answer += background;
	
	return answer;
}


// xx is phi (outer)
// yy is theta (inner)
double
FCC_Integrand(double w[], double qq, double xx, double yy) {
	
	double retVal,temp1,temp3,aa,Da,Dnn,gg,Pi;
	
	Pi = 4.0*atan(1.0);
	Dnn = w[1]; //Nearest neighbor distance A
	gg = w[2]; //Paracrystal distortion factor
	aa = Dnn;
	Da = gg*aa;
	
	temp1 = qq*qq*Da*Da;
	temp3 = qq*aa;
	
	retVal = FCCeval(yy,xx,temp1,temp3);
	retVal /=4*Pi;
	
	return(retVal);
}

double
FCCeval(double Theta, double Phi, double temp1, double temp3) {

	double temp6,temp7,temp8,temp9,temp10;
	double result;
	
	temp6 = sin(Theta);
	temp7 = sin(Theta)*sin(Phi)+cos(Theta);
	temp8 = -1.0*sin(Theta)*cos(Phi)+cos(Theta);
	temp9 = -1.0*sin(Theta)*cos(Phi)+sin(Theta)*sin(Phi);
	temp10 = exp((-1.0/8.0)*temp1*((temp7*temp7)+(temp8*temp8)+(temp9*temp9)));
	result = pow((1.0-(temp10*temp10)),3)*temp6/((1.0-2.0*temp10*cos(0.5*temp3*(temp7))+(temp10*temp10))*(1.0-2.0*temp10*cos(0.5*temp3*(temp8))+(temp10*temp10))*(1.0-2.0*temp10*cos(0.5*temp3*(temp9))+(temp10*temp10)));
	
	return (result);
}


/*	SC_ParaCrystal  :  calculates the form factor of a Triaxial Ellipsoid at the given x-value p->x

Uses 150 pt Gaussian quadrature for both integrals

*/
double
SC_ParaCrystal(double w[], double x)
{
	int i,j;
	double Pi;
	double scale,Dnn,gg,Rad,contrast,background,latticeScale,sld,sldSolv;		//local variables of coefficient wave
	int nordi=150;			//order of integration
	int nordj=150;
	double va,vb;		//upper and lower integration limits
	double summ,zi,yyy,answer;			//running tally of integration
	double summj,vaj,vbj,zij;			//for the inner integration
	
	Pi = 4.0*atan(1.0);
	va = 0.0;
	vb = Pi/2.0;		//orintational average, outer integral
	vaj = 0.0;
	vbj = Pi/2.0;		//endpoints of inner integral
	
	summ = 0.0;			//initialize intergral
	
	scale = w[0];
	Dnn = w[1];					//Nearest neighbor distance A
	gg = w[2];					//Paracrystal distortion factor
	Rad = w[3];					//Sphere radius
	sld = w[4];
	sldSolv = w[5];
	background = w[6]; 
	
	contrast = sld - sldSolv;
	//Volume fraction calculated from lattice symmetry and sphere radius
	latticeScale = (4.0/3.0)*Pi*(Rad*Rad*Rad)/pow(Dnn,3);
	
	for(i=0;i<nordi;i++) {
		//setup inner integral over the ellipsoidal cross-section
		summj=0.0;
		zi = ( Gauss150Z[i]*(vb-va) + va + vb )/2.0;		//the outer dummy is phi
		for(j=0;j<nordj;j++) {
			//20 gauss points for the inner integral
			zij = ( Gauss150Z[j]*(vbj-vaj) + vaj + vbj )/2.0;		//the inner dummy is theta
			yyy = Gauss150Wt[j] * SC_Integrand(w,x,zi,zij);
			summj += yyy;
		}
		//now calculate the value of the inner integral
		answer = (vbj-vaj)/2.0*summj;
		
		//now calculate outer integral
		yyy = Gauss150Wt[i] * answer;
		summ += yyy;
	}		//final scaling is done at the end of the function, after the NT_FP64 case
	
	answer = (vb-va)/2.0*summ;
	// Multiply by contrast^2
	answer *= SphereForm_Paracrystal(Rad,contrast,x)*scale*latticeScale;
	// add in the background
	answer += background;
	
	return answer;
}

// xx is phi (outer)
// yy is theta (inner)
double
SC_Integrand(double w[], double qq, double xx, double yy) {
	
	double retVal,temp1,temp2,temp3,temp4,temp5,aa,Da,Dnn,gg,Pi;
	
	Pi = 4.0*atan(1.0);
	Dnn = w[1]; //Nearest neighbor distance A
	gg = w[2]; //Paracrystal distortion factor
	aa = Dnn;
	Da = gg*aa;
	
	temp1 = qq*qq*Da*Da;
	temp2 = pow( 1.0-exp(-1.0*temp1) ,3);
	temp3 = qq*aa;
	temp4 = 2.0*exp(-0.5*temp1);
	temp5 = exp(-1.0*temp1);
	
	
	retVal = temp2*SCeval(yy,xx,temp3,temp4,temp5);
	retVal *= 2.0/Pi;
	
	return(retVal);
}

double
SCeval(double Theta, double Phi, double temp3, double temp4, double temp5) { //Function to calculate integrand values for simple cubic structure

	double temp6,temp7,temp8,temp9; //Theta and phi dependent parts of the equation
	double result;
	
	temp6 = sin(Theta);
	temp7 = -1.0*temp3*sin(Theta)*cos(Phi);
	temp8 = temp3*sin(Theta)*sin(Phi);
	temp9 = temp3*cos(Theta);
	result = temp6/((1.0-temp4*cos((temp7))+temp5)*(1.0-temp4*cos((temp8))+temp5)*(1.0-temp4*cos((temp9))+temp5));
	
	return (result);
}

// scattering from a uniform sphere with a Gaussian size distribution
//
double
FuzzySpheres(double dp[], double q)
{
	double pi,x;
	double scale,rad,pd,sig,rho,rhos,bkg,delrho,sig_surf,f2,bes,vol,f;		//my local names
	double va,vb,zi,yy,summ,inten;
	int nord=20,ii;
	
	pi = 4.0*atan(1.0);
	x= q;
	
	scale=dp[0];
	rad=dp[1];
	pd=dp[2];
	sig=pd*rad;
	sig_surf = dp[3];
	rho=dp[4];
	rhos=dp[5];
	delrho=rho-rhos;
	bkg=dp[6];
	
			
	va = -4.0*sig + rad;
	if (va<0) {
		va=0;		//to avoid numerical error when  va<0 (-ve q-value)
	}
	vb = 4.0*sig +rad;
	
	summ = 0.0;		// initialize integral
	for(ii=0;ii<nord;ii+=1) {
		// calculate Gauss points on integration interval (r-value for evaluation)
		zi = ( Gauss20Z[ii]*(vb-va) + vb + va )/2.0;
		// calculate sphere scattering
		//
		//handle q==0 separately
		if (x==0.0) {
			f2 = 4.0/3.0*pi*zi*zi*zi*delrho*delrho*1.0e8;
			f2 *= exp(-0.5*sig_surf*sig_surf*x*x);
			f2 *= exp(-0.5*sig_surf*sig_surf*x*x);
		} else {
			bes = 3.0*(sin(x*zi)-x*zi*cos(x*zi))/(x*x*x)/(zi*zi*zi);
			vol = 4.0*pi/3.0*zi*zi*zi;
			f = vol*bes*delrho;		// [=] A
			f *= exp(-0.5*sig_surf*sig_surf*x*x);
			// normalize to single particle volume, convert to 1/cm
			f2 = f * f / vol * 1.0e8;		// [=] 1/cm
		}
	
		yy = Gauss20Wt[ii] *  Gauss_distr(sig,rad,zi) * f2;
		yy *= 4.0*pi/3.0*zi*zi*zi;		//un-normalize by current sphere volume
		
		summ += yy;		//add to the running total of the quadrature
		
		
   	}
	// calculate value of integral to return
	inten = (vb-va)/2.0*summ;
	
	//re-normalize by polydisperse sphere volume
	inten /= (4.0*pi/3.0*rad*rad*rad)*(1.0+3.0*pd*pd);
	
	inten *= scale;
	inten += bkg;
	
    return(inten);	//scale, and add in the background
}



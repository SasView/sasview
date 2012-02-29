/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */

/**
 * Scattering model classes
 * The classes use the IGOR library found in
 *   sansmodels/src/libigor
 *
 */

#include <math.h>
#include "parameters.hh"
#include <stdio.h>
#include "rpa.h"

using namespace std;

static double rpa_kernel(double dp[], double q) {
  int lCASE = dp[0];

  double Na,Nb,Nc,Nd,Nab,Nac,Nad,Nbc,Nbd,Ncd;
  double Phia,Phib,Phic,Phid,Phiab,Phiac,Phiad;
  double Phibc,Phibd,Phicd;
  double va,vb,vc,vd,vab,vac,vad,vbc,vbd,vcd;
  double m;
  double ba,bb,bc,bd;
  double Xa,Xb,Xc,Xd;
  double Paa,S0aa,Pab,S0ab,Pac,S0ac,Pad,S0ad;
  double S0ba,Pbb,S0bb,Pbc,S0bc,Pbd,S0bd;
  double S0ca,S0cb,Pcc,S0cc,Pcd,S0cd;
  double S0da,S0db,S0dc,Pdd,S0dd;
  double Kaa,Kab,Kac,Kad,Kba,Kbb,Kbc,Kbd;
  double Kca,Kcb,Kcc,Kcd,Kda,Kdb,Kdc,Kdd;
  double Zaa,Zab,Zac,Zba,Zbb,Zbc,Zca,Zcb,Zcc;
  double DenT,T11,T12,T13,T21,T22,T23,T31,T32,T33;
  double Y1,Y2,Y3,X11,X12,X13,X21,X22,X23,X31,X32,X33;
  double ZZ,DenQ1,DenQ2,DenQ3,DenQ,Q11,Q12,Q13,Q21,Q22,Q23,Q31,Q32,Q33;
  double N11,N12,N13,N21,N22,N23,N31,N32,N33;
  double M11,M12,M13,M21,M22,M23,M31,M32,M33;
  double S11,S12,S13,S14,S21,S22,S23,S24;
  double S31,S32,S33,S34,S41,S42,S43,S44;
  double La,Lb,Lc,Ld,Lad,Lbd,Lcd,Nav,Intg;
  double scale, background;

  int ii=13;  //dp[ii<13] = fittable, else fixed

  Na=1000.0;
  Nb=1000.0;
  Nc=1000.0;
  Nd=1000.0;  //DEGREE OF POLYMERIZATION
  Phia=0.25;
  Phib=0.25;
  Phic=0.25;
  Phid=0.25 ; //VOL FRACTION
  Kab=-0.0004;
  Kac=-0.0004;
  Kad=-0.0004;  //CHI PARAM
  Kbc=-0.0004;
  Kbd=-0.0004;
  Kcd=-0.0004;
  La=1.0e-12;
  Lb=1.0e-12;
  Lc=1.0e-12;
  Ld=0.0e-12;   //SCATT. LENGTH
  va=100.0;
  vb=100.0;
  vc=100.0;
  vd=100.0  ; //SPECIFIC VOLUME
  ba=5.0;
  bb=5.0;
  bc=5.0;
  bd=5.0;   //SEGMENT LENGTH

  //lCASE was shifted to N-1 from the original code
  if (lCASE <= 1){
    Phia=0.0000001;
    Phib=0.0000001;
    Phic=0.5;
    Phid=0.5;
    Nc=dp[ii+8];
    Phic=dp[ii+9];
    vc=dp[ii+10];
    Lc=dp[ii+11];
    bc=dp[3];
    Nd=dp[ii+12];
    Phid=dp[ii+13];
    vd=dp[ii+14];
    Ld=dp[ii+15];
    bd=dp[4];
    Kcd=dp[10];
    scale=dp[11];
    background=dp[12];
  }
  else if ((lCASE > 1) && (lCASE <= 4)){
    Phia=0.0000001;
    Phib=0.333333;
    Phic=0.333333;
    Phid=0.333333;
    Nb=dp[ii+4];
    Phib=dp[ii+5];
    vb=dp[ii+6];
    Lb=dp[ii+7];
    bb=dp[2];
    Nc=dp[ii+8];
    Phic=dp[ii+9];
    vc=dp[ii+10];
    Lc=dp[ii+11];
    bc=dp[3];
    Nd=dp[ii+12];
    Phid=dp[ii+13];
    vd=dp[ii+14];
    Ld=dp[ii+15];
    bd=dp[4];
    Kbc=dp[8];
    Kbd=dp[9];
    Kcd=dp[10];
    scale=dp[11];
    background=dp[12];
  }
  else {
    Phia=0.25;
    Phib=0.25;
    Phic=0.25;
    Phid=0.25;
    Na=dp[ii+0];
    Phia=dp[ii+1];
    va=dp[ii+2];
    La=dp[ii+3];
    ba=dp[1];
    Nb=dp[ii+4];
    Phib=dp[ii+5];
    vb=dp[ii+6];
    Lb=dp[ii+7];
    bb=dp[2];
    Nc=dp[ii+8];
    Phic=dp[ii+9];
    vc=dp[ii+10];
    Lc=dp[ii+11];
    bc=dp[3];
    Nd=dp[ii+12];
    Phid=dp[ii+13];
    vd=dp[ii+14];
    Ld=dp[ii+15];
    bd=dp[4];
    Kab=dp[5];
    Kac=dp[6];
    Kad=dp[7];
    Kbc=dp[8];
    Kbd=dp[9];
    Kcd=dp[10];
    scale=dp[11];
    background=dp[12];
  }

  Nab=pow((Na*Nb),(0.5));
  Nac=pow((Na*Nc),(0.5));
  Nad=pow((Na*Nd),(0.5));
  Nbc=pow((Nb*Nc),(0.5));
  Nbd=pow((Nb*Nd),(0.5));
  Ncd=pow((Nc*Nd),(0.5));

  vab=pow((va*vb),(0.5));
  vac=pow((va*vc),(0.5));
  vad=pow((va*vd),(0.5));
  vbc=pow((vb*vc),(0.5));
  vbd=pow((vb*vd),(0.5));
  vcd=pow((vc*vd),(0.5));

  Phiab=pow((Phia*Phib),(0.5));
  Phiac=pow((Phia*Phic),(0.5));
  Phiad=pow((Phia*Phid),(0.5));
  Phibc=pow((Phib*Phic),(0.5));
  Phibd=pow((Phib*Phid),(0.5));
  Phicd=pow((Phic*Phid),(0.5));

  Xa=q*q*ba*ba*Na/6.0;
  Xb=q*q*bb*bb*Nb/6.0;
  Xc=q*q*bc*bb*Nc/6.0;
  Xd=q*q*bd*bb*Nd/6.0;

  Paa=2.0*(exp(-Xa)-1.0+Xa)/pow(Xa,2.0);
  S0aa=Na*Phia*va*Paa;
  Pab=((1.0-exp(-Xa))/Xa)*((1.0-exp(-Xb))/Xb);
  S0ab=(Phiab*vab*Nab)*Pab;
  Pac=((1.0-exp(-Xa))/Xa)*exp(-Xb)*((1.0-exp(-Xc))/Xc);
  S0ac=(Phiac*vac*Nac)*Pac;
  Pad=((1.0-exp(-Xa))/Xa)*exp(-Xb-Xc)*((1.0-exp(-Xd))/Xd);
  S0ad=(Phiad*vad*Nad)*Pad;

  S0ba=S0ab;
  Pbb=2.0*(exp(-Xb)-1.0+Xb)/pow(Xb,2.0);
  S0bb=Nb*Phib*vb*Pbb;
  Pbc=((1.0-exp(-Xb))/Xb)*((1.0-exp(-Xc))/Xc);
  S0bc=(Phibc*vbc*Nbc)*Pbc;
  Pbd=((1.0-exp(-Xb))/Xb)*exp(-Xc)*((1.0-exp(-Xd))/Xd);
  S0bd=(Phibd*vbd*Nbd)*Pbd;

  S0ca=S0ac;
  S0cb=S0bc;
  Pcc=2.0*(exp(-Xc)-1.0+Xc)/pow(Xc,2.0);
  S0cc=Nc*Phic*vc*Pcc;
  Pcd=((1.0-exp(-Xc))/Xc)*((1.0-exp(-Xd))/Xd);
  S0cd=(Phicd*vcd*Ncd)*Pcd;

  S0da=S0ad;
  S0db=S0bd;
  S0dc=S0cd;
  Pdd=2.0*(exp(-Xd)-1.0+Xd)/pow(Xd,2.0);
  S0dd=Nd*Phid*vd*Pdd;
  //lCASE was shifted to N-1 from the original code
  switch(lCASE){
  case 0:
    S0aa=0.000001;
    S0ab=0.000002;
    S0ac=0.000003;
    S0ad=0.000004;
    S0bb=0.000005;
    S0bc=0.000006;
    S0bd=0.000007;
    S0cd=0.000008;
    break;
  case 1:
    S0aa=0.000001;
    S0ab=0.000002;
    S0ac=0.000003;
    S0ad=0.000004;
    S0bb=0.000005;
    S0bc=0.000006;
    S0bd=0.000007;
    break;
  case 2:
    S0aa=0.000001;
    S0ab=0.000002;
    S0ac=0.000003;
    S0ad=0.000004;
    S0bc=0.000005;
    S0bd=0.000006;
    S0cd=0.000007;
    break;
  case 3:
    S0aa=0.000001;
    S0ab=0.000002;
    S0ac=0.000003;
    S0ad=0.000004;
    S0bc=0.000005;
    S0bd=0.000006;
    break;
  case 4:
    S0aa=0.000001;
    S0ab=0.000002;
    S0ac=0.000003;
    S0ad=0.000004;
    break;
  case 5:
    S0ab=0.000001;
    S0ac=0.000002;
    S0ad=0.000003;
    S0bc=0.000004;
    S0bd=0.000005;
    S0cd=0.000006;
    break;
  case 6:
    S0ab=0.000001;
    S0ac=0.000002;
    S0ad=0.000003;
    S0bc=0.000004;
    S0bd=0.000005;
    break;
  case 7:
    S0ab=0.000001;
    S0ac=0.000002;
    S0ad=0.000003;
    break;
  case 8:
    S0ac=0.000001;
    S0ad=0.000002;
    S0bc=0.000003;
    S0bd=0.000004;
    break;
  default : //case 9:
    break;
  }
  S0ba=S0ab;
  S0ca=S0ac;
  S0cb=S0bc;
  S0da=S0ad;
  S0db=S0bd;
  S0dc=S0cd;

  Kaa=0.0;
  Kbb=0.0;
  Kcc=0.0;
  Kdd=0.0;

  Kba=Kab;
  Kca=Kac;
  Kcb=Kbc;
  Kda=Kad;
  Kdb=Kbd;
  Kdc=Kcd;

  Zaa=Kaa-Kad-Kad;
  Zab=Kab-Kad-Kbd;
  Zac=Kac-Kad-Kcd;
  Zba=Kba-Kbd-Kad;
  Zbb=Kbb-Kbd-Kbd;
  Zbc=Kbc-Kbd-Kcd;
  Zca=Kca-Kcd-Kad;
  Zcb=Kcb-Kcd-Kbd;
  Zcc=Kcc-Kcd-Kcd;

  DenT=(-(S0ac*S0bb*S0ca) + S0ab*S0bc*S0ca + S0ac*S0ba*S0cb - S0aa*S0bc*S0cb - S0ab*S0ba*S0cc + S0aa*S0bb*S0cc);

  T11= (-(S0bc*S0cb) + S0bb*S0cc)/DenT;
  T12= (S0ac*S0cb - S0ab*S0cc)/DenT;
  T13= (-(S0ac*S0bb) + S0ab*S0bc)/DenT;
  T21= (S0bc*S0ca - S0ba*S0cc)/DenT;
  T22= (-(S0ac*S0ca) + S0aa*S0cc)/DenT;
  T23= (S0ac*S0ba - S0aa*S0bc)/DenT;
  T31= (-(S0bb*S0ca) + S0ba*S0cb)/DenT;
  T32= (S0ab*S0ca - S0aa*S0cb)/DenT;
  T33= (-(S0ab*S0ba) + S0aa*S0bb)/DenT;

  Y1=T11*S0ad+T12*S0bd+T13*S0cd+1.0;
  Y2=T21*S0ad+T22*S0bd+T23*S0cd+1.0;
  Y3=T31*S0ad+T32*S0bd+T33*S0cd+1.0;

  X11=Y1*Y1;
  X12=Y1*Y2;
  X13=Y1*Y3;
  X21=Y2*Y1;
  X22=Y2*Y2;
  X23=Y2*Y3;
  X31=Y3*Y1;
  X32=Y3*Y2;
  X33=Y3*Y3;

  ZZ=S0ad*(T11*S0ad+T12*S0bd+T13*S0cd)+S0bd*(T21*S0ad+T22*S0bd+T23*S0cd)+S0cd*(T31*S0ad+T32*S0bd+T33*S0cd);

  m=1.0/(S0dd-ZZ);

  N11=m*X11+Zaa;
  N12=m*X12+Zab;
  N13=m*X13+Zac;
  N21=m*X21+Zba;
  N22=m*X22+Zbb;
  N23=m*X23+Zbc;
  N31=m*X31+Zca;
  N32=m*X32+Zcb;
  N33=m*X33+Zcc;

  M11= N11*S0aa + N12*S0ab + N13*S0ac;
  M12= N11*S0ab + N12*S0bb + N13*S0bc;
  M13= N11*S0ac + N12*S0bc + N13*S0cc;
  M21= N21*S0aa + N22*S0ab + N23*S0ac;
  M22= N21*S0ab + N22*S0bb + N23*S0bc;
  M23= N21*S0ac + N22*S0bc + N23*S0cc;
  M31= N31*S0aa + N32*S0ab + N33*S0ac;
  M32= N31*S0ab + N32*S0bb + N33*S0bc;
  M33= N31*S0ac + N32*S0bc + N33*S0cc;

  DenQ1=1.0+M11-M12*M21+M22+M11*M22-M13*M31-M13*M22*M31;
  DenQ2=  M12*M23*M31+M13*M21*M32-M23*M32-M11*M23*M32+M33+M11*M33;
  DenQ3=  -M12*M21*M33+M22*M33+M11*M22*M33;
  DenQ=DenQ1+DenQ2+DenQ3;

  Q11= (1.0 + M22-M23*M32 + M33 + M22*M33)/DenQ;
  Q12= (-M12 + M13*M32 - M12*M33)/DenQ;
  Q13= (-M13 - M13*M22 + M12*M23)/DenQ;
  Q21= (-M21 + M23*M31 - M21*M33)/DenQ;
  Q22= (1.0 + M11 - M13*M31 + M33 + M11*M33)/DenQ;
  Q23= (M13*M21 - M23 - M11*M23)/DenQ;
  Q31= (-M31 - M22*M31 + M21*M32)/DenQ;
  Q32= (M12*M31 - M32 - M11*M32)/DenQ;
  Q33= (1.0 + M11 - M12*M21 + M22 + M11*M22)/DenQ;

  S11= Q11*S0aa + Q21*S0ab + Q31*S0ac;
  S12= Q12*S0aa + Q22*S0ab + Q32*S0ac;
  S13= Q13*S0aa + Q23*S0ab + Q33*S0ac;
  S14=-S11-S12-S13;
  S21= Q11*S0ba + Q21*S0bb + Q31*S0bc;
  S22= Q12*S0ba + Q22*S0bb + Q32*S0bc;
  S23= Q13*S0ba + Q23*S0bb + Q33*S0bc;
  S24=-S21-S22-S23;
  S31= Q11*S0ca + Q21*S0cb + Q31*S0cc;
  S32= Q12*S0ca + Q22*S0cb + Q32*S0cc;
  S33= Q13*S0ca + Q23*S0cb + Q33*S0cc;
  S34=-S31-S32-S33;
  S41=S14;
  S42=S24;
  S43=S34;
  S44=S11+S22+S33+2.0*S12+2.0*S13+2.0*S23;

  Nav=6.022045e+23;
  Lad=(La/va-Ld/vd)*sqrt(Nav);
  Lbd=(Lb/vb-Ld/vd)*sqrt(Nav);
  Lcd=(Lc/vc-Ld/vd)*sqrt(Nav);

  Intg=pow(Lad,2.0)*S11+pow(Lbd,2.0)*S22+pow(Lcd,2.0)*S33+2.0*Lad*Lbd*S12+2.0*Lbd*Lcd*S23+2.0*Lad*Lcd*S13;

  Intg *= scale;
  Intg += background;

  return Intg;

}

RPAModel :: RPAModel() {
  lcase_n = Parameter(0.0);
  ba = Parameter(5.0);
  bb = Parameter(5.0);
  bc = Parameter(5.0);
  bd = Parameter(5.0);

  Kab = Parameter(-0.0004);
  Kac = Parameter(-0.0004);
  Kad = Parameter(-0.0004);
  Kbc = Parameter(-0.0004);
  Kbd = Parameter(-0.0004);
  Kcd = Parameter(-0.0004);

  scale = Parameter(1.0);
  background = Parameter(0.0);

  Na = Parameter(1000.0);
  Phia = Parameter(0.25);
  va = Parameter(100.0);
  La = Parameter(1.0e-012);

  Nb = Parameter(1000.0);
  Phib = Parameter(0.25);
  vb = Parameter(100.0);
  Lb = Parameter(1.0e-012);

  Nc = Parameter(1000.0);
  Phic = Parameter(0.25);
  vc = Parameter(100.0);
  Lc = Parameter(1.0e-012);

  Nd = Parameter(1000.0);
  Phid = Parameter(0.25);
  vd = Parameter(100.0);
  Ld = Parameter(0.0e-012);

}

/**
 * Function to evaluate 1D scattering function
 * The NIST IGOR library is used for the actual calculation.
 * @param q: q-value
 * @return: function value
 */
double RPAModel :: operator()(double q) {
  double dp[29];
  // Fill parameter array for IGOR library
  // Add the background after averaging
  //Fittable parameters
  dp[0] = lcase_n();

  dp[1] = ba();
  dp[2] = bb();
  dp[3] = bc();
  dp[4] = bd();

  dp[5] = Kab();
  dp[6] = Kac();
  dp[7] = Kad();
  dp[8] = Kbc();
  dp[9] = Kbd();
  dp[10] = Kcd();

  dp[11] = scale();
  dp[12] = background();

  //Fixed parameters
  dp[13] = Na();
  dp[14] = Phia();
  dp[15] = va();
  dp[16] = La();

  dp[17] = Nb();
  dp[18] = Phib();
  dp[19] = vb();
  dp[20] = Lb();

  dp[21] = Nc();
  dp[22] = Phic();
  dp[23] = vc();
  dp[24] = Lc();

  dp[25] = Nd();
  dp[26] = Phid();
  dp[27] = vd();
  dp[28] = Ld();

  return rpa_kernel(dp,q);
}

/**
 * Function to evaluate 2D scattering function
 * @param q_x: value of Q along x
 * @param q_y: value of Q along y
 * @return: function value
 */
double RPAModel :: operator()(double qx, double qy) {
  double q = sqrt(qx*qx + qy*qy);
  return (*this).operator()(q);
}

/**
 * Function to evaluate 2D scattering function
 * @param pars: parameters of the sphere
 * @param q: q-value
 * @param phi: angle phi
 * @return: function value
 */
double RPAModel :: evaluate_rphi(double q, double phi) {
  return (*this).operator()(q);
}

/**
 * Function to calculate effective radius
 * @return: effective radius value
 */
double RPAModel :: calculate_ER() {
  //NOT implemented!!!
  return 0.0;
}
double RPAModel :: calculate_VR() {
  return 1.0;
}

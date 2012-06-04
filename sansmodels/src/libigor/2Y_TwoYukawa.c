/*
 *  twoyukawa.c
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/7/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

#include "2Y_TwoYukawa.h"
#include "2Y_cpoly.h"
#include "2Y_utility.h"
#include "2Y_PairCorrelation.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/*
 ================================================================================================== 
 
 The two-yukawa structure factor is uniquley determined by 6 parameters a, b, c1, c2, d1, d2,
 which are the solution of a system of 6 equations ( 4 linear, 2 nonlinear ). The solution can 
 constructed by the roots of a polynomial of 22nd degree. For more details see attached 
 Mathematica snotebook, where a derivation is given
 
 ================================================================================================== 
 */

double TY_q22;
double TY_qa12, TY_qa21, TY_qa22, TY_qa23, TY_qa32;
double TY_qb12, TY_qb21, TY_qb22, TY_qb23, TY_qb32;
double TY_qc112, TY_qc121, TY_qc122, TY_qc123, TY_qc132;
double TY_qc212, TY_qc221, TY_qc222, TY_qc223, TY_qc232;
double TY_A12, TY_A21, TY_A22, TY_A23, TY_A32, TY_A41, TY_A42, TY_A43, TY_A52;
double TY_B12, TY_B14, TY_B21, TY_B22, TY_B23, TY_B24, TY_B25, TY_B32, TY_B34;
double TY_F14, TY_F16, TY_F18, TY_F23, TY_F24, TY_F25, TY_F26, TY_F27, TY_F28, TY_F29, TY_F32, TY_F33, TY_F34, TY_F35, TY_F36, TY_F37, TY_F38, TY_F39, TY_F310;
double TY_G13, TY_G14, TY_G15, TY_G16, TY_G17, TY_G18, TY_G19, TY_G110, TY_G111, TY_G112, TY_G113, TY_G22, TY_G23, TY_G24, TY_G25, TY_G26, TY_G27, TY_G28, TY_G29, TY_G210, TY_G211, TY_G212, TY_G213, TY_G214;
double TY_w[23];

double TY_sigma( double s, 
				 double Z1, double Z2, 
			     double a, double b, double c1, double c2, double d1, double d2 )
{
	return -(a / 2. + b + c1 * exp( -Z1 ) + c2 * exp( -Z2 )) / s + a * pow( s, -3 ) + b * pow( s, -2 ) + 
	( c1 + d1 ) * pow( s + Z1, -1 ) + ( c2 + d2 ) * pow( s + Z2, -1 );
}

double TY_tau( double s, 
			   double Z1, double Z2, 
		       double a, double b, double c1, double c2 )
{
	return b * pow( s, -2 ) + a * ( pow( s, -3 ) + pow( s, -2 ) ) - pow( s, -1 ) * ( c1 * Z1 * exp( -Z1 ) * 
																					pow( s + Z1, -1 ) + c2 * Z2 * exp( -Z2 ) * pow( s + Z2, -1 ) );
} 

double TY_q( double s, 
			     double Z1, double Z2, 
			     double a, double b, double c1, double c2, double d1, double d2 )
{
	return TY_sigma(s, Z1, Z2, a, b, c1, c2, d1, d2) - exp( -s ) * TY_tau(s, Z1, Z2, a,b, c1, c2);
}

double TY_g( double s, 
		     double phi, double Z1, double Z2, 
		     double a, double b, double c1, double c2, double d1, double d2 )
{
	return s * TY_tau( s, Z1, Z2, a, b, c1, c2 ) * exp( -s ) / ( 1 - 12 * phi * TY_q( s, Z1, Z2, a, b, c1, c2, d1, d2 ) );
}

/*
 ================================================================================================== 
 
 Structure factor for the potential 
 
 V(r) = -kB * T * ( K1 * exp[ -Z1 * (r - 1)] / r + K2 * exp[ -Z2 * (r - 1)] / r ) for r > 1
 V(r) = inf for r <= 1
 
 The structure factor is parametrized by (a, b, c1, c2, d1, d2) 
 which depend on (K1, K2, Z1, Z2, phi).  
 
 ================================================================================================== 
 */

double TY_hq( double q, double Z, double K, double v )
{
	double t1, t2, t3, t4;

	if ( q == 0) 
	{
		return (exp(-2*Z)*(v + (v*(-1 + Z) - 2*K*Z)*exp(Z))*(-(v*(1 + Z)) + (v + 2*K*Z*(1 + Z))*exp(Z))*pow(K,-1)*pow(Z,-4))/4.;
	}
	else 
	{
		
		t1 = ( 1 - v / ( 2 * K * Z * exp( Z ) ) ) * ( ( 1 - cos( q ) ) / ( q*q ) - 1 / ( Z*Z + q*q ) );
		t2 = ( v*v * ( q * cos( q ) - Z * sin( q ) ) ) / ( 4 * K * Z*Z * q * ( Z*Z + q*q ) );
		t3 = ( q * cos( q ) + Z * sin( q ) ) / ( q * ( Z*Z + q*q ) );
		t4 = v / ( Z * exp( Z ) ) - v*v / ( 4 * K * Z*Z * exp( 2 * Z ) ) - K;
		
		return v / Z * t1 - t2 + t3 * t4;
	}
}

double TY_pc( double q, 
			  double Z1, double Z2,double K1, double K2, double phi,
			  double a, double b, double c1, double c2, double d1, double d2 )
{	
	double v1 = 24 * phi * K1 * exp( Z1 ) * TY_g( Z1, phi, Z1, Z2, a, b, c1, c2, d1, d2 );
	double v2 = 24 * phi * K2 * exp( Z2 ) * TY_g( Z2, phi, Z1, Z2, a, b, c1, c2, d1, d2 );
	
	double a0 = a * a;
	double b0 = -12 * phi *( pow( a + b,2 ) / 2 + a * ( c1 * exp( -Z1 ) + c2 * exp( -Z2 ) ) );
	
	double t1, t2, t3,t4;
	
	if ( q == 0 ) 
	{
		t1 = a0 / 3;
		t2 = b0 / 4;
		t3 = a0 * phi / 12;
	}
	else 
	{
		t1 = a0 * ( sin( q ) - q * cos( q ) ) / pow( q, 3 );
		t2 = b0 * ( 2 * q * sin( q ) - ( q * q - 2 ) * cos( q ) - 2 ) / pow( q, 4 );
		t3 = a0 * phi * ( ( q*q - 6 ) * 4 * q * sin( q ) - ( pow( q, 4 ) - 12 * q*q + 24) * cos( q ) + 24 ) / ( 2 * pow( q, 6 ) );
	}
	t4 = TY_hq( q, Z1, K1, v1 ) + TY_hq( q, Z2, K2, v2 );
	return -24 * phi * ( t1 + t2 + t3 + t4 );
}

double SqTwoYukawa( double q, 
				    double Z1, double Z2, double K1, double K2, double phi,
				    double a, double b, double c1, double c2, double d1, double d2 )
{
	if ( Z1 == Z2 ) 
	{
		// one-yukawa potential
		return 0;
	} 
	else 
	{
		// two-yukawa potential
		return 1. / ( 1. - TY_pc( q, Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	}
}

/*
================================================================================================== 

 Non-linear eqaution system that determines the parameter for structure factor
  
================================================================================================== 
*/

double TY_LinearEquation_1( double Z1, double Z2, double K1, double K2, double phi, 
						    double a, double b, double c1, double c2, double d1, double d2 )
{
	return b - 12 * phi * ( -a / 8. - b / 6. + d1 * pow( Z1, -2 ) + c1 * ( pow( Z1, -2 )  - exp( -Z1 ) * 
		    ( 0.5 + ( 1 + Z1 ) * pow( Z1, -2 ) ) ) + d2 * pow( Z2, -2 ) + c2 * ( pow( Z2, -2 ) - exp( -Z2 )
			* ( 0.5 + ( 1 + Z2 ) * pow( Z2, -2 ) ) ) );
}

double TY_LinearEquation_2( double Z1, double Z2, double K1, double K2, double phi, 
							double a, double b, double c1, double c2, double d1, double d2 )
{
	return 1 - a - 12 * phi * ( -a / 3. - b / 2. + d1 * pow( Z1, -1 ) + c1 * ( pow( Z1, -1 ) - ( 1 + Z1 ) * 
		   exp( -Z1 ) * pow( Z1, -1 ) ) + d2 * pow( Z2, -1 ) + c2 * ( pow( Z2, -1 ) - ( 1 + Z2 ) * exp( -Z2 ) * pow( Z2, -1 ) ) );
}	

double TY_LinearEquation_3( double Z1, double Z2, double K1, double K2, double phi, 
						    double a, double b, double c1, double c2, double d1, double d2 )
{								
	return K1 * exp( Z1 ) - d1 * Z1 * ( 1 - 12 * phi * TY_q( Z1, Z1, Z2, a, b, c1, c2, d1, d2 ) ); 
}

double TY_LinearEquation_4( double Z1, double Z2, double K1, double K2, double phi, 
						    double a, double b, double c1, double c2, double d1, double d2 )
{
	return K2 * exp( Z2 ) - d2 * Z2 * ( 1 - 12 * phi * TY_q( Z2, Z1, Z2, a, b, c1, c2, d1, d2 ) );
}

double TY_NonlinearEquation_1( double Z1, double Z2, double K1, double K2, double phi, 
						       double a, double b, double c1, double c2, double d1, double d2 )
{
	return c1 + d1 - 12 * phi * ( ( c1 + d1 ) * TY_sigma( Z1, Z1, Z2, a, b, c1, c2, d1, d2 ) 
								 - c1 * TY_tau( Z1, Z1, Z2, a, b, c1, c2 ) * exp( -Z1 ) );
}

double TY_NonlinearEquation_2( double Z1, double Z2, double K1, double K2, double phi, 
						       double a, double b, double c1, double c2, double d1, double d2 )
{
	return c2 + d2 - 12 * phi * ( ( c2 + d2 ) * TY_sigma( Z2, Z1, Z2, a, b, c1, c2, d1, d2 ) 
								 - c2 * TY_tau( Z2, Z1, Z2, a, b, c1, c2 ) * exp( -Z2 ) );
}

// Check the computed solutions satisfy the system of equations 
int TY_CheckSolution( double Z1, double Z2, double K1, double K2, double phi, 
				      double a, double b, double c1, double c2, double d1, double d2 )
{
	double eq_1 = chop( TY_LinearEquation_1( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	double eq_2 = chop( TY_LinearEquation_2( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	double eq_3 = chop( TY_LinearEquation_3( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	double eq_4 = chop( TY_LinearEquation_4( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	double eq_5 = chop( TY_NonlinearEquation_1( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	double eq_6 = chop( TY_NonlinearEquation_2( Z1, Z2, K1, K2, phi, a, b, c1, c2, d1, d2 ) );
	
	// check if all equation are zero
	return eq_1 == 0 && eq_2 == 0 && eq_3 == 0 && eq_4 == 0 && eq_5 == 0 && eq_6 == 0;
}

void TY_ReduceNonlinearSystem( double Z1, double Z2, double K1, double K2, double phi, int debug )
{
	/* solution of the 4 linear equations depending on d1 and d2, the solution is polynomial
	 in d1, d2. We represend the solution as determiants obtained by Cramer's rule
	 which can be expressed by their coefficient matrices
	 */
	char buf[256];
	
	double m11 = (3*phi)/2.;
	double m13 = 6*phi*exp(-Z1)*(2 + Z1*(2 + Z1) - 2*exp(Z1))*pow(Z1,-2);
	double m14 = 6*phi*exp(-Z2)*(2 + Z2*(2 + Z2) - 2*exp(Z2))*pow(Z2,-2);
	double m23 = -12*phi*exp(-Z1)*(-1 - Z1 + exp(Z1))*pow(Z1,-1);
	double m24 = -12*phi*exp(-Z2)*(-1 - Z2 + exp(Z2))*pow(Z2,-1);
	double m31 = -6*phi*exp(-Z1)*pow(Z1,-2)*(2*(1 + Z1) + exp(Z1)*(-2 + pow(Z1,2)));
	double m32 = -12*phi*(-1 + Z1 + exp(-Z1))*pow(Z1,-1);
	double m33 = 6*phi*exp(-2*Z1)*pow(-1 + exp(Z1),2);
	double m34 = 12*phi*exp(-Z1 - Z2)*(Z2 - (Z1 + Z2)*exp(Z1) + Z1*exp(Z1 + Z2))*pow(Z1 + Z2,-1);
	double m41 = -6*phi*exp(-Z2)*pow(Z2,-2)*(2*(1 + Z2) + exp(Z2)*(-2 + pow(Z2,2)));
	double m42 = -12*phi*(-1 + Z2 + exp(-Z2))*pow(Z2,-1);
	double m43 = 12*phi*exp(-Z1 - Z2)*(Z1 - (Z1 + Z2 - Z2*exp(Z1))*exp(Z2))*pow(Z1 + Z2,-1);	
	double m44 = 6*phi*exp(-2*Z2)*pow(-1 + exp(Z2),2);
	
	/* determinant of the linear system expressed as coefficient matrix in d1, d2 */
	
	TY_q22 = m14*(-(m33*m42) + m23*(m32*m41 - m31*m42) + m32*m43 + (4*m11*(-3*m33*m41 + 2*m33*m42 + 3*m31*m43 - 2*m32*m43))/3.) + 
		  m13*(m34*m42 + m24*(-(m32*m41) + m31*m42) - m32*m44 + (4*m11*(3*m34*m41 - 2*m34*m42 - 3*m31*m44 + 2*m32*m44))/3.) + (3*m24*
		  (m33*(3*m41 + 4*m11*m41 - 3*m11*m42) + (-3*m31 - 4*m11*m31 + 3*m11*m32)*m43) + 3*m23*(-3*m34*m41 - 4*m11*m34*m41 + 
		  3*m11*m34*m42 + 3*m31*m44 + 4*m11*m31*m44 - 3*m11*m32*m44) - (m34*m43 - m33*m44)*pow(3 - 2*m11,2))/9.;
/*	
	if( debug ) 
	{
		sprintf(buf,"\rDet = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t%f\r%f\t%f\r", 0., 0., 0., TY_q22 );
		XOPNotice(buf);
	}
*/
	
	/* Matrix representation of the determinant of the of the system where row refering to 
	 the variable a is replaced by solution vector */
	
	TY_qa12 = (K1*(3*m14*(m23*m42 - 4*m11*m43) - 3*m13*(m24*m42 - 4*m11*m44) + (3 + 4*m11)*(m24*m43 - m23*m44))*exp(Z1))/3.;
	
	TY_qa21 = -(K2*(3*m14*(m23*m32 - 4*m11*m33) - 3*m13*(m24*m32 - 4*m11*m34) + (3 + 4*m11)*(m24*m33 - m23*m34))*exp(Z2))/3.;
	
	TY_qa22 = m14*(-(m23*m42*Z1) + 4*m11*m43*Z1 - m33*(m42 + 4*m11*Z2) + m32*(m43 + m23*Z2)) + 
		   (3*m13*(m24*m42*Z1 - 4*m11*m44*Z1 + m34*(m42 + 4*m11*Z2) - m32*(m44 + m24*Z2)) + 
		   (3 + 4*m11)*(-(m24*m43*Z1) + m23*m44*Z1 - m34*(m43 + m23*Z2) + m33*(m44 + m24*Z2)))/3.;	
	
	TY_qa23 = 2*phi*pow(Z2,-2)*(m24*(2*(-3*m13*m42 + 3*m43 + 4*m11*m43)*Z1*pow(Z2,2) - m33*(Z1 + Z2)*(6*m42 + (3 + 4*m11)*pow(Z2,2)) + 
		   3*m32*(Z1 + Z2)*(2*m43 + m13*pow(Z2,2))) + 
		   m23*(2*(3*m14*m42 - 3*m44 - 4*m11*m44)*Z1*pow(Z2,2) + m34*(Z1 + Z2)*(6*m42 + (3 + 4*m11)*pow(Z2,2)) - 
		   3*m32*(Z1 + Z2)*(2*m44 + m14*pow(Z2,2))) + 
		   2*(3*(m14*m33*m42 - m13*m34*m42 - m14*m32*m43 + m34*m43 + m13*m32*m44 - m33*m44)*Z2*(Z1 + Z2) + 
		   2*m11*(6*(-(m14*m43) + m13*m44)*Z1*pow(Z2,2) + m34*(Z1 + Z2)*(2*m43*(-3 + Z2) - 3*m13*pow(Z2,2)) + 
		  m33*(Z1 + Z2)*(6*m44 - 2*m44*Z2 + 3*m14*pow(Z2,2)))))*pow(Z1 + Z2,-1);	
	
	TY_qa32 = 2*phi*pow(Z1,-2)*(m24*((-3*m13*m42 + (3 + 4*m11)*m43)*(Z1 + Z2)*pow(Z1,2) - 
		   2*m33*(3*m42*(Z1 + Z2) + (3 + 4*m11)*Z2*pow(Z1,2)) + 6*m32*(m43*(Z1 + Z2) + m13*Z2*pow(Z1,2))) + 
		   m23*((3*m14*m42 - (3 + 4*m11)*m44)*(Z1 + Z2)*pow(Z1,2) + m34*(6*m42*(Z1 + Z2) + 2*(3 + 4*m11)*Z2*pow(Z1,2)) - 
		   6*m32*(m44*(Z1 + Z2) + m14*Z2*pow(Z1,2))) + 
		   2*(3*(m14*m33*m42 - m13*m34*m42 - m14*m32*m43 + m34*m43 + m13*m32*m44 - m33*m44)*Z1*(Z1 + Z2) + 
		   2*m11*(-3*(m14*m43 - m13*m44)*(Z1 + Z2)*pow(Z1,2) + 2*m34*(m43*(-3 + Z1)*(Z1 + Z2) - 3*m13*Z2*pow(Z1,2)) + 
		  m33*(-2*m44*(-3 + Z1)*(Z1 + Z2) + 6*m14*Z2*pow(Z1,2)))))*pow(Z1 + Z2,-1);
/*		
	if( debug ) 
	{
		sprintf(buf,"\rDet_a = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t%f\t%f\r%f\t%f\t%f\r%f\t%f\t%f\r", 
			   0., TY_qa12, 0., 
			   TY_qa21, TY_qa22, TY_qa23, 
			   0.,    TY_qa32, 0. );
		XOPNotice(buf);
	}
*/
	
	/* Matrix representation of the determinant of the of the system where row refering to 
	 the variable b is replaced by solution vector */
	
	TY_qb12 = (K1*(-3*m11*m24*m43 + m14*(-3*m23*m41 + (-3 + 8*m11)*m43) + 3*m11*m23*m44 + m13*(3*m24*m41 + 3*m44 - 8*m11*m44))*exp(Z1))/3.;
	
	TY_qb21 = (K2*(-3*m13*m24*m31 + 3*m11*m24*m33 + m14*(3*m23*m31 + (3 - 8*m11)*m33) - 3*m13*m34 + 8*m11*m13*m34 - 3*m11*m23*m34)*
			exp(Z2))/3.;
	
	TY_qb22 = m13*(m31*m44 - m24*m41*Z1 - m44*Z1 + (8*m11*m44*Z1)/3. + m24*m31*Z2 + m34*(-m41 + Z2 - (8*m11*Z2)/3.)) + 
		   m14*(m23*m41*Z1 + m43*Z1 - (8*m11*m43*Z1)/3. + m33*(m41 - Z2 + (8*m11*Z2)/3.) - m31*(m43 + m23*Z2)) + 
		   m11*(m24*m43*Z1 - m23*m44*Z1 + m34*(m43 + m23*Z2) - m33*(m44 + m24*Z2));	
	
	TY_qb23 = 2*phi*(3*m14*m23*m31 - 3*m13*m24*m31 + 3*m14*m33 - 8*m11*m14*m33 + 3*m11*m24*m33 - 3*m13*m34 + 8*m11*m13*m34 - 
		   3*m11*m23*m34 + 2*(3*m24*(m33*m41 - m31*m43) + m23*(-3*m34*m41 + 3*m31*m44) + (-3 + 8*m11)*(m34*m43 - m33*m44))*
		   pow(Z2,-2) + 6*(-(m14*m33*m41) + m13*m34*m41 + m14*m31*m43 - m11*m34*m43 - m13*m31*m44 + m11*m33*m44)*pow(Z2,-1) + 
		   2*(-3*m11*m24*m43 + m14*(-3*m23*m41 + (-3 + 8*m11)*m43) + 3*m11*m23*m44 + m13*(3*m24*m41 + 3*m44 - 8*m11*m44))*Z1*
		   pow(Z1 + Z2,-1));
	
	TY_qb32 = 2*phi*pow(Z1,-2)*(6*(-(m34*(m23*m41 + m43)) + m24*(m33*m41 - m31*m43) + (m23*m31 + m33)*m44) + 
		   6*(-(m14*m33*m41) + m13*m34*m41 + m14*m31*m43 - m13*m31*m44)*Z1 + 
		   3*(m14*(2*m23*m31 + 2*m33 - m23*m41 - m43) + m13*(-2*m34 + m24*(-2*m31 + m41) + m44))*pow(Z1,2) + 
		   (m11*Z2*(16*m34*m43 - 16*m33*m44 - 6*m34*m43*Z1 + 6*m33*m44*Z1 + 
		   (6*m24*m33 - 3*m24*m43 + 8*m14*(-2*m33 + m43) + (8*m13 - 3*m23)*(2*m34 - m44))*pow(Z1,2)) + 
		   m11*Z1*(2*m34*m43*(8 - 3*Z1) + 2*m33*m44*(-8 + 3*Z1) + (8*m14*m43 - 3*m24*m43 - 8*m13*m44 + 3*m23*m44)*pow(Z1,2)))*
		   pow(Z1 + Z2,-1) + 6*(-(m14*(m23*m31 + m33)) + m13*(m24*m31 + m34))*pow(Z1,3)*pow(Z1 + Z2,-1));
/*		
	if( debug ) 
	{
		sprintf(buf,"\rDet_b = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t%f\t%f\r%f\t%f\t%f\r%f\t%f\t%f\r", 
			   0., TY_qb12, 0.,
			   TY_qb21, TY_qb22, TY_qb23,
			   0., TY_qb32, 0. );
		XOPNotice(buf);
	}
*/
	
	/* Matrix representation of the determinant of the of the system where row refering to 
	 the variable c1 is replaced by solution vector */
	
	TY_qc112 = -(K1*exp(Z1)*(9*m24*m41 - 9*m14*m42 + 3*m11*(-12*m14*m41 + 4*m24*m41 + 8*m14*m42 - 3*m24*m42) + m44*pow(3 - 2*m11,2)))/9.;
	
	TY_qc121 = (K2*exp(Z2)*(9*m24*m31 - 9*m14*m32 + 3*m11*(-12*m14*m31 + 4*m24*m31 + 8*m14*m32 - 3*m24*m32) + m34*pow(3 - 2*m11,2)))/9.;
	
	TY_qc122 = m14*(-4*m11*m41*Z1 - m42*Z1 + (8*m11*m42*Z1)/3. + m32*(-m41 + Z2 - (8*m11*Z2)/3.) + m31*(m42 + 4*m11*Z2)) + 
			(3*m34*((3 + 4*m11)*m41 - 3*m11*m42) + 9*m11*m32*m44 + 9*m24*m41*Z1 + 12*m11*m24*m41*Z1 - 9*m11*m24*m42*Z1 + 9*m44*Z1 - 
			12*m11*m44*Z1 + 9*m11*m24*m32*Z2 - 3*(3 + 4*m11)*m31*(m44 + m24*Z2) - m34*Z2*pow(3 - 2*m11,2) + 4*m44*Z1*pow(m11,2))/9.;
	
	TY_qc123 = (2*phi*pow(Z2,-2)*(9*(m34*(Z1 + Z2)*(2*m42 + Z2*(-2*m41 + Z2)) - m32*(Z1 + Z2)*(2*m44 + m14*Z2*(-2*m41 + Z2)) - 
			2*(m14*m42 - m44)*Z2*(-(Z1*Z2) + m31*(Z1 + Z2))) + 4*(-2*m44*Z1 + m34*(Z1 + Z2))*pow(m11,2)*pow(Z2,2) - 
			3*m24*(2*(3*m41 + 4*m11*m41 - 3*m11*m42)*Z1*pow(Z2,2) + 3*m32*(Z1 + Z2)*(2*m41 + m11*pow(Z2,2)) - 
			m31*(Z1 + Z2)*(6*m42 + (3 + 4*m11)*pow(Z2,2))) - 
			6*m11*(-8*m32*m44*Z1 + m32*m44*(-8 + 3*Z1)*Z2 + (3*m32*m44 - 4*(m14*(m32 + 3*m41 - 2*m42) + m44)*Z1)*pow(Z2,2) + 
			m34*(Z1 + Z2)*(8*m42 + 4*m41*(-3 + Z2) - 3*m42*Z2 + 2*pow(Z2,2)) + 2*m31*(Z1 + Z2)*(6*m44 - 2*m44*Z2 + 3*m14*pow(Z2,2)) - 
			4*m14*m32*pow(Z2,3)))*pow(Z1 + Z2,-1))/3.;
	
	TY_qc132 = (-2*phi*pow(Z1,-2)*(9*((m14*m42 - m44)*(2*m31 - Z1)*Z1*(Z1 + Z2) - 2*m34*(m42*(Z1 + Z2) - Z1*(-(Z1*Z2) + m41*(Z1 + Z2))) + 
			2*m32*(m44*(Z1 + Z2) - m14*Z1*(-(Z1*Z2) + m41*(Z1 + Z2)))) + 4*(-2*m34*Z2 + m44*(Z1 + Z2))*pow(m11,2)*pow(Z1,2) + 
			3*m24*(((3 + 4*m11)*m41 - 3*m11*m42)*(Z1 + Z2)*pow(Z1,2) + 6*m32*(m41*(Z1 + Z2) + m11*Z2*pow(Z1,2)) - 
			2*m31*(3*m42*(Z1 + Z2) + (3 + 4*m11)*Z2*pow(Z1,2))) + 
			6*m11*(Z1*(-8*m32*m44 + m34*(m42*(8 - 3*Z1) + 4*m41*(-3 + Z1)) - 4*m31*m44*(-3 + Z1) + 3*m32*m44*Z1 - 
			2*(3*m14*m41 - 2*m14*m42 + m44)*pow(Z1,2)) + 
			Z2*(4*(3*m31 - 2*m32)*m44 + Z1*(-4*m31*m44 + 3*m32*m44 - 2*(m14*(-6*m31 + 4*m32 + 3*m41 - 2*m42) + m44)*Z1) + 
			m34*(m42*(8 - 3*Z1) + 4*m41*(-3 + Z1) + 4*pow(Z1,2)))))*pow(Z1 + Z2,-1))/3.;
/*		
	if( debug ) 
	{
		sprintf(buf,"\rDet_c1 = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t%f\t%f\r%f\t%f\t%f\r%f\t%f\t%f\r", 
			    0., TY_qc112, 0., 
			   TY_qc121, TY_qc122, TY_qc123,
			   0., TY_qc132, 0. );
		XOPNotice(buf);
	}
 */
	/* Matrix representation of the determinant of the of the system where row refering to 
	 the variable c1 is replaced by solution vector */
	
	TY_qc212 = (K1*exp(Z1)*(9*m23*m41 - 9*m13*m42 + 3*m11*(-12*m13*m41 + 4*m23*m41 + 8*m13*m42 - 3*m23*m42) + m43*pow(3 - 2*m11,2)))/9.;
	
	TY_qc221 = -(K2*exp(Z2)*(9*m23*m31 - 9*m13*m32 + 3*m11*(-12*m13*m31 + 4*m23*m31 + 8*m13*m32 - 3*m23*m32) + m33*pow(3 - 2*m11,2)))/9.;
	
	TY_qc222 = m13*(4*m11*m41*Z1 + m42*Z1 - (8*m11*m42*Z1)/3. + m32*(m41 - Z2 + (8*m11*Z2)/3.) - m31*(m42 + 4*m11*Z2)) + 
			(9*m31*m43 - 9*(m23*m41 + m43)*Z1 + 9*m23*m31*Z2 + 3*m11*
			((-4*m23*m41 + 3*m23*m42 + 4*m43)*Z1 + 4*m31*(m43 + m23*Z2) - 3*m32*(m43 + m23*Z2)) + 
			m33*(-3*(3 + 4*m11)*m41 + 9*m11*m42 + Z2*pow(3 - 2*m11,2)) - 4*m43*Z1*pow(m11,2))/9.;
	
	TY_qc223 = (2*phi*pow(Z2,-2)*(9*(-(m33*(Z1 + Z2)*(2*m42 + Z2*(-2*m41 + Z2))) + m32*(Z1 + Z2)*(2*m43 + m13*Z2*(-2*m41 + Z2)) + 
			2*(m13*m42 - m43)*Z2*(-(Z1*Z2) + m31*(Z1 + Z2))) - 4*(-2*m43*Z1 + m33*(Z1 + Z2))*pow(m11,2)*pow(Z2,2) + 
			3*m23*(2*(3*m41 + 4*m11*m41 - 3*m11*m42)*Z1*pow(Z2,2) + 3*m32*(Z1 + Z2)*(2*m41 + m11*pow(Z2,2)) - 
			m31*(Z1 + Z2)*(6*m42 + (3 + 4*m11)*pow(Z2,2))) + 
			6*m11*(-8*m32*m43*Z1 + m32*m43*(-8 + 3*Z1)*Z2 + (3*m32*m43 - 4*(m13*(m32 + 3*m41 - 2*m42) + m43)*Z1)*pow(Z2,2) + 
			m33*(Z1 + Z2)*(8*m42 + 4*m41*(-3 + Z2) - 3*m42*Z2 + 2*pow(Z2,2)) + 2*m31*(Z1 + Z2)*(6*m43 - 2*m43*Z2 + 3*m13*pow(Z2,2)) - 
			4*m13*m32*pow(Z2,3)))*pow(Z1 + Z2,-1))/3.;
	
	TY_qc232 = (2*phi*pow(Z1,-2)*(9*((m13*m42 - m43)*(2*m31 - Z1)*Z1*(Z1 + Z2) - 2*m33*(m42*(Z1 + Z2) - Z1*(-(Z1*Z2) + m41*(Z1 + Z2))) + 
			2*m32*(m43*(Z1 + Z2) - m13*Z1*(-(Z1*Z2) + m41*(Z1 + Z2)))) + 4*(-2*m33*Z2 + m43*(Z1 + Z2))*pow(m11,2)*pow(Z1,2) + 
			3*m23*(((3 + 4*m11)*m41 - 3*m11*m42)*(Z1 + Z2)*pow(Z1,2) + 6*m32*(m41*(Z1 + Z2) + m11*Z2*pow(Z1,2)) - 
			2*m31*(3*m42*(Z1 + Z2) + (3 + 4*m11)*Z2*pow(Z1,2))) + 
			6*m11*(Z1*(-8*m32*m43 + m33*(m42*(8 - 3*Z1) + 4*m41*(-3 + Z1)) - 4*m31*m43*(-3 + Z1) + 3*m32*m43*Z1 - 
			2*(3*m13*m41 - 2*m13*m42 + m43)*pow(Z1,2)) + 
			Z2*(4*(3*m31 - 2*m32)*m43 + Z1*(-4*m31*m43 + 3*m32*m43 - 2*(m13*(-6*m31 + 4*m32 + 3*m41 - 2*m42) + m43)*Z1) + 
			m33*(m42*(8 - 3*Z1) + 4*m41*(-3 + Z1) + 4*pow(Z1,2)))))*pow(Z1 + Z2,-1))/3.;
/*		
	if( debug ) 
	{
		sprintf(buf,"\rDet_c2 = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t%f\t%f\r%f\t%f\t%f\r%f\t%f\t%f\r", 
			   0., TY_qc212, 0., 
			   TY_qc221, TY_qc222, TY_qc223, 
			   0., TY_qc232, 0. );
		XOPNotice(buf);
	}	
*/
	
	/* coefficient matrices of nonlinear equation 1 */
	
	TY_A12 = 6*phi*TY_qc112*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*TY_qc212*exp(Z1)*(-Z2 + (Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(exp(2*Z1)*(Z1*(2*TY_qb12*(-1 + Z1)*(Z1 + Z2) - Z1*(2*TY_qc212*Z1 + TY_qc112*(Z1 + Z2))) + TY_qa12*(Z1 + Z2)*(-2 + pow(Z1,2))) - 
		  TY_qc112*(Z1 + Z2)*pow(Z1,2) + 2*(Z1 + Z2)*exp(Z1)*(TY_qa12 + (TY_qa12 + TY_qb12)*Z1 + TY_qc112*pow(Z1,2))))*pow(Z1 + Z2,-1);
	
	TY_A21 = 6*phi*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*(TY_qc121*TY_qc212 + TY_qc112*TY_qc221)*exp(Z1)*(-Z2 + (Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(2*(TY_qa12*TY_qc121 + TY_qa21*TY_qc112*(1 + Z1) + Z1*(TY_qb21*TY_qc112 + TY_qc121*(TY_qa12 + TY_qb12 + 2*TY_qc112*Z1)))*(Z1 + Z2)*exp(Z1) + 
		  exp(2*Z1)*(2*Z1*(TY_qb21*TY_qc112*(-1 + Z1)*(Z1 + Z2) + TY_qb12*TY_qc121*(-1 + Z1)*(Z1 + Z2) - 
		  Z1*(TY_qc121*TY_qc212*Z1 + TY_qc112*(TY_qc121 + TY_qc221)*Z1 + TY_qc112*TY_qc121*Z2)) + TY_qa21*TY_qc112*(Z1 + Z2)*(-2 + pow(Z1,2)) + 
		  TY_qa12*TY_qc121*(Z1 + Z2)*(-2 + pow(Z1,2))) - 2*TY_qc112*TY_qc121*(Z1 + Z2)*pow(Z1,2)))*pow(Z1 + Z2,-1);
	
	TY_A22 = exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(12*phi*(TY_qc122*TY_qc212 + TY_qc112*TY_qc222)*exp(Z1)*(-Z2 + (Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(12*phi*(TY_qa12*TY_qc122 + TY_qa22*TY_qc112*(1 + Z1) + Z1*(TY_qb22*TY_qc112 + TY_qc122*(TY_qa12 + TY_qb12 + 2*TY_qc112*Z1)))*(Z1 + Z2)*exp(Z1) - 
		  2*phi*TY_qc112*TY_qc122*(Z1 + Z2)*pow(Z1,2) + exp(2*Z1)*
		  (6*phi*(2*Z1*(TY_qb22*TY_qc112*(-1 + Z1)*(Z1 + Z2) + TY_qb12*TY_qc122*(-1 + Z1)*(Z1 + Z2) - 
		  Z1*(TY_qc122*TY_qc212*Z1 + TY_qc112*(TY_qc122 + TY_qc222)*Z1 + TY_qc112*TY_qc122*Z2)) + TY_qa22*TY_qc112*(Z1 + Z2)*(-2 + pow(Z1,2)) + 
		  TY_qa12*TY_qc122*(Z1 + Z2)*(-2 + pow(Z1,2))) + TY_q22*TY_qc112*(Z1 + Z2)*pow(Z1,3))))*pow(Z1 + Z2,-1);
	
	TY_A23 = 6*phi*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*(TY_qc123*TY_qc212 + TY_qc112*TY_qc223)*exp(Z1)*(-Z2 + (Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(2*(TY_qa12*TY_qc123 + TY_qa23*TY_qc112*(1 + Z1) + Z1*(TY_qb23*TY_qc112 + TY_qc123*(TY_qa12 + TY_qb12 + 2*TY_qc112*Z1)))*(Z1 + Z2)*exp(Z1) + 
		  exp(2*Z1)*(2*Z1*(TY_qb23*TY_qc112*(-1 + Z1)*(Z1 + Z2) + TY_qb12*TY_qc123*(-1 + Z1)*(Z1 + Z2) - 
		  Z1*((TY_q22*TY_qc112 + TY_qc123*(TY_qc112 + TY_qc212) + TY_qc112*TY_qc223)*Z1 + TY_qc112*TY_qc123*Z2)) + TY_qa23*TY_qc112*(Z1 + Z2)*(-2 + pow(Z1,2)) + 
		  TY_qa12*TY_qc123*(Z1 + Z2)*(-2 + pow(Z1,2))) - 2*TY_qc112*TY_qc123*(Z1 + Z2)*pow(Z1,2)))*pow(Z1 + Z2,-1);
	
	TY_A32 = exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(12*phi*(TY_qa23*TY_qc121 + TY_qa22*TY_qc122 + TY_qa21*TY_qc123 + TY_qa12*TY_qc132 + TY_qa32*TY_qc112*(1 + Z1) + 
		  Z1*(TY_qb32*TY_qc112 + (TY_qa23 + TY_qb23)*TY_qc121 + (TY_qa21 + TY_qb21)*TY_qc123 + (TY_qa12 + TY_qb12)*TY_qc132 + TY_q22*TY_qc112*Z1 + 
		  2*(TY_qc121*TY_qc123 + TY_qc112*TY_qc132)*Z1 + TY_qc122*(TY_qa22 + TY_qb22 + TY_qc122*Z1)))*(Z1 + Z2)*exp(Z1 + Z2) - 
		  12*phi*(TY_qc132*TY_qc212 + TY_qc123*TY_qc221 + TY_qc122*TY_qc222 + TY_qc121*TY_qc223 + TY_qc112*TY_qc232)*Z2*exp(Z1)*pow(Z1,2) + 
		  12*phi*((TY_q22 + TY_qc132)*TY_qc212 + TY_qc123*TY_qc221 + TY_qc122*TY_qc222 + TY_qc121*TY_qc223 + TY_qc112*TY_qc232)*(Z1 + Z2)*exp(2*Z1)*pow(Z1,2) - 
		  6*phi*(Z1 + Z2)*exp(Z2)*(2*TY_qc121*TY_qc123 + 2*TY_qc112*TY_qc132 + pow(TY_qc122,2))*pow(Z1,2) + 
		  exp(2*Z1 + Z2)*(TY_q22*(6*phi*(2*Z1*(TY_qb12*(-1 + Z1)*(Z1 + Z2) - Z1*((TY_qc112 + TY_qc121 + TY_qc212)*Z1 + TY_qc112*Z2)) + 
		  TY_qa12*(Z1 + Z2)*(-2 + pow(Z1,2))) + TY_qc122*(Z1 + Z2)*pow(Z1,3)) + 
		  6*phi*(-2*TY_qa22*TY_qc122*Z1 - 2*TY_qa21*TY_qc123*Z1 - 2*TY_qa12*TY_qc132*Z1 + TY_qa32*TY_qc112*(Z1 + Z2)*(-2 + pow(Z1,2)) + 
		  TY_qa23*TY_qc121*(Z1 + Z2)*(-2 + pow(Z1,2)) - 2*TY_qb32*TY_qc112*pow(Z1,2) - 2*TY_qb23*TY_qc121*pow(Z1,2) - 2*TY_qb22*TY_qc122*pow(Z1,2) - 
		  2*TY_qb21*TY_qc123*pow(Z1,2) - 2*TY_qb12*TY_qc132*pow(Z1,2) + 
		  Z2*(-2*(TY_qa22*TY_qc122 + TY_qa21*TY_qc123 + TY_qa12*TY_qc132) - 2*(TY_qb32*TY_qc112 + TY_qb23*TY_qc121 + TY_qb22*TY_qc122 + TY_qb21*TY_qc123 + TY_qb12*TY_qc132)*Z1 + 
		  (2*TY_qb32*TY_qc112 + 2*TY_qb23*TY_qc121 + (TY_qa22 + 2*TY_qb22 - TY_qc122)*TY_qc122 + (TY_qa21 + 2*TY_qb21 - 2*TY_qc121)*TY_qc123 + 
		  (TY_qa12 + 2*TY_qb12 - 2*TY_qc112)*TY_qc132)*pow(Z1,2)) + 2*TY_qb32*TY_qc112*pow(Z1,3) + 2*TY_qb23*TY_qc121*pow(Z1,3) + TY_qa22*TY_qc122*pow(Z1,3) + 
		  2*TY_qb22*TY_qc122*pow(Z1,3) + TY_qa21*TY_qc123*pow(Z1,3) + 2*TY_qb21*TY_qc123*pow(Z1,3) - 2*TY_qc121*TY_qc123*pow(Z1,3) + TY_qa12*TY_qc132*pow(Z1,3) + 
		  2*TY_qb12*TY_qc132*pow(Z1,3) - 2*TY_qc112*TY_qc132*pow(Z1,3) - 2*TY_qc132*TY_qc212*pow(Z1,3) - 2*TY_qc123*TY_qc221*pow(Z1,3) - 
		  2*TY_qc122*TY_qc222*pow(Z1,3) - 2*TY_qc121*TY_qc223*pow(Z1,3) - 2*TY_qc112*TY_qc232*pow(Z1,3) - pow(TY_qc122,2)*pow(Z1,3))))*pow(Z1 + Z2,-1);
	
	TY_A41 = 6*phi*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*exp(Z1)*
		  ((-(TY_qc132*TY_qc221) - TY_qc121*TY_qc232)*Z2 + ((TY_q22 + TY_qc132)*TY_qc221 + TY_qc121*TY_qc232)*(Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(2*(TY_qa21*TY_qc132 + TY_qa32*TY_qc121*(1 + Z1) + Z1*(TY_qb32*TY_qc121 + (TY_qa21 + TY_qb21)*TY_qc132 + TY_qc121*(TY_q22 + 2*TY_qc132)*Z1))*(Z1 + Z2)*
		  exp(Z1) - 2*TY_qc121*TY_qc132*(Z1 + Z2)*pow(Z1,2) + 
		  exp(2*Z1)*(Z2*(-2*(TY_qa32*TY_qc121 + TY_qa21*(TY_q22 + TY_qc132)) - 2*(TY_qb32*TY_qc121 + TY_qb21*(TY_q22 + TY_qc132))*Z1 + 
		  (TY_q22*(TY_qa21 + 2*TY_qb21 - 2*TY_qc121) + TY_qc121*(TY_qa32 + 2*TY_qb32 - 2*TY_qc132) + (TY_qa21 + 2*TY_qb21)*TY_qc132)*pow(Z1,2)) + 
		  Z1*(-2*(TY_qa32*TY_qc121 + TY_qa21*(TY_q22 + TY_qc132)) - 2*(TY_qb32*TY_qc121 + TY_qb21*(TY_q22 + TY_qc132))*Z1 + 
		  (TY_qa32*TY_qc121 + 2*TY_qb32*TY_qc121 + TY_qa21*TY_qc132 + 2*TY_qb21*TY_qc132 - 2*TY_qc121*TY_qc132 + TY_q22*(TY_qa21 + 2*TY_qb21 - 2*TY_qc121 - 2*TY_qc221) - 
		  2*TY_qc132*TY_qc221 - 2*TY_qc121*TY_qc232)*pow(Z1,2)))))*pow(Z1 + Z2,-1);
	
	TY_A42 = exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(12*phi*(TY_qa22*TY_qc132 + TY_qa32*TY_qc122*(1 + Z1) + 
		  Z1*(TY_qb32*TY_qc122 + (TY_qa22 + TY_qb22)*TY_qc132 + TY_qc122*(TY_q22 + 2*TY_qc132)*Z1))*(Z1 + Z2)*exp(Z1 + Z2) - 
		  12*phi*(TY_qc132*TY_qc222 + TY_qc122*TY_qc232)*Z2*exp(Z1)*pow(Z1,2) + 
		  12*phi*((TY_q22 + TY_qc132)*TY_qc222 + TY_qc122*TY_qc232)*(Z1 + Z2)*exp(2*Z1)*pow(Z1,2) - 12*phi*TY_qc122*TY_qc132*(Z1 + Z2)*exp(Z2)*pow(Z1,2) + 
		  exp(2*Z1 + Z2)*(6*phi*(2*Z1*(TY_qb32*TY_qc122*(-1 + Z1)*(Z1 + Z2) + TY_qb22*TY_qc132*(-1 + Z1)*(Z1 + Z2) - 
		  Z1*(TY_qc132*TY_qc222*Z1 + TY_qc122*(TY_qc132 + TY_qc232)*Z1 + TY_qc122*TY_qc132*Z2)) + TY_qa32*TY_qc122*(Z1 + Z2)*(-2 + pow(Z1,2)) + 
		  TY_qa22*TY_qc132*(Z1 + Z2)*(-2 + pow(Z1,2))) + (Z1 + Z2)*pow(TY_q22,2)*pow(Z1,3) + 
		  TY_q22*(6*phi*(2*Z1*(TY_qb22*(-1 + Z1)*(Z1 + Z2) - Z1*((TY_qc122 + TY_qc222)*Z1 + TY_qc122*Z2)) + TY_qa22*(Z1 + Z2)*(-2 + pow(Z1,2))) + 
		  TY_qc132*(Z1 + Z2)*pow(Z1,3))))*pow(Z1 + Z2,-1);
	
	TY_A43 = -6*phi*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*exp(Z1)*
		  ((TY_qc132*TY_qc223 + TY_qc123*TY_qc232)*Z2 - ((TY_q22 + TY_qc132)*TY_qc223 + TY_qc123*TY_qc232)*(Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*(-2*(TY_qa23*TY_qc132 + TY_qa32*TY_qc123*(1 + Z1) + Z1*(TY_qb32*TY_qc123 + (TY_qa23 + TY_qb23)*TY_qc132 + TY_qc123*(TY_q22 + 2*TY_qc132)*Z1))*(Z1 + Z2)*
		  exp(Z1) + 2*TY_qc123*TY_qc132*(Z1 + Z2)*pow(Z1,2) + 
		  exp(2*Z1)*(Z2*(2*TY_qa32*TY_qc123 + 2*TY_qa23*(TY_q22 + TY_qc132) + 2*(TY_qb32*TY_qc123 + TY_qb23*(TY_q22 + TY_qc132))*Z1 - 
		  (TY_q22*(TY_qa23 + 2*TY_qb23 - 2*TY_qc123) + TY_qc123*(TY_qa32 + 2*TY_qb32 - 2*TY_qc132) + (TY_qa23 + 2*TY_qb23)*TY_qc132)*pow(Z1,2)) + 
		  Z1*(2*TY_qa32*TY_qc123 + 2*TY_qa23*(TY_q22 + TY_qc132) + 2*(TY_qb32*TY_qc123 + TY_qb23*(TY_q22 + TY_qc132))*Z1 + 
		  (-(TY_qa32*TY_qc123) - (TY_qa23 + 2*TY_qb23)*TY_qc132 + TY_q22*(-TY_qa23 + 2*(-TY_qb23 + TY_qc123 + TY_qc132 + TY_qc223)) + 
		  2*(-(TY_qb32*TY_qc123) + TY_qc132*(TY_qc123 + TY_qc223) + TY_qc123*TY_qc232) + 2*pow(TY_q22,2))*pow(Z1,2)))))*pow(Z1 + Z2,-1);
	
	TY_A52 = -6*phi*exp(-2*Z1 - Z2)*pow(TY_q22,-2)*pow(Z1,-3)*(2*TY_qc232*exp(Z1)*(TY_qc132*Z2 - (TY_q22 + TY_qc132)*(Z1 + Z2)*exp(Z1))*pow(Z1,2) + 
		  exp(Z2)*((TY_q22 + TY_qc132)*exp(2*Z1)*(Z1*(-2*TY_qb32*(-1 + Z1)*(Z1 + Z2) + Z1*((TY_q22 + TY_qc132 + 2*TY_qc232)*Z1 + (TY_q22 + TY_qc132)*Z2)) - 
		  TY_qa32*(Z1 + Z2)*(-2 + pow(Z1,2))) + (Z1 + Z2)*pow(TY_qc132,2)*pow(Z1,2) - 
		  2*TY_qc132*(Z1 + Z2)*exp(Z1)*(TY_qa32 + (TY_qa32 + TY_qb32)*Z1 + (TY_q22 + TY_qc132)*pow(Z1,2))))*pow(Z1 + Z2,-1);
	
	// normalize A
	/*double norm_A = sqrt(pow(TY_A52,2)+pow(TY_A43,2)+pow(TY_A42, 2)+pow(TY_A41, 2)+pow(TY_A32, 2)+
						 pow(TY_A23,2)+pow(TY_A22,2)+pow(TY_A21, 2)+pow(TY_A12, 2));
	TY_A12 /= norm_A;
	TY_A21 /= norm_A;
	TY_A22 /= norm_A;
	TY_A23 /= norm_A;
	TY_A32 /= norm_A;
	TY_A41 /= norm_A;
	TY_A42 /= norm_A;
	TY_A43 /= norm_A;
	TY_A52 /= norm_A;*/
/*	
	if( debug ) 
	{
		sprintf(buf,"\rNonlinear equation 1 = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\r", 0.,   TY_A12, 0.   );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\r", TY_A21, TY_A22, TY_A23 );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\r",  0.,  TY_A32, 0.   );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\r", TY_A41, TY_A42, TY_A43 );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\r", 0.,   TY_A52, 0. );		
		XOPNotice(buf);
	}
 */
	
	/* coefficient matrices of nonlinear equation 2 */
	
	TY_B12 = 6*phi*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-2*TY_qc212*TY_qc221*(Z1 + Z2)*exp(Z1)*pow(Z2,2) + 
		  2*exp(Z2)*((Z1 + Z2)*(TY_qa12*TY_qc221 + TY_qa21*TY_qc212*(1 + Z2) + Z2*(TY_qb21*TY_qc212 + TY_qc221*(TY_qa12 + TY_qb12 + 2*TY_qc212*Z2)))*exp(Z1) + 
		  (-(TY_qc121*TY_qc212) - TY_qc112*TY_qc221)*Z1*pow(Z2,2)) + 
		  exp(2*Z2)*(exp(Z1)*(2*Z2*(TY_qb21*TY_qc212*(-1 + Z2)*(Z1 + Z2) + TY_qb12*TY_qc221*(-1 + Z2)*(Z1 + Z2) - 
		  Z2*(TY_qc212*TY_qc221*Z1 + TY_qc112*TY_qc221*Z2 + TY_qc212*(TY_qc121 + TY_qc221)*Z2)) + TY_qa21*TY_qc212*(Z1 + Z2)*(-2 + pow(Z2,2)) + 
		  TY_qa12*TY_qc221*(Z1 + Z2)*(-2 + pow(Z2,2))) + 2*(TY_qc121*TY_qc212 + TY_qc112*TY_qc221)*(Z1 + Z2)*pow(Z2,2)))*pow(Z1 + Z2,-1);
	
	TY_B14 = 6*phi*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-2*TY_qc212*TY_qc223*(Z1 + Z2)*exp(Z1)*pow(Z2,2) + 
		  2*exp(Z2)*((Z1 + Z2)*(TY_qa12*TY_qc223 + TY_qa23*TY_qc212*(1 + Z2) + Z2*(TY_qb23*TY_qc212 + (TY_qa12 + TY_qb12)*TY_qc223 + TY_qc212*(TY_q22 + 2*TY_qc223)*Z2))*
		  exp(Z1) + (-(TY_qc123*TY_qc212) - TY_qc112*TY_qc223)*Z1*pow(Z2,2)) + 
		  exp(2*Z2)*(2*(TY_qc123*TY_qc212 + TY_qc112*(TY_q22 + TY_qc223))*(Z1 + Z2)*pow(Z2,2) + 
		  exp(Z1)*(-2*(TY_qa23*TY_qc212 + TY_qa12*(TY_q22 + TY_qc223))*Z1 - 
		  2*(TY_qa23*TY_qc212 + TY_qa12*(TY_q22 + TY_qc223) + (TY_qb23*TY_qc212 + TY_qb12*(TY_q22 + TY_qc223))*Z1)*Z2 + 
		  (-2*(TY_qb23*TY_qc212 + TY_qb12*(TY_q22 + TY_qc223)) + (TY_q22*(TY_qa12 + 2*TY_qb12 - 2*TY_qc212) + TY_qc212*(TY_qa23 + 2*TY_qb23 - 2*TY_qc223) + 
		  (TY_qa12 + 2*TY_qb12)*TY_qc223)*Z1)*pow(Z2,2) + 
		  (TY_q22*(TY_qa12 + 2*TY_qb12 - 2*TY_qc112 - 2*TY_qc212) + TY_qc212*(TY_qa23 + 2*TY_qb23 - 2*TY_qc123 - 2*TY_qc223) + (TY_qa12 + 2*TY_qb12 - 2*TY_qc112)*TY_qc223)*
		  pow(Z2,3))))*pow(Z1 + Z2,-1);
	
	TY_B21 = 6*phi*TY_qc221*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-(TY_qc221*(Z1 + Z2)*exp(Z1)*pow(Z2,2)) + 
		  exp(2*Z2)*(exp(Z1)*(Z2*(2*TY_qb21*(-1 + Z2)*(Z1 + Z2) - Z2*(2*TY_qc121*Z2 + TY_qc221*(Z1 + Z2))) + TY_qa21*(Z1 + Z2)*(-2 + pow(Z2,2))) + 
		  2*TY_qc121*(Z1 + Z2)*pow(Z2,2)) + 2*exp(Z2)*(-(TY_qc121*Z1*pow(Z2,2)) + (Z1 + Z2)*exp(Z1)*(TY_qa21 + (TY_qa21 + TY_qb21)*Z2 + TY_qc221*pow(Z2,2)))
		  )*pow(Z1 + Z2,-1);
	
	TY_B22 = exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-12*phi*TY_qc221*TY_qc222*(Z1 + Z2)*exp(Z1)*pow(Z2,2) + 
		  12*phi*exp(Z2)*((Z1 + Z2)*(TY_qa21*TY_qc222 + TY_qa22*TY_qc221*(1 + Z2) + Z2*(TY_qb22*TY_qc221 + TY_qc222*(TY_qa21 + TY_qb21 + 2*TY_qc221*Z2)))*exp(Z1) + 
		  (-(TY_qc122*TY_qc221) - TY_qc121*TY_qc222)*Z1*pow(Z2,2)) + 
		  exp(2*Z2)*(12*phi*(TY_qc122*TY_qc221 + TY_qc121*TY_qc222)*(Z1 + Z2)*pow(Z2,2) + 
		  exp(Z1)*(6*phi*(2*Z2*(TY_qb22*TY_qc221*(-1 + Z2)*(Z1 + Z2) + TY_qb21*TY_qc222*(-1 + Z2)*(Z1 + Z2) - 
		  Z2*(TY_qc221*TY_qc222*Z1 + TY_qc121*TY_qc222*Z2 + TY_qc221*(TY_qc122 + TY_qc222)*Z2)) + TY_qa22*TY_qc221*(Z1 + Z2)*(-2 + pow(Z2,2)) + 
		  TY_qa21*TY_qc222*(Z1 + Z2)*(-2 + pow(Z2,2))) + TY_q22*TY_qc221*(Z1 + Z2)*pow(Z2,3))))*pow(Z1 + Z2,-1);
	
	TY_B23 = exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-6*phi*(Z1 + Z2)*exp(Z1)*(2*TY_qc221*TY_qc223 + 2*TY_qc212*TY_qc232 + pow(TY_qc222,2))*pow(Z2,2) + 
		  12*phi*exp(Z2)*((Z1 + Z2)*exp(Z1)*(TY_qa23*TY_qc221 + TY_qa22*TY_qc222 + TY_qa21*TY_qc223 + TY_qa12*TY_qc232 + TY_qa32*TY_qc212*(1 + Z2) + 
		  Z2*(TY_qb32*TY_qc212 + (TY_qa23 + TY_qb23)*TY_qc221 + (TY_qa22 + TY_qb22)*TY_qc222 + (TY_qa21 + TY_qb21)*TY_qc223 + (TY_qa12 + TY_qb12)*TY_qc232 + 
		  Z2*(TY_q22*TY_qc221 + 2*TY_qc221*TY_qc223 + 2*TY_qc212*TY_qc232 + pow(TY_qc222,2)))) + 
		  (-(TY_qc132*TY_qc212) - TY_qc123*TY_qc221 - TY_qc122*TY_qc222 - TY_qc121*TY_qc223 - TY_qc112*TY_qc232)*Z1*pow(Z2,2)) + 
		  exp(2*Z2)*(12*phi*(TY_qc132*TY_qc212 + TY_qc123*TY_qc221 + TY_qc122*TY_qc222 + TY_qc121*(TY_q22 + TY_qc223) + TY_qc112*TY_qc232)*(Z1 + Z2)*pow(Z2,2) + 
		  exp(Z1)*(TY_q22*TY_qc222*(Z1 + Z2)*pow(Z2,3) - 6*phi*
		  (2*(TY_qa32*TY_qc212 + TY_qa23*TY_qc221 + TY_qa22*TY_qc222 + TY_qa21*(TY_q22 + TY_qc223) + TY_qa12*TY_qc232)*Z1 + 
		  2*(TY_qa32*TY_qc212 + TY_qa23*TY_qc221 + TY_qa22*TY_qc222 + TY_qa21*(TY_q22 + TY_qc223) + TY_qa12*TY_qc232 + 
		  (TY_qb32*TY_qc212 + TY_qb23*TY_qc221 + TY_qb22*TY_qc222 + TY_qb21*(TY_q22 + TY_qc223) + TY_qb12*TY_qc232)*Z1)*Z2 - 
		  (-2*(TY_qb32*TY_qc212 + TY_qb23*TY_qc221 + TY_qb22*TY_qc222 + TY_qb21*(TY_q22 + TY_qc223) + TY_qb12*TY_qc232) + 
		  (TY_q22*(TY_qa21 + 2*TY_qb21 - 2*TY_qc221) + (TY_qa22 + 2*TY_qb22 - TY_qc222)*TY_qc222 + TY_qc221*(TY_qa23 + 2*TY_qb23 - 2*TY_qc223) + TY_qa21*TY_qc223 + 
		  2*TY_qb21*TY_qc223 + TY_qc212*(TY_qa32 + 2*TY_qb32 - 2*TY_qc232) + TY_qa12*TY_qc232 + 2*TY_qb12*TY_qc232)*Z1)*pow(Z2,2) - 
		  (TY_q22*(TY_qa21 + 2*TY_qb21 - 2*TY_qc121 - 2*TY_qc212 - 2*TY_qc221) + (TY_qa22 + 2*TY_qb22 - 2*TY_qc122 - TY_qc222)*TY_qc222 + 
		  TY_qc221*(TY_qa23 + 2*TY_qb23 - 2*TY_qc123 - 2*TY_qc223) + (TY_qa21 + 2*TY_qb21 - 2*TY_qc121)*TY_qc223 + 
		  TY_qc212*(TY_qa32 + 2*TY_qb32 - 2*TY_qc132 - 2*TY_qc232) + (TY_qa12 + 2*TY_qb12 - 2*TY_qc112)*TY_qc232)*pow(Z2,3)))))*pow(Z1 + Z2,-1);
	
	TY_B24 = exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(12*phi*(Z1 + Z2)*
		  (TY_qa22*TY_qc223 + TY_qa23*TY_qc222*(1 + Z2) + Z2*(TY_qb23*TY_qc222 + (TY_qa22 + TY_qb22)*TY_qc223 + TY_qc222*(TY_q22 + 2*TY_qc223)*Z2))*exp(Z1 + Z2) - 
		  12*phi*TY_qc222*TY_qc223*(Z1 + Z2)*exp(Z1)*pow(Z2,2) - 12*phi*(TY_qc123*TY_qc222 + TY_qc122*TY_qc223)*Z1*exp(Z2)*pow(Z2,2) + 
		  12*phi*(TY_qc123*TY_qc222 + TY_qc122*(TY_q22 + TY_qc223))*(Z1 + Z2)*exp(2*Z2)*pow(Z2,2) + 
		  exp(Z1 + 2*Z2)*(6*phi*(2*Z2*(TY_qb23*TY_qc222*(-1 + Z2)*(Z1 + Z2) + TY_qb22*TY_qc223*(-1 + Z2)*(Z1 + Z2) - 
		  Z2*(TY_qc222*TY_qc223*Z1 + TY_qc122*TY_qc223*Z2 + TY_qc222*(TY_qc123 + TY_qc223)*Z2)) + TY_qa23*TY_qc222*(Z1 + Z2)*(-2 + pow(Z2,2)) + 
		  TY_qa22*TY_qc223*(Z1 + Z2)*(-2 + pow(Z2,2))) + (Z1 + Z2)*pow(TY_q22,2)*pow(Z2,3) + 
		  TY_q22*(6*phi*(2*Z2*(TY_qb22*(-1 + Z2)*(Z1 + Z2) - Z2*(TY_qc222*Z1 + (TY_qc122 + TY_qc222)*Z2)) + TY_qa22*(Z1 + Z2)*(-2 + pow(Z2,2))) + 
		  TY_qc223*(Z1 + Z2)*pow(Z2,3))))*pow(Z1 + Z2,-1);
	
	TY_B25 = -6*phi*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*((Z1 + Z2)*exp(Z1)*pow(TY_qc223,2)*pow(Z2,2) + 
		  (TY_q22 + TY_qc223)*exp(2*Z2)*(exp(Z1)*(Z2*(-2*TY_qb23*(-1 + Z2)*(Z1 + Z2) + Z2*((TY_q22 + TY_qc223)*Z1 + (TY_q22 + 2*TY_qc123 + TY_qc223)*Z2)) - 
		  TY_qa23*(Z1 + Z2)*(-2 + pow(Z2,2))) - 2*TY_qc123*(Z1 + Z2)*pow(Z2,2)) + 
		  2*TY_qc223*exp(Z2)*(TY_qc123*Z1*pow(Z2,2) - (Z1 + Z2)*exp(Z1)*(TY_qa23 + (TY_qa23 + TY_qb23)*Z2 + (TY_q22 + TY_qc223)*pow(Z2,2))))*pow(Z1 + Z2,-1);
	
	TY_B32 = 6*phi*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(-2*TY_qc221*TY_qc232*(Z1 + Z2)*exp(Z1)*pow(Z2,2) + 
		  2*exp(Z2)*((Z1 + Z2)*(TY_qa21*TY_qc232 + TY_qa32*TY_qc221*(1 + Z2) + Z2*(TY_qb32*TY_qc221 + TY_qc232*(TY_qa21 + TY_qb21 + 2*TY_qc221*Z2)))*exp(Z1) + 
		  (-(TY_qc132*TY_qc221) - TY_qc121*TY_qc232)*Z1*pow(Z2,2)) + 
		  exp(2*Z2)*(exp(Z1)*(2*Z2*(TY_qb32*TY_qc221*(-1 + Z2)*(Z1 + Z2) + TY_qb21*TY_qc232*(-1 + Z2)*(Z1 + Z2) - 
		  Z2*(TY_qc221*TY_qc232*Z1 + TY_qc121*TY_qc232*Z2 + TY_qc221*(TY_q22 + TY_qc132 + TY_qc232)*Z2)) + TY_qa32*TY_qc221*(Z1 + Z2)*(-2 + pow(Z2,2)) + 
		  TY_qa21*TY_qc232*(Z1 + Z2)*(-2 + pow(Z2,2))) + 2*(TY_qc132*TY_qc221 + TY_qc121*TY_qc232)*(Z1 + Z2)*pow(Z2,2)))*pow(Z1 + Z2,-1);
	
	TY_B34 = -6*phi*exp(-Z1 - 2*Z2)*pow(TY_q22,-2)*pow(Z2,-3)*(2*TY_qc223*TY_qc232*(Z1 + Z2)*exp(Z1)*pow(Z2,2) + 
		  2*exp(Z2)*(-((Z1 + Z2)*(TY_qa23*TY_qc232 + TY_qa32*TY_qc223*(1 + Z2) + Z2*(TY_qb32*TY_qc223 + TY_qc232*(TY_qa23 + TY_qb23 + TY_q22*Z2 + 2*TY_qc223*Z2)))*exp(Z1)) + 
		  (TY_qc132*TY_qc223 + TY_qc123*TY_qc232)*Z1*pow(Z2,2)) + exp(2*Z2)*
		  (-2*(TY_qc132*(TY_q22 + TY_qc223) + TY_qc123*TY_qc232)*(Z1 + Z2)*pow(Z2,2) + 
		  exp(Z1)*(2*(TY_qa32*(TY_q22 + TY_qc223) + TY_qa23*TY_qc232)*Z1 + 
		  2*(TY_qa32*(TY_q22 + TY_qc223) + TY_qa23*TY_qc232 + (TY_qb32*(TY_q22 + TY_qc223) + TY_qb23*TY_qc232)*Z1)*Z2 - 
		  (-2*(TY_qb32*(TY_q22 + TY_qc223) + TY_qb23*TY_qc232) + ((TY_qa32 + 2*TY_qb32)*(TY_q22 + TY_qc223) + (-2*TY_q22 + TY_qa23 + 2*TY_qb23 - 2*TY_qc223)*TY_qc232)*Z1)*
		  pow(Z2,2) + ((2*TY_q22 - TY_qa32 - 2*TY_qb32 + 2*TY_qc132)*(TY_q22 + TY_qc223) + (2*TY_q22 - TY_qa23 + 2*(-TY_qb23 + TY_qc123 + TY_qc223))*TY_qc232)*pow(Z2,3))))*pow(Z1 + Z2,-1);
	
	/*double norm_B = sqrt(pow(TY_B12, 2)+pow(TY_B14, 2)+pow(TY_B21, 2)+pow(TY_B22, 2)+pow(TY_B23, 2)+pow(TY_B24, 2)+pow(TY_B25, 2)+pow(TY_B32, 2)+pow(TY_B34, 2));
	
	TY_B12 /= norm_B;
	TY_B14 /= norm_B;
	TY_B21 /= norm_B;
	TY_B22 /= norm_B;
	TY_B23 /= norm_B;
	TY_B24 /= norm_B;
	TY_B25 /= norm_B;
	TY_B32 /= norm_B;
	TY_B34 /= norm_B; */
/*	
	if( debug ) 
	{
		sprintf(buf,"\rNonlinear equation 2 = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0.,  TY_B12, 0.,  TY_B14, 0.  );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\r", TY_B21, TY_B22, TY_B23, TY_B24, TY_B25 );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0.,  TY_B32, 0.,  TY_B34, 0.  );
		XOPNotice(buf);
	}
*/
	
	/* decrease order of nonlinear equation 1 by means of equation 2 */
	
	TY_F14 = -(TY_A32*TY_B12*TY_B32) + TY_A52*pow(TY_B12,2) + TY_A12*pow(TY_B32,2);
	TY_F16 = 2*TY_A52*TY_B12*TY_B14 - TY_A32*TY_B14*TY_B32 - TY_A32*TY_B12*TY_B34 + 2*TY_A12*TY_B32*TY_B34;
	TY_F18 = -(TY_A32*TY_B14*TY_B34) + TY_A52*pow(TY_B14,2) + TY_A12*pow(TY_B34,2);
	TY_F23 = 2*TY_A52*TY_B12*TY_B21 - TY_A41*TY_B12*TY_B32 - TY_A32*TY_B21*TY_B32 + TY_A21*pow(TY_B32,2);
	TY_F24 = 2*TY_A52*TY_B12*TY_B22 - TY_A42*TY_B12*TY_B32 - TY_A32*TY_B22*TY_B32 + TY_A22*pow(TY_B32,2);
	TY_F25 = 2*TY_A52*TY_B14*TY_B21 + 2*TY_A52*TY_B12*TY_B23 - TY_A43*TY_B12*TY_B32 - TY_A41*TY_B14*TY_B32 - TY_A32*TY_B23*TY_B32 - TY_A41*TY_B12*TY_B34 - TY_A32*TY_B21*TY_B34 + 2*TY_A21*TY_B32*TY_B34 + TY_A23*pow(TY_B32,2);
	TY_F26 = 2*TY_A52*TY_B14*TY_B22 + 2*TY_A52*TY_B12*TY_B24 - TY_A42*TY_B14*TY_B32 - TY_A32*TY_B24*TY_B32 - TY_A42*TY_B12*TY_B34 - TY_A32*TY_B22*TY_B34 + 2*TY_A22*TY_B32*TY_B34;
	TY_F27 = 2*TY_A52*TY_B14*TY_B23 + 2*TY_A52*TY_B12*TY_B25 - TY_A43*TY_B14*TY_B32 - TY_A32*TY_B25*TY_B32 - TY_A43*TY_B12*TY_B34 - TY_A41*TY_B14*TY_B34 - TY_A32*TY_B23*TY_B34 + 2*TY_A23*TY_B32*TY_B34 + TY_A21*pow(TY_B34,2);
	TY_F28 = 2*TY_A52*TY_B14*TY_B24 - TY_A42*TY_B14*TY_B34 - TY_A32*TY_B24*TY_B34 + TY_A22*pow(TY_B34,2);
	TY_F29 = 2*TY_A52*TY_B14*TY_B25 - TY_A43*TY_B14*TY_B34 - TY_A32*TY_B25*TY_B34 + TY_A23*pow(TY_B34,2);
	TY_F32 = -(TY_A41*TY_B21*TY_B32) + TY_A52*pow(TY_B21,2);
	TY_F33 = 2*TY_A52*TY_B21*TY_B22 - TY_A42*TY_B21*TY_B32 - TY_A41*TY_B22*TY_B32;
	TY_F34 = 2*TY_A52*TY_B21*TY_B23 - TY_A43*TY_B21*TY_B32 - TY_A42*TY_B22*TY_B32 - TY_A41*TY_B23*TY_B32 - TY_A41*TY_B21*TY_B34 + TY_A52*pow(TY_B22,2);
	TY_F35 = 2*TY_A52*TY_B22*TY_B23 + 2*TY_A52*TY_B21*TY_B24 - TY_A43*TY_B22*TY_B32 - TY_A42*TY_B23*TY_B32 - TY_A41*TY_B24*TY_B32 - TY_A42*TY_B21*TY_B34 - TY_A41*TY_B22*TY_B34;
	TY_F36 = 2*TY_A52*TY_B22*TY_B24 + 2*TY_A52*TY_B21*TY_B25 - TY_A43*TY_B23*TY_B32 - TY_A42*TY_B24*TY_B32 - TY_A41*TY_B25*TY_B32 - TY_A43*TY_B21*TY_B34 - TY_A42*TY_B22*TY_B34 - TY_A41*TY_B23*TY_B34 + TY_A52*pow(TY_B23,2);
	TY_F37 = 2*TY_A52*TY_B23*TY_B24 + 2*TY_A52*TY_B22*TY_B25 - TY_A43*TY_B24*TY_B32 - TY_A42*TY_B25*TY_B32 - TY_A43*TY_B22*TY_B34 - TY_A42*TY_B23*TY_B34 - TY_A41*TY_B24*TY_B34;
	TY_F38 = 2*TY_A52*TY_B23*TY_B25 - TY_A43*TY_B25*TY_B32 - TY_A43*TY_B23*TY_B34 - TY_A42*TY_B24*TY_B34 - TY_A41*TY_B25*TY_B34 + TY_A52*pow(TY_B24,2);
	TY_F39 = 2*TY_A52*TY_B24*TY_B25 - TY_A43*TY_B24*TY_B34 - TY_A42*TY_B25*TY_B34;
	TY_F310 = -(TY_A43*TY_B25*TY_B34) + TY_A52*pow(TY_B25,2);

/*
	if( debug ) 
	{
		sprintf(buf,"\rF = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0., 0.,  0.,  TY_F14, 0.,  TY_F16, 0.,  TY_F18, 0.,  0.    );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0., 0.,  TY_F23, TY_F24, TY_F25, TY_F26, TY_F27, TY_F28, TY_F29, 0.    );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0., TY_F32, TY_F33, TY_F34, TY_F35, TY_F36, TY_F37, TY_F38, TY_F39, TY_F310 );
		XOPNotice(buf);
	}
*/
 
	TY_G13  = -(TY_B12*TY_F32);
	TY_G14  = -(TY_B12*TY_F33);
	TY_G15  = TY_B32*TY_F14 - TY_B14*TY_F32 - TY_B12*TY_F34;
	TY_G16  = -(TY_B14*TY_F33) - TY_B12*TY_F35;
	TY_G17  = TY_B34*TY_F14 + TY_B32*TY_F16 - TY_B14*TY_F34 - TY_B12*TY_F36;
	TY_G18  = -(TY_B14*TY_F35) - TY_B12*TY_F37;
	TY_G19  = TY_B34*TY_F16 + TY_B32*TY_F18 - TY_B14*TY_F36 - TY_B12*TY_F38;
	TY_G110 = -(TY_B14*TY_F37) - TY_B12*TY_F39;
	TY_G111 = TY_B34*TY_F18 - TY_B12*TY_F310 - TY_B14*TY_F38;
	TY_G112 = -(TY_B14*TY_F39);
	TY_G113 = -(TY_B14*TY_F310);
	TY_G22  = -(TY_B21*TY_F32);
	TY_G23  = -(TY_B22*TY_F32) - TY_B21*TY_F33;
	TY_G24  = TY_B32*TY_F23 - TY_B23*TY_F32 - TY_B22*TY_F33 - TY_B21*TY_F34;
	TY_G25  = TY_B32*TY_F24 - TY_B24*TY_F32 - TY_B23*TY_F33 - TY_B22*TY_F34 - TY_B21*TY_F35;
	TY_G26  = TY_B34*TY_F23 + TY_B32*TY_F25 - TY_B25*TY_F32 - TY_B24*TY_F33 - TY_B23*TY_F34 - TY_B22*TY_F35 - TY_B21*TY_F36;
	TY_G27  = TY_B34*TY_F24 + TY_B32*TY_F26 - TY_B25*TY_F33 - TY_B24*TY_F34 - TY_B23*TY_F35 - TY_B22*TY_F36 - TY_B21*TY_F37;
	TY_G28  = TY_B34*TY_F25 + TY_B32*TY_F27 - TY_B25*TY_F34 - TY_B24*TY_F35 - TY_B23*TY_F36 - TY_B22*TY_F37 - TY_B21*TY_F38;
	TY_G29  = TY_B34*TY_F26 + TY_B32*TY_F28 - TY_B25*TY_F35 - TY_B24*TY_F36 - TY_B23*TY_F37 - TY_B22*TY_F38 - TY_B21*TY_F39;
	TY_G210 = TY_B34*TY_F27 + TY_B32*TY_F29 - TY_B21*TY_F310 - TY_B25*TY_F36 - TY_B24*TY_F37 - TY_B23*TY_F38 - TY_B22*TY_F39;
	TY_G211 = TY_B34*TY_F28 - TY_B22*TY_F310 - TY_B25*TY_F37 - TY_B24*TY_F38 - TY_B23*TY_F39;
	TY_G212 = TY_B34*TY_F29 - TY_B23*TY_F310 - TY_B25*TY_F38 - TY_B24*TY_F39;
	TY_G213 = -(TY_B24*TY_F310) - TY_B25*TY_F39;
	TY_G214 = -(TY_B25*TY_F310);
/*	
	if( debug ) 
	{
		sprintf(buf,"\rG = \r" );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0., 0.,  TY_G13, TY_G14, TY_G15, TY_G16, TY_G17, TY_G18, TY_G19, TY_G110, TY_G111, TY_G112, TY_G113, 0. );
		XOPNotice(buf);
		sprintf(buf, "%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\t\t%f\r", 0., TY_G22, TY_G23, TY_G24, TY_G25, TY_G26, TY_G27, TY_G28, TY_G29, TY_G210, TY_G211, TY_G212, TY_G213, TY_G214 );
		XOPNotice(buf);
	}
*/	
	// coefficients for polynomial
	TY_w[0] = (-(TY_A21*TY_B12) + TY_A12*TY_B21)*(TY_A52*TY_B21 - TY_A41*TY_B32)*pow(TY_B21,2)*pow(TY_B32,3);
	
	TY_w[1] = 2*TY_B32*TY_G13*TY_G14 - TY_B24*TY_G13*TY_G22 - TY_B23*TY_G14*TY_G22 - TY_B22*TY_G15*TY_G22 - TY_B21*TY_G16*TY_G22 - TY_B23*TY_G13*TY_G23 - TY_B22*TY_G14*TY_G23 - TY_B21*TY_G15*TY_G23 + 2*TY_B14*TY_G22*TY_G23 - 
	TY_B22*TY_G13*TY_G24 - TY_B21*TY_G14*TY_G24 + 2*TY_B12*TY_G23*TY_G24 - TY_B21*TY_G13*TY_G25 + 2*TY_B12*TY_G22*TY_G25;
	
	TY_w[2] = -(TY_B25*TY_G13*TY_G22) - TY_B24*TY_G14*TY_G22 - TY_B23*TY_G15*TY_G22 - TY_B22*TY_G16*TY_G22 - TY_B21*TY_G17*TY_G22 - TY_B24*TY_G13*TY_G23 - TY_B23*TY_G14*TY_G23 - TY_B22*TY_G15*TY_G23 - TY_B21*TY_G16*TY_G23 - 
	TY_B23*TY_G13*TY_G24 - TY_B22*TY_G14*TY_G24 - TY_B21*TY_G15*TY_G24 + 2*TY_B14*TY_G22*TY_G24 - TY_B22*TY_G13*TY_G25 - TY_B21*TY_G14*TY_G25 + 2*TY_B12*TY_G23*TY_G25 - TY_B21*TY_G13*TY_G26 + 2*TY_B12*TY_G22*TY_G26 + 
	TY_B34*pow(TY_G13,2) + TY_B32*(2*TY_G13*TY_G15 + pow(TY_G14,2)) + TY_B14*pow(TY_G23,2) + TY_B12*pow(TY_G24,2);
	
	TY_w[3] = 2*TY_B34*TY_G13*TY_G14 + 2*TY_B32*(TY_G14*TY_G15 + TY_G13*TY_G16) - TY_B25*TY_G14*TY_G22 - TY_B24*TY_G15*TY_G22 - TY_B23*TY_G16*TY_G22 - TY_B22*TY_G17*TY_G22 - TY_B21*TY_G18*TY_G22 - TY_B25*TY_G13*TY_G23 - 
	TY_B24*TY_G14*TY_G23 - TY_B23*TY_G15*TY_G23 - TY_B22*TY_G16*TY_G23 - TY_B21*TY_G17*TY_G23 - TY_B24*TY_G13*TY_G24 - TY_B23*TY_G14*TY_G24 - TY_B22*TY_G15*TY_G24 - TY_B21*TY_G16*TY_G24 + 2*TY_B14*TY_G23*TY_G24 - 
	TY_B23*TY_G13*TY_G25 - TY_B22*TY_G14*TY_G25 - TY_B21*TY_G15*TY_G25 + 2*TY_B14*TY_G22*TY_G25 + 2*TY_B12*TY_G24*TY_G25 - TY_B22*TY_G13*TY_G26 - TY_B21*TY_G14*TY_G26 + 2*TY_B12*TY_G23*TY_G26 - TY_B21*TY_G13*TY_G27 + 
	2*TY_B12*TY_G22*TY_G27;
	
	TY_w[4] = -(TY_B25*TY_G15*TY_G22) - TY_B24*TY_G16*TY_G22 - TY_B23*TY_G17*TY_G22 - TY_B22*TY_G18*TY_G22 - TY_B21*TY_G19*TY_G22 - TY_B25*TY_G14*TY_G23 - TY_B24*TY_G15*TY_G23 - TY_B23*TY_G16*TY_G23 - TY_B22*TY_G17*TY_G23 - 
	TY_B21*TY_G18*TY_G23 - TY_B25*TY_G13*TY_G24 - TY_B24*TY_G14*TY_G24 - TY_B23*TY_G15*TY_G24 - TY_B22*TY_G16*TY_G24 - TY_B21*TY_G17*TY_G24 - TY_B24*TY_G13*TY_G25 - TY_B23*TY_G14*TY_G25 - TY_B22*TY_G15*TY_G25 - 
	TY_B21*TY_G16*TY_G25 + 2*TY_B14*TY_G23*TY_G25 - TY_B23*TY_G13*TY_G26 - TY_B22*TY_G14*TY_G26 - TY_B21*TY_G15*TY_G26 + 2*TY_B14*TY_G22*TY_G26 + 2*TY_B12*TY_G24*TY_G26 - TY_B22*TY_G13*TY_G27 - TY_B21*TY_G14*TY_G27 + 
	2*TY_B12*TY_G23*TY_G27 - TY_B21*TY_G13*TY_G28 + 2*TY_B12*TY_G22*TY_G28 + TY_B34*(2*TY_G13*TY_G15 + pow(TY_G14,2)) + TY_B32*(2*TY_G14*TY_G16 + 2*TY_G13*TY_G17 + pow(TY_G15,2)) + TY_B14*pow(TY_G24,2) + 
	TY_B12*pow(TY_G25,2);
	
	TY_w[5] = 2*TY_B34*(TY_G14*TY_G15 + TY_G13*TY_G16) + 2*TY_B32*(TY_G15*TY_G16 + TY_G14*TY_G17 + TY_G13*TY_G18) - TY_B21*TY_G110*TY_G22 - TY_B25*TY_G16*TY_G22 - TY_B24*TY_G17*TY_G22 - TY_B23*TY_G18*TY_G22 - TY_B22*TY_G19*TY_G22 - 
	TY_B25*TY_G15*TY_G23 - TY_B24*TY_G16*TY_G23 - TY_B23*TY_G17*TY_G23 - TY_B22*TY_G18*TY_G23 - TY_B21*TY_G19*TY_G23 - TY_B25*TY_G14*TY_G24 - TY_B24*TY_G15*TY_G24 - TY_B23*TY_G16*TY_G24 - TY_B22*TY_G17*TY_G24 - 
	TY_B21*TY_G18*TY_G24 - TY_B25*TY_G13*TY_G25 - TY_B24*TY_G14*TY_G25 - TY_B23*TY_G15*TY_G25 - TY_B22*TY_G16*TY_G25 - TY_B21*TY_G17*TY_G25 + 2*TY_B14*TY_G24*TY_G25 - TY_B24*TY_G13*TY_G26 - TY_B23*TY_G14*TY_G26 - 
	TY_B22*TY_G15*TY_G26 - TY_B21*TY_G16*TY_G26 + 2*TY_B14*TY_G23*TY_G26 + 2*TY_B12*TY_G25*TY_G26 - TY_B23*TY_G13*TY_G27 - TY_B22*TY_G14*TY_G27 - TY_B21*TY_G15*TY_G27 + 2*TY_B14*TY_G22*TY_G27 + 2*TY_B12*TY_G24*TY_G27 - 
	TY_B22*TY_G13*TY_G28 - TY_B21*TY_G14*TY_G28 + 2*TY_B12*TY_G23*TY_G28 - TY_B21*TY_G13*TY_G29 + 2*TY_B12*TY_G22*TY_G29;
	
	TY_w[6] = -(TY_B22*TY_G110*TY_G22) - TY_B21*TY_G111*TY_G22 - TY_B25*TY_G17*TY_G22 - TY_B24*TY_G18*TY_G22 - TY_B23*TY_G19*TY_G22 + TY_G210*(-(TY_B21*TY_G13) + 2*TY_B12*TY_G22) - TY_B21*TY_G110*TY_G23 - TY_B25*TY_G16*TY_G23 - 
	TY_B24*TY_G17*TY_G23 - TY_B23*TY_G18*TY_G23 - TY_B22*TY_G19*TY_G23 - TY_B25*TY_G15*TY_G24 - TY_B24*TY_G16*TY_G24 - TY_B23*TY_G17*TY_G24 - TY_B22*TY_G18*TY_G24 - TY_B21*TY_G19*TY_G24 - TY_B25*TY_G14*TY_G25 - 
	TY_B24*TY_G15*TY_G25 - TY_B23*TY_G16*TY_G25 - TY_B22*TY_G17*TY_G25 - TY_B21*TY_G18*TY_G25 - TY_B25*TY_G13*TY_G26 - TY_B24*TY_G14*TY_G26 - TY_B23*TY_G15*TY_G26 - TY_B22*TY_G16*TY_G26 - TY_B21*TY_G17*TY_G26 + 
	2*TY_B14*TY_G24*TY_G26 - TY_B24*TY_G13*TY_G27 - TY_B23*TY_G14*TY_G27 - TY_B22*TY_G15*TY_G27 - TY_B21*TY_G16*TY_G27 + 2*TY_B14*TY_G23*TY_G27 + 2*TY_B12*TY_G25*TY_G27 - TY_B23*TY_G13*TY_G28 - TY_B22*TY_G14*TY_G28 - 
	TY_B21*TY_G15*TY_G28 + 2*TY_B14*TY_G22*TY_G28 + 2*TY_B12*TY_G24*TY_G28 - TY_B22*TY_G13*TY_G29 - TY_B21*TY_G14*TY_G29 + 2*TY_B12*TY_G23*TY_G29 + TY_B34*(2*TY_G14*TY_G16 + 2*TY_G13*TY_G17 + pow(TY_G15,2)) + 
	TY_B32*(2*(TY_G15*TY_G17 + TY_G14*TY_G18 + TY_G13*TY_G19) + pow(TY_G16,2)) + TY_B14*pow(TY_G25,2) + TY_B12*pow(TY_G26,2);
	
	TY_w[7] = 2*TY_B34*(TY_G15*TY_G16 + TY_G14*TY_G17 + TY_G13*TY_G18) + 2*TY_B32*(TY_G110*TY_G13 + TY_G16*TY_G17 + TY_G15*TY_G18 + TY_G14*TY_G19) - TY_B22*TY_G13*TY_G210 - TY_B21*TY_G14*TY_G210 - TY_B23*TY_G110*TY_G22 - 
	TY_B22*TY_G111*TY_G22 - TY_B21*TY_G112*TY_G22 - TY_B25*TY_G18*TY_G22 - TY_B24*TY_G19*TY_G22 + TY_G211*(-(TY_B21*TY_G13) + 2*TY_B12*TY_G22) - TY_B22*TY_G110*TY_G23 - TY_B21*TY_G111*TY_G23 - TY_B25*TY_G17*TY_G23 - 
	TY_B24*TY_G18*TY_G23 - TY_B23*TY_G19*TY_G23 + 2*TY_B12*TY_G210*TY_G23 - TY_B21*TY_G110*TY_G24 - TY_B25*TY_G16*TY_G24 - TY_B24*TY_G17*TY_G24 - TY_B23*TY_G18*TY_G24 - TY_B22*TY_G19*TY_G24 - TY_B25*TY_G15*TY_G25 - 
	TY_B24*TY_G16*TY_G25 - TY_B23*TY_G17*TY_G25 - TY_B22*TY_G18*TY_G25 - TY_B21*TY_G19*TY_G25 - TY_B25*TY_G14*TY_G26 - TY_B24*TY_G15*TY_G26 - TY_B23*TY_G16*TY_G26 - TY_B22*TY_G17*TY_G26 - TY_B21*TY_G18*TY_G26 + 
	2*TY_B14*TY_G25*TY_G26 - TY_B25*TY_G13*TY_G27 - TY_B24*TY_G14*TY_G27 - TY_B23*TY_G15*TY_G27 - TY_B22*TY_G16*TY_G27 - TY_B21*TY_G17*TY_G27 + 2*TY_B14*TY_G24*TY_G27 + 2*TY_B12*TY_G26*TY_G27 - TY_B24*TY_G13*TY_G28 - 
	TY_B23*TY_G14*TY_G28 - TY_B22*TY_G15*TY_G28 - TY_B21*TY_G16*TY_G28 + 2*TY_B14*TY_G23*TY_G28 + 2*TY_B12*TY_G25*TY_G28 - TY_B23*TY_G13*TY_G29 - TY_B22*TY_G14*TY_G29 - TY_B21*TY_G15*TY_G29 + 2*TY_B14*TY_G22*TY_G29 + 
	2*TY_B12*TY_G24*TY_G29;
	
	TY_w[8] = -(TY_B23*TY_G13*TY_G210) - TY_B22*TY_G14*TY_G210 - TY_B21*TY_G15*TY_G210 - TY_B22*TY_G13*TY_G211 - TY_B21*TY_G14*TY_G211 - TY_B21*TY_G13*TY_G212 - TY_B24*TY_G110*TY_G22 - TY_B23*TY_G111*TY_G22 - TY_B22*TY_G112*TY_G22 - 
	TY_B21*TY_G113*TY_G22 - TY_B25*TY_G19*TY_G22 + 2*TY_B14*TY_G210*TY_G22 + 2*TY_B12*TY_G212*TY_G22 - TY_B23*TY_G110*TY_G23 - TY_B22*TY_G111*TY_G23 - TY_B21*TY_G112*TY_G23 - TY_B25*TY_G18*TY_G23 - TY_B24*TY_G19*TY_G23 + 
	2*TY_B12*TY_G211*TY_G23 - TY_B22*TY_G110*TY_G24 - TY_B21*TY_G111*TY_G24 - TY_B25*TY_G17*TY_G24 - TY_B24*TY_G18*TY_G24 - TY_B23*TY_G19*TY_G24 + 2*TY_B12*TY_G210*TY_G24 - TY_B21*TY_G110*TY_G25 - TY_B25*TY_G16*TY_G25 - 
	TY_B24*TY_G17*TY_G25 - TY_B23*TY_G18*TY_G25 - TY_B22*TY_G19*TY_G25 - TY_B25*TY_G15*TY_G26 - TY_B24*TY_G16*TY_G26 - TY_B23*TY_G17*TY_G26 - TY_B22*TY_G18*TY_G26 - TY_B21*TY_G19*TY_G26 - TY_B25*TY_G14*TY_G27 - 
	TY_B24*TY_G15*TY_G27 - TY_B23*TY_G16*TY_G27 - TY_B22*TY_G17*TY_G27 - TY_B21*TY_G18*TY_G27 + 2*TY_B14*TY_G25*TY_G27 - TY_B25*TY_G13*TY_G28 - TY_B24*TY_G14*TY_G28 - TY_B23*TY_G15*TY_G28 - TY_B22*TY_G16*TY_G28 - 
	TY_B21*TY_G17*TY_G28 + 2*TY_B14*TY_G24*TY_G28 + 2*TY_B12*TY_G26*TY_G28 - TY_B24*TY_G13*TY_G29 - TY_B23*TY_G14*TY_G29 - TY_B22*TY_G15*TY_G29 - TY_B21*TY_G16*TY_G29 + 2*TY_B14*TY_G23*TY_G29 + 2*TY_B12*TY_G25*TY_G29 + 
	TY_B34*(2*(TY_G15*TY_G17 + TY_G14*TY_G18 + TY_G13*TY_G19) + pow(TY_G16,2)) + TY_B32*(2*(TY_G111*TY_G13 + TY_G110*TY_G14 + TY_G16*TY_G18 + TY_G15*TY_G19) + pow(TY_G17,2)) + TY_B14*pow(TY_G26,2) + 
	TY_B12*pow(TY_G27,2);
	
	TY_w[9] = 2*TY_B34*(TY_G110*TY_G13 + TY_G16*TY_G17 + TY_G15*TY_G18 + TY_G14*TY_G19) + 2*TY_B32*(TY_G112*TY_G13 + TY_G111*TY_G14 + TY_G110*TY_G15 + TY_G17*TY_G18 + TY_G16*TY_G19) - TY_B24*TY_G13*TY_G210 - TY_B23*TY_G14*TY_G210 - 
	TY_B22*TY_G15*TY_G210 - TY_B21*TY_G16*TY_G210 - TY_B23*TY_G13*TY_G211 - TY_B22*TY_G14*TY_G211 - TY_B21*TY_G15*TY_G211 - TY_B22*TY_G13*TY_G212 - TY_B21*TY_G14*TY_G212 - TY_B25*TY_G110*TY_G22 - TY_B24*TY_G111*TY_G22 - 
	TY_B23*TY_G112*TY_G22 - TY_B22*TY_G113*TY_G22 + 2*TY_B14*TY_G211*TY_G22 + TY_G213*(-(TY_B21*TY_G13) + 2*TY_B12*TY_G22) - TY_B24*TY_G110*TY_G23 - TY_B23*TY_G111*TY_G23 - TY_B22*TY_G112*TY_G23 - 
	TY_B21*TY_G113*TY_G23 - TY_B25*TY_G19*TY_G23 + 2*TY_B14*TY_G210*TY_G23 + 2*TY_B12*TY_G212*TY_G23 - TY_B23*TY_G110*TY_G24 - TY_B22*TY_G111*TY_G24 - TY_B21*TY_G112*TY_G24 - TY_B25*TY_G18*TY_G24 - TY_B24*TY_G19*TY_G24 + 
	2*TY_B12*TY_G211*TY_G24 - TY_B22*TY_G110*TY_G25 - TY_B21*TY_G111*TY_G25 - TY_B25*TY_G17*TY_G25 - TY_B24*TY_G18*TY_G25 - TY_B23*TY_G19*TY_G25 + 2*TY_B12*TY_G210*TY_G25 - TY_B21*TY_G110*TY_G26 - TY_B25*TY_G16*TY_G26 - 
	TY_B24*TY_G17*TY_G26 - TY_B23*TY_G18*TY_G26 - TY_B22*TY_G19*TY_G26 - TY_B25*TY_G15*TY_G27 - TY_B24*TY_G16*TY_G27 - TY_B23*TY_G17*TY_G27 - TY_B22*TY_G18*TY_G27 - TY_B21*TY_G19*TY_G27 + 2*TY_B14*TY_G26*TY_G27 - 
	TY_B25*TY_G14*TY_G28 - TY_B24*TY_G15*TY_G28 - TY_B23*TY_G16*TY_G28 - TY_B22*TY_G17*TY_G28 - TY_B21*TY_G18*TY_G28 + 2*TY_B14*TY_G25*TY_G28 + 2*TY_B12*TY_G27*TY_G28 - TY_B25*TY_G13*TY_G29 - TY_B24*TY_G14*TY_G29 - 
	TY_B23*TY_G15*TY_G29 - TY_B22*TY_G16*TY_G29 - TY_B21*TY_G17*TY_G29 + 2*TY_B14*TY_G24*TY_G29 + 2*TY_B12*TY_G26*TY_G29;
	
	TY_w[10] = -(TY_B25*TY_G13*TY_G210) - TY_B24*TY_G14*TY_G210 - TY_B23*TY_G15*TY_G210 - TY_B22*TY_G16*TY_G210 - TY_B21*TY_G17*TY_G210 - TY_B24*TY_G13*TY_G211 - TY_B23*TY_G14*TY_G211 - TY_B22*TY_G15*TY_G211 - TY_B21*TY_G16*TY_G211 - 
	TY_B23*TY_G13*TY_G212 - TY_B22*TY_G14*TY_G212 - TY_B21*TY_G15*TY_G212 - TY_B22*TY_G13*TY_G213 - TY_B21*TY_G14*TY_G213 - TY_B21*TY_G13*TY_G214 - TY_B25*TY_G111*TY_G22 - TY_B24*TY_G112*TY_G22 - TY_B23*TY_G113*TY_G22 + 
	2*TY_B14*TY_G212*TY_G22 + 2*TY_B12*TY_G214*TY_G22 - TY_B25*TY_G110*TY_G23 - TY_B24*TY_G111*TY_G23 - TY_B23*TY_G112*TY_G23 - TY_B22*TY_G113*TY_G23 + 2*TY_B14*TY_G211*TY_G23 + 2*TY_B12*TY_G213*TY_G23 - 
	TY_B24*TY_G110*TY_G24 - TY_B23*TY_G111*TY_G24 - TY_B22*TY_G112*TY_G24 - TY_B21*TY_G113*TY_G24 - TY_B25*TY_G19*TY_G24 + 2*TY_B14*TY_G210*TY_G24 + 2*TY_B12*TY_G212*TY_G24 - TY_B23*TY_G110*TY_G25 - 
	TY_B22*TY_G111*TY_G25 - TY_B21*TY_G112*TY_G25 - TY_B25*TY_G18*TY_G25 - TY_B24*TY_G19*TY_G25 + 2*TY_B12*TY_G211*TY_G25 - TY_B22*TY_G110*TY_G26 - TY_B21*TY_G111*TY_G26 - TY_B25*TY_G17*TY_G26 - TY_B24*TY_G18*TY_G26 - 
	TY_B23*TY_G19*TY_G26 + 2*TY_B12*TY_G210*TY_G26 - TY_B21*TY_G110*TY_G27 - TY_B25*TY_G16*TY_G27 - TY_B24*TY_G17*TY_G27 - TY_B23*TY_G18*TY_G27 - TY_B22*TY_G19*TY_G27 - TY_B25*TY_G15*TY_G28 - TY_B24*TY_G16*TY_G28 - 
	TY_B23*TY_G17*TY_G28 - TY_B22*TY_G18*TY_G28 - TY_B21*TY_G19*TY_G28 + 2*TY_B14*TY_G26*TY_G28 - TY_B25*TY_G14*TY_G29 - TY_B24*TY_G15*TY_G29 - TY_B23*TY_G16*TY_G29 - TY_B22*TY_G17*TY_G29 - TY_B21*TY_G18*TY_G29 + 
	2*TY_B14*TY_G25*TY_G29 + 2*TY_B12*TY_G27*TY_G29 + TY_B34*(2*(TY_G111*TY_G13 + TY_G110*TY_G14 + TY_G16*TY_G18 + TY_G15*TY_G19) + pow(TY_G17,2)) + 
	TY_B32*(2*(TY_G113*TY_G13 + TY_G112*TY_G14 + TY_G111*TY_G15 + TY_G110*TY_G16 + TY_G17*TY_G19) + pow(TY_G18,2)) + TY_B14*pow(TY_G27,2) + TY_B12*pow(TY_G28,2);
	
	TY_w[11] = 2*TY_B34*(TY_G112*TY_G13 + TY_G111*TY_G14 + TY_G110*TY_G15 + TY_G17*TY_G18 + TY_G16*TY_G19) + 2*TY_B32*(TY_G113*TY_G14 + TY_G112*TY_G15 + TY_G111*TY_G16 + TY_G110*TY_G17 + TY_G18*TY_G19) - TY_B25*TY_G14*TY_G210 - 
	TY_B24*TY_G15*TY_G210 - TY_B23*TY_G16*TY_G210 - TY_B22*TY_G17*TY_G210 - TY_B21*TY_G18*TY_G210 - TY_B25*TY_G13*TY_G211 - TY_B24*TY_G14*TY_G211 - TY_B23*TY_G15*TY_G211 - TY_B22*TY_G16*TY_G211 - TY_B21*TY_G17*TY_G211 - 
	TY_B24*TY_G13*TY_G212 - TY_B23*TY_G14*TY_G212 - TY_B22*TY_G15*TY_G212 - TY_B21*TY_G16*TY_G212 - TY_B23*TY_G13*TY_G213 - TY_B22*TY_G14*TY_G213 - TY_B21*TY_G15*TY_G213 - TY_B25*TY_G112*TY_G22 - TY_B24*TY_G113*TY_G22 + 
	2*TY_B14*TY_G213*TY_G22 - TY_B25*TY_G111*TY_G23 - TY_B24*TY_G112*TY_G23 - TY_B23*TY_G113*TY_G23 + 2*TY_B14*TY_G212*TY_G23 - TY_G214*(TY_B22*TY_G13 + TY_B21*TY_G14 - 2*TY_B12*TY_G23) - TY_B25*TY_G110*TY_G24 - 
	TY_B24*TY_G111*TY_G24 - TY_B23*TY_G112*TY_G24 - TY_B22*TY_G113*TY_G24 + 2*TY_B14*TY_G211*TY_G24 + 2*TY_B12*TY_G213*TY_G24 - TY_B24*TY_G110*TY_G25 - TY_B23*TY_G111*TY_G25 - TY_B22*TY_G112*TY_G25 - 
	TY_B21*TY_G113*TY_G25 - TY_B25*TY_G19*TY_G25 + 2*TY_B14*TY_G210*TY_G25 + 2*TY_B12*TY_G212*TY_G25 - TY_B23*TY_G110*TY_G26 - TY_B22*TY_G111*TY_G26 - TY_B21*TY_G112*TY_G26 - TY_B25*TY_G18*TY_G26 - TY_B24*TY_G19*TY_G26 + 
	2*TY_B12*TY_G211*TY_G26 - TY_B22*TY_G110*TY_G27 - TY_B21*TY_G111*TY_G27 - TY_B25*TY_G17*TY_G27 - TY_B24*TY_G18*TY_G27 - TY_B23*TY_G19*TY_G27 + 2*TY_B12*TY_G210*TY_G27 - TY_B21*TY_G110*TY_G28 - TY_B25*TY_G16*TY_G28 - 
	TY_B24*TY_G17*TY_G28 - TY_B23*TY_G18*TY_G28 - TY_B22*TY_G19*TY_G28 + 2*TY_B14*TY_G27*TY_G28 - TY_B25*TY_G15*TY_G29 - TY_B24*TY_G16*TY_G29 - TY_B23*TY_G17*TY_G29 - TY_B22*TY_G18*TY_G29 - TY_B21*TY_G19*TY_G29 + 
	2*TY_B14*TY_G26*TY_G29 + 2*TY_B12*TY_G28*TY_G29;
	
	TY_w[12] = -(TY_B25*TY_G15*TY_G210) - TY_B24*TY_G16*TY_G210 - TY_B23*TY_G17*TY_G210 - TY_B22*TY_G18*TY_G210 - TY_B21*TY_G19*TY_G210 - TY_B25*TY_G14*TY_G211 - TY_B24*TY_G15*TY_G211 - TY_B23*TY_G16*TY_G211 - TY_B22*TY_G17*TY_G211 - 
	TY_B21*TY_G18*TY_G211 - TY_B25*TY_G13*TY_G212 - TY_B24*TY_G14*TY_G212 - TY_B23*TY_G15*TY_G212 - TY_B22*TY_G16*TY_G212 - TY_B21*TY_G17*TY_G212 - TY_B24*TY_G13*TY_G213 - TY_B23*TY_G14*TY_G213 - TY_B22*TY_G15*TY_G213 - 
	TY_B21*TY_G16*TY_G213 - TY_B25*TY_G113*TY_G22 - TY_B25*TY_G112*TY_G23 - TY_B24*TY_G113*TY_G23 + 2*TY_B14*TY_G213*TY_G23 - TY_B25*TY_G111*TY_G24 - TY_B24*TY_G112*TY_G24 - TY_B23*TY_G113*TY_G24 + 
	2*TY_B14*TY_G212*TY_G24 - TY_G214*(TY_B23*TY_G13 + TY_B22*TY_G14 + TY_B21*TY_G15 - 2*TY_B14*TY_G22 - 2*TY_B12*TY_G24) - TY_B25*TY_G110*TY_G25 - TY_B24*TY_G111*TY_G25 - TY_B23*TY_G112*TY_G25 - 
	TY_B22*TY_G113*TY_G25 + 2*TY_B14*TY_G211*TY_G25 + 2*TY_B12*TY_G213*TY_G25 - TY_B24*TY_G110*TY_G26 - TY_B23*TY_G111*TY_G26 - TY_B22*TY_G112*TY_G26 - TY_B21*TY_G113*TY_G26 - TY_B25*TY_G19*TY_G26 + 
	2*TY_B14*TY_G210*TY_G26 + 2*TY_B12*TY_G212*TY_G26 - TY_B23*TY_G110*TY_G27 - TY_B22*TY_G111*TY_G27 - TY_B21*TY_G112*TY_G27 - TY_B25*TY_G18*TY_G27 - TY_B24*TY_G19*TY_G27 + 2*TY_B12*TY_G211*TY_G27 - 
	TY_B22*TY_G110*TY_G28 - TY_B21*TY_G111*TY_G28 - TY_B25*TY_G17*TY_G28 - TY_B24*TY_G18*TY_G28 - TY_B23*TY_G19*TY_G28 + 2*TY_B12*TY_G210*TY_G28 - TY_B21*TY_G110*TY_G29 - TY_B25*TY_G16*TY_G29 - TY_B24*TY_G17*TY_G29 - 
	TY_B23*TY_G18*TY_G29 - TY_B22*TY_G19*TY_G29 + 2*TY_B14*TY_G27*TY_G29 + TY_B34*(2*(TY_G113*TY_G13 + TY_G112*TY_G14 + TY_G111*TY_G15 + TY_G110*TY_G16 + TY_G17*TY_G19) + pow(TY_G18,2)) + 
	TY_B32*(2*(TY_G113*TY_G15 + TY_G112*TY_G16 + TY_G111*TY_G17 + TY_G110*TY_G18) + pow(TY_G19,2)) + TY_B14*pow(TY_G28,2) + TY_B12*pow(TY_G29,2);
	
	TY_w[13] = 2*TY_B32*(TY_G113*TY_G16 + TY_G112*TY_G17 + TY_G111*TY_G18 + TY_G110*TY_G19) + 2*TY_B34*(TY_G113*TY_G14 + TY_G112*TY_G15 + TY_G111*TY_G16 + TY_G110*TY_G17 + TY_G18*TY_G19) - TY_B21*TY_G110*TY_G210 - 
	TY_B25*TY_G16*TY_G210 - TY_B24*TY_G17*TY_G210 - TY_B23*TY_G18*TY_G210 - TY_B22*TY_G19*TY_G210 - TY_B25*TY_G15*TY_G211 - TY_B24*TY_G16*TY_G211 - TY_B23*TY_G17*TY_G211 - TY_B22*TY_G18*TY_G211 - TY_B21*TY_G19*TY_G211 - 
	TY_B25*TY_G14*TY_G212 - TY_B24*TY_G15*TY_G212 - TY_B23*TY_G16*TY_G212 - TY_B22*TY_G17*TY_G212 - TY_B21*TY_G18*TY_G212 - TY_B25*TY_G13*TY_G213 - TY_B24*TY_G14*TY_G213 - TY_B23*TY_G15*TY_G213 - TY_B22*TY_G16*TY_G213 - 
	TY_B21*TY_G17*TY_G213 - TY_B25*TY_G113*TY_G23 - TY_B25*TY_G112*TY_G24 - TY_B24*TY_G113*TY_G24 + 2*TY_B14*TY_G213*TY_G24 - TY_B25*TY_G111*TY_G25 - TY_B24*TY_G112*TY_G25 - TY_B23*TY_G113*TY_G25 + 
	2*TY_B14*TY_G212*TY_G25 - TY_G214*(TY_B24*TY_G13 + TY_B23*TY_G14 + TY_B22*TY_G15 + TY_B21*TY_G16 - 2*TY_B14*TY_G23 - 2*TY_B12*TY_G25) - TY_B25*TY_G110*TY_G26 - TY_B24*TY_G111*TY_G26 - TY_B23*TY_G112*TY_G26 - 
	TY_B22*TY_G113*TY_G26 + 2*TY_B14*TY_G211*TY_G26 + 2*TY_B12*TY_G213*TY_G26 - TY_B24*TY_G110*TY_G27 - TY_B23*TY_G111*TY_G27 - TY_B22*TY_G112*TY_G27 - TY_B21*TY_G113*TY_G27 - TY_B25*TY_G19*TY_G27 + 
	2*TY_B14*TY_G210*TY_G27 + 2*TY_B12*TY_G212*TY_G27 - TY_B23*TY_G110*TY_G28 - TY_B22*TY_G111*TY_G28 - TY_B21*TY_G112*TY_G28 - TY_B25*TY_G18*TY_G28 - TY_B24*TY_G19*TY_G28 + 2*TY_B12*TY_G211*TY_G28 - 
	TY_B22*TY_G110*TY_G29 - TY_B21*TY_G111*TY_G29 - TY_B25*TY_G17*TY_G29 - TY_B24*TY_G18*TY_G29 - TY_B23*TY_G19*TY_G29 + 2*TY_B12*TY_G210*TY_G29 + 2*TY_B14*TY_G28*TY_G29;
	
	TY_w[14] = -(TY_B22*TY_G110*TY_G210) - TY_B21*TY_G111*TY_G210 - TY_B25*TY_G17*TY_G210 - TY_B24*TY_G18*TY_G210 - TY_B23*TY_G19*TY_G210 - TY_B21*TY_G110*TY_G211 - TY_B25*TY_G16*TY_G211 - TY_B24*TY_G17*TY_G211 - 
	TY_B23*TY_G18*TY_G211 - TY_B22*TY_G19*TY_G211 - TY_B25*TY_G15*TY_G212 - TY_B24*TY_G16*TY_G212 - TY_B23*TY_G17*TY_G212 - TY_B22*TY_G18*TY_G212 - TY_B21*TY_G19*TY_G212 - TY_B25*TY_G14*TY_G213 - TY_B24*TY_G15*TY_G213 - 
	TY_B23*TY_G16*TY_G213 - TY_B22*TY_G17*TY_G213 - TY_B21*TY_G18*TY_G213 - TY_B25*TY_G113*TY_G24 - TY_B25*TY_G112*TY_G25 - TY_B24*TY_G113*TY_G25 + 2*TY_B14*TY_G213*TY_G25 - TY_B25*TY_G111*TY_G26 - TY_B24*TY_G112*TY_G26 - 
	TY_B23*TY_G113*TY_G26 + 2*TY_B14*TY_G212*TY_G26 - TY_G214*(TY_B25*TY_G13 + TY_B24*TY_G14 + TY_B23*TY_G15 + TY_B22*TY_G16 + TY_B21*TY_G17 - 2*TY_B14*TY_G24 - 2*TY_B12*TY_G26) - TY_B25*TY_G110*TY_G27 - 
	TY_B24*TY_G111*TY_G27 - TY_B23*TY_G112*TY_G27 - TY_B22*TY_G113*TY_G27 + 2*TY_B14*TY_G211*TY_G27 + 2*TY_B12*TY_G213*TY_G27 - TY_B24*TY_G110*TY_G28 - TY_B23*TY_G111*TY_G28 - TY_B22*TY_G112*TY_G28 - 
	TY_B21*TY_G113*TY_G28 - TY_B25*TY_G19*TY_G28 + 2*TY_B14*TY_G210*TY_G28 + 2*TY_B12*TY_G212*TY_G28 - TY_B23*TY_G110*TY_G29 - TY_B22*TY_G111*TY_G29 - TY_B21*TY_G112*TY_G29 - TY_B25*TY_G18*TY_G29 - TY_B24*TY_G19*TY_G29 + 
	2*TY_B12*TY_G211*TY_G29 + TY_B32*(2*(TY_G113*TY_G17 + TY_G112*TY_G18 + TY_G111*TY_G19) + pow(TY_G110,2)) + 
	TY_B34*(2*(TY_G113*TY_G15 + TY_G112*TY_G16 + TY_G111*TY_G17 + TY_G110*TY_G18) + pow(TY_G19,2)) + TY_B12*pow(TY_G210,2) + TY_B14*pow(TY_G29,2); 
	
	TY_w[15] = 2*TY_B34*(TY_G113*TY_G16 + TY_G112*TY_G17 + TY_G111*TY_G18 + TY_G110*TY_G19) + 2*TY_B32*(TY_G110*TY_G111 + TY_G113*TY_G18 + TY_G112*TY_G19) - TY_B23*TY_G110*TY_G210 - TY_B22*TY_G111*TY_G210 - 
	TY_B21*TY_G112*TY_G210 - TY_B25*TY_G18*TY_G210 - TY_B24*TY_G19*TY_G210 - TY_B22*TY_G110*TY_G211 - TY_B21*TY_G111*TY_G211 - TY_B25*TY_G17*TY_G211 - TY_B24*TY_G18*TY_G211 - TY_B23*TY_G19*TY_G211 + 
	2*TY_B12*TY_G210*TY_G211 - TY_B21*TY_G110*TY_G212 - TY_B25*TY_G16*TY_G212 - TY_B24*TY_G17*TY_G212 - TY_B23*TY_G18*TY_G212 - TY_B22*TY_G19*TY_G212 - TY_B25*TY_G15*TY_G213 - TY_B24*TY_G16*TY_G213 - 
	TY_B23*TY_G17*TY_G213 - TY_B22*TY_G18*TY_G213 - TY_B21*TY_G19*TY_G213 - TY_B25*TY_G113*TY_G25 - TY_B25*TY_G112*TY_G26 - TY_B24*TY_G113*TY_G26 + 2*TY_B14*TY_G213*TY_G26 - TY_B25*TY_G111*TY_G27 - TY_B24*TY_G112*TY_G27 - 
	TY_B23*TY_G113*TY_G27 + 2*TY_B14*TY_G212*TY_G27 - TY_G214*(TY_B25*TY_G14 + TY_B24*TY_G15 + TY_B23*TY_G16 + TY_B22*TY_G17 + TY_B21*TY_G18 - 2*TY_B14*TY_G25 - 2*TY_B12*TY_G27) - TY_B25*TY_G110*TY_G28 - 
	TY_B24*TY_G111*TY_G28 - TY_B23*TY_G112*TY_G28 - TY_B22*TY_G113*TY_G28 + 2*TY_B14*TY_G211*TY_G28 + 2*TY_B12*TY_G213*TY_G28 - TY_B24*TY_G110*TY_G29 - TY_B23*TY_G111*TY_G29 - TY_B22*TY_G112*TY_G29 - 
	TY_B21*TY_G113*TY_G29 - TY_B25*TY_G19*TY_G29 + 2*TY_B14*TY_G210*TY_G29 + 2*TY_B12*TY_G212*TY_G29;
	
	TY_w[16] = -(TY_B24*TY_G110*TY_G210) - TY_B23*TY_G111*TY_G210 - TY_B22*TY_G112*TY_G210 - TY_B21*TY_G113*TY_G210 - TY_B25*TY_G19*TY_G210 - TY_B23*TY_G110*TY_G211 - TY_B22*TY_G111*TY_G211 - TY_B21*TY_G112*TY_G211 - 
	TY_B25*TY_G18*TY_G211 - TY_B24*TY_G19*TY_G211 - TY_B22*TY_G110*TY_G212 - TY_B21*TY_G111*TY_G212 - TY_B25*TY_G17*TY_G212 - TY_B24*TY_G18*TY_G212 - TY_B23*TY_G19*TY_G212 + 2*TY_B12*TY_G210*TY_G212 - 
	TY_B21*TY_G110*TY_G213 - TY_B25*TY_G16*TY_G213 - TY_B24*TY_G17*TY_G213 - TY_B23*TY_G18*TY_G213 - TY_B22*TY_G19*TY_G213 - TY_B25*TY_G113*TY_G26 - TY_B25*TY_G112*TY_G27 - TY_B24*TY_G113*TY_G27 + 
	2*TY_B14*TY_G213*TY_G27 - TY_B25*TY_G111*TY_G28 - TY_B24*TY_G112*TY_G28 - TY_B23*TY_G113*TY_G28 + 2*TY_B14*TY_G212*TY_G28 - 
	TY_G214*(TY_B25*TY_G15 + TY_B24*TY_G16 + TY_B23*TY_G17 + TY_B22*TY_G18 + TY_B21*TY_G19 - 2*TY_B14*TY_G26 - 2*TY_B12*TY_G28) - TY_B25*TY_G110*TY_G29 - TY_B24*TY_G111*TY_G29 - TY_B23*TY_G112*TY_G29 - 
	TY_B22*TY_G113*TY_G29 + 2*TY_B14*TY_G211*TY_G29 + 2*TY_B12*TY_G213*TY_G29 + TY_B34*(2*(TY_G113*TY_G17 + TY_G112*TY_G18 + TY_G111*TY_G19) + pow(TY_G110,2)) + 
	TY_B32*(2*TY_G110*TY_G112 + 2*TY_G113*TY_G19 + pow(TY_G111,2)) + TY_B14*pow(TY_G210,2) + TY_B12*pow(TY_G211,2);
	
	TY_w[17] = 2*TY_B32*(TY_G111*TY_G112 + TY_G110*TY_G113) + 2*TY_B34*(TY_G110*TY_G111 + TY_G113*TY_G18 + TY_G112*TY_G19) - TY_B25*TY_G110*TY_G210 - TY_B24*TY_G111*TY_G210 - TY_B23*TY_G112*TY_G210 - TY_B22*TY_G113*TY_G210 - 
	TY_B24*TY_G110*TY_G211 - TY_B23*TY_G111*TY_G211 - TY_B22*TY_G112*TY_G211 - TY_B21*TY_G113*TY_G211 - TY_B25*TY_G19*TY_G211 + 2*TY_B14*TY_G210*TY_G211 - TY_B23*TY_G110*TY_G212 - TY_B22*TY_G111*TY_G212 - 
	TY_B21*TY_G112*TY_G212 - TY_B25*TY_G18*TY_G212 - TY_B24*TY_G19*TY_G212 + 2*TY_B12*TY_G211*TY_G212 - TY_B22*TY_G110*TY_G213 - TY_B21*TY_G111*TY_G213 - TY_B25*TY_G17*TY_G213 - TY_B24*TY_G18*TY_G213 - 
	TY_B23*TY_G19*TY_G213 + 2*TY_B12*TY_G210*TY_G213 - TY_B25*TY_G113*TY_G27 - TY_B25*TY_G112*TY_G28 - TY_B24*TY_G113*TY_G28 + 2*TY_B14*TY_G213*TY_G28 - TY_B25*TY_G111*TY_G29 - TY_B24*TY_G112*TY_G29 - 
	TY_B23*TY_G113*TY_G29 + 2*TY_B14*TY_G212*TY_G29 - TY_G214*(TY_B21*TY_G110 + TY_B25*TY_G16 + TY_B24*TY_G17 + TY_B23*TY_G18 + TY_B22*TY_G19 - 2*TY_B14*TY_G27 - 2*TY_B12*TY_G29);
	
	TY_w[18] = -(TY_B25*TY_G111*TY_G210) - TY_B24*TY_G112*TY_G210 - TY_B23*TY_G113*TY_G210 - TY_B25*TY_G110*TY_G211 - TY_B24*TY_G111*TY_G211 - TY_B23*TY_G112*TY_G211 - TY_B22*TY_G113*TY_G211 - TY_B24*TY_G110*TY_G212 - 
	TY_B23*TY_G111*TY_G212 - TY_B22*TY_G112*TY_G212 - TY_B21*TY_G113*TY_G212 - TY_B25*TY_G19*TY_G212 + 2*TY_B14*TY_G210*TY_G212 - TY_B23*TY_G110*TY_G213 - TY_B22*TY_G111*TY_G213 - TY_B21*TY_G112*TY_G213 - 
	TY_B25*TY_G18*TY_G213 - TY_B24*TY_G19*TY_G213 + 2*TY_B12*TY_G211*TY_G213 - TY_B25*TY_G113*TY_G28 - 
	TY_G214*(TY_B22*TY_G110 + TY_B21*TY_G111 + TY_B25*TY_G17 + TY_B24*TY_G18 + TY_B23*TY_G19 - 2*TY_B12*TY_G210 - 2*TY_B14*TY_G28) - TY_B25*TY_G112*TY_G29 - TY_B24*TY_G113*TY_G29 + 2*TY_B14*TY_G213*TY_G29 + 
	TY_B34*(2*TY_G110*TY_G112 + 2*TY_G113*TY_G19 + pow(TY_G111,2)) + TY_B32*(2*TY_G111*TY_G113 + pow(TY_G112,2)) + TY_B14*pow(TY_G211,2) + TY_B12*pow(TY_G212,2);
	
	TY_w[19] = 2*TY_B32*TY_G112*TY_G113 + 2*TY_B34*(TY_G111*TY_G112 + TY_G110*TY_G113) - TY_B25*TY_G112*TY_G210 - TY_B24*TY_G113*TY_G210 - TY_B25*TY_G111*TY_G211 - TY_B24*TY_G112*TY_G211 - TY_B23*TY_G113*TY_G211 - 
	TY_B25*TY_G110*TY_G212 - TY_B24*TY_G111*TY_G212 - TY_B23*TY_G112*TY_G212 - TY_B22*TY_G113*TY_G212 + 2*TY_B14*TY_G211*TY_G212 - TY_B24*TY_G110*TY_G213 - TY_B23*TY_G111*TY_G213 - TY_B22*TY_G112*TY_G213 - 
	TY_B21*TY_G113*TY_G213 - TY_B25*TY_G19*TY_G213 + 2*TY_B14*TY_G210*TY_G213 + 2*TY_B12*TY_G212*TY_G213 - TY_B25*TY_G113*TY_G29 - 
	TY_G214*(TY_B23*TY_G110 + TY_B22*TY_G111 + TY_B21*TY_G112 + TY_B25*TY_G18 + TY_B24*TY_G19 - 2*TY_B12*TY_G211 - 2*TY_B14*TY_G29);
	
	TY_w[20] = -(TY_B25*TY_G113*TY_G210) - TY_B25*TY_G112*TY_G211 - TY_B24*TY_G113*TY_G211 - TY_B25*TY_G111*TY_G212 - TY_B24*TY_G112*TY_G212 - TY_B23*TY_G113*TY_G212 - TY_B25*TY_G110*TY_G213 - TY_B24*TY_G111*TY_G213 - 
	TY_B23*TY_G112*TY_G213 - TY_B22*TY_G113*TY_G213 + 2*TY_B14*TY_G211*TY_G213 - (TY_B24*TY_G110 + TY_B23*TY_G111 + TY_B22*TY_G112 + TY_B21*TY_G113 + TY_B25*TY_G19 - 2*TY_B14*TY_G210 - 2*TY_B12*TY_G212)*TY_G214 + 
	TY_B34*(2*TY_G111*TY_G113 + pow(TY_G112,2)) + TY_B32*pow(TY_G113,2) + TY_B14*pow(TY_G212,2) + TY_B12*pow(TY_G213,2);
	
	TY_w[21] = TY_B25*(TY_A23*TY_B14*(-3*TY_A52*TY_B24*TY_B25 + (2*TY_A43*TY_B24 + TY_A42*TY_B25)*TY_B34) + TY_B25*(TY_A22*TY_B14*(-(TY_A52*TY_B25) + TY_A43*TY_B34) 
																			 + TY_A12*(4*TY_A52*TY_B24*TY_B25 - (3*TY_A43*TY_B24 + TY_A42*TY_B25)*TY_B34)))*pow(TY_B34,3);
	
	TY_w[22] = (-(TY_A23*TY_B14) + TY_A12*TY_B25)*(TY_A52*TY_B25 - TY_A43*TY_B34)*pow(TY_B25,2)*pow(TY_B34,3);
/*	
	if( debug ) 
	{
		sprintf(buf,"\rCoefficients of polynomial\r");
		XOPNotice(buf);
		int i;
		for ( i = 0; i < 23; i ++ ) {
			sprintf(buf, "w[%d] = %f\r", i, TY_w[i] );
			XOPNotice(buf);
		}
		sprintf(buf, "\r" );
		XOPNotice(buf);
	}
 */
}

double TY_Q( double d2 )
{
	return d2 * TY_B32 + pow( d2, 3 ) *  TY_B34;
}

double TY_V( double d2 )
{
	return	-( pow( d2, 2 ) * TY_G13 + pow( d2, 3 ) * TY_G14 + pow( d2, 4 ) * TY_G15 + pow( d2, 5 ) * TY_G16 + 
			  pow( d2, 6 ) * TY_G17 + pow( d2, 7 ) *  TY_G18 + pow( d2, 8 ) * TY_G19 + pow( d2, 9 ) * TY_G110 + 
			  pow( d2, 10 ) *  TY_G111 + pow( d2, 11 ) *  TY_G112 + pow( d2, 12 ) *  TY_G113 );
}

double TY_W( double d2 )
{
	return d2  * TY_G22 + pow( d2, 2 ) * TY_G23 + pow( d2, 3 ) * TY_G24 + pow( d2, 4 ) * TY_G25 + pow( d2, 5 ) * TY_G26 + 
	pow( d2, 6 ) * TY_G27 + pow( d2, 7 ) *  TY_G28 + pow( d2, 8 ) *  TY_G29 + pow( d2, 9 ) * TY_G210 + 
	pow( d2, 10 ) * TY_G211 + pow( d2, 11 ) * TY_G212 + pow( d2, 12 ) * TY_G213 + pow( d2, 13 ) * TY_G214;
}

double TY_X( double d2 )
{
	return TY_V( d2 ) / TY_W( d2 );
}

// solve the linear system depending on d1, d2 using Cramer's rule
void TY_SolveLinearEquations( double d1, double d2, 
						      double* a, double* b, double* c1, double* c2)
{
	double det    = TY_q22 * d1 * d2;
	double det_a  = TY_qa12  * d2 + TY_qa21  * d1 + TY_qa22  * d1 * d2 + TY_qa23  * d1 * pow( d2, 2 ) + TY_qa32  * pow( d1, 2 ) * d2; 
	double det_b  = TY_qb12  * d2 + TY_qb21  * d1 + TY_qb22  * d1 * d2 + TY_qb23  * d1 * pow( d2, 2 ) + TY_qb32  * pow( d1, 2 ) * d2; 
	double det_c1 = TY_qc112 * d2 + TY_qc121 * d1 + TY_qc122 * d1 * d2 + TY_qc123 * d1 * pow( d2, 2 ) + TY_qc132 * pow( d1, 2 ) * d2; 
	double det_c2 = TY_qc212 * d2 + TY_qc221 * d1 + TY_qc222 * d1 * d2 + TY_qc223 * d1 * pow( d2, 2 ) + TY_qc232 * pow( d1, 2 ) * d2;
	
	*a  = det_a  / det;
	*b  = det_b  / det;
	*c1 = det_c1 / det;
	*c2 = det_c2 / det;
}

//Solve the system of linear and nonlinear equations for given Zi, Ki, phi which gives at 
// most 22 solutions for the parameters a,b,ci,di. From the set of solutions choose the 
// physical one and return it.
int TY_SolveEquations( double Z1, double Z2, double K1, double K2, double phi, 
					   double* a, double* b, double* c1, double* c2, double* d1, double* d2, 
				       int debug )
{
	
	// the two coupled non-linear eqautions were reduced to a
	// 22nd order polynomial, the roots are give all possible solutions 
	// for d2, than d1 can be computed by the function X 
	char buf[256];
	
 	double real_coefficient[23];
	double imag_coefficient[23];
	
	double real_root[22];
	double imag_root[22];
	
	//integer degree of polynomial
	int degree = 22;
	int i;
	double x,y;
	double var_a, var_b, var_c1, var_c2, var_d1, var_d2;
	double sol_a[22], sol_b[22], sol_c1[22], sol_c2[22], sol_d1[22], sol_d2[22];
	
	int j = 0;
	
	int n_roots,n,selected_root;
	double dr,qmax,q,dq,min,sum;
	double *sq,*gr;
	double Pi = 3.14159265358979323846264338327950288;   /* pi */
	
	
	// reduce system to a polynomial from which all solution are extracted
	// by doing that a lot of global background variables are set
	TY_ReduceNonlinearSystem( Z1, Z2, K1, K2, phi, debug );
	
	// vector of real and imaginary coefficients in order of decreasing powers
	for ( i = 0; i <= degree; i++ )
	{
		// the global variablw TY_w was set by TY_ReduceNonlinearSystem
		real_coefficient[i] = TY_w[ 22 - i ];
		imag_coefficient[i] = 0.;
	}
	
	// Jenkins-Traub method to approximate the roots of the polynomial
	cpoly( real_coefficient, imag_coefficient, degree, real_root, imag_root );
	
	// show the result if in debug mode
/*	
	if ( debug )
	{
		for ( i = 0; i < degree; i++ )
		{
			x = real_root[i];
			y = imag_root[i];
			if ( chop( y ) == 0 )
				sprintf(buf, "root(%d) = %g\r", i+1, x );
			else
				sprintf(buf, "root(%d) = %g + %g i\r", i+1, x, y );
			XOPNotice(buf);
		}
		sprintf(buf, "\r" );
		XOPNotice(buf);
	}
 */
	
	// select real roots and those satisfying Q(x) != 0 and W(x) != 0
	// Paper: Cluster formation in two-Yukawa Fluids, J. Chem. Phys. 122, 2005
	// The right set of (a, b, c1, c2, d1, d2) should have the following properties:
	// (1) a > 0 
	// (2) d1, d2 are real
	// (3) vi/Ki > 0 <=> g(Zi) > 0
	// (4) if there is still more than root, calculate g(r) for each root
	//     and g(r) of the correct root should have the minimum average value 
	//	   inside the hardcore	

	for ( i = 0; i < degree; i++ )
	{
		x = real_root[i];
		y = imag_root[i];
		
		if ( chop( y ) == 0 && TY_W( x ) != 0 && TY_Q( x ) != 0 )
		{
			var_d1 = TY_X( x );
			var_d2 = x;
			
			// solution of linear system for given d1, d2 to obtain a,b,ci,di
			TY_SolveLinearEquations( var_d1, var_d2, &var_a, &var_b, &var_c1, &var_c2 );
			
			// select physical solutions, for details check paper: "Cluster formation in
			// two-Yukawa fluids", J. Chem. Phys. 122 (2005)
			if ( var_a > 0 && 
				 TY_g( Z1, phi, Z1, Z2, var_a, var_b, var_c1, var_c2, var_d1, var_d2 ) > 0 &&
	 			 TY_g( Z2, phi, Z1, Z2, var_a, var_b, var_c1, var_c2, var_d1, var_d2 ) > 0 )
			{
				sol_a[j]  = var_a;
				sol_b[j]  = var_b;
				sol_c1[j] = var_c1;
				sol_c2[j] = var_c2;
				sol_d1[j] = var_d1;
				sol_d2[j] = var_d2;
/*				
				if ( debug )
				{
					double eq1 = chop( TY_LinearEquation_1( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					double eq2 = chop( TY_LinearEquation_2( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					double eq3 = chop( TY_LinearEquation_3( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					double eq4 = chop( TY_LinearEquation_4( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					double eq5 = chop( TY_NonlinearEquation_1( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					double eq6 = chop( TY_NonlinearEquation_2( Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] ) );
					
					sprintf(buf, "solution[%d] = (%g, %g, %g, %g, %g, %g), ( eq == 0 ) = (%g, %g, %g, %g, %g, %g)\r", j, 
						   sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j], 
						   eq1 , eq2, eq3, eq4, eq5, eq6 );
					XOPNotice(buf);
				}
 */
				j++;
			}
		}
	}
	// number  remaining roots 
	n_roots = j;
	
	
	// if there is still more than one root left, than choose the one with the minimum
	// average value inside the hardcore
	if ( n_roots > 1 )
	{
		// the number of q values should be a power of 2
		// in order to speed up the FFT
		n = 1 << 14;
		
		// the maximum q value should be large enough 
		// to enable a reasoble approximation of g(r)
		qmax = 16 * 10 * 2 * Pi;
		dq = qmax / ( n - 1 );
		
		// step size for g(r) = dr
		
		// allocate memory for pair correlation function g(r)
		// and structure factor S(q)
		sq = malloc( sizeof( double ) * n );
		gr = malloc( sizeof( double ) * n );
		
		// loop over all remaining roots
		min = 1e99;
		selected_root = 10;	
		sum = 0;
		for ( j = 0; j < n_roots; j++) 
		{
			// calculate structure factor at different q values
			for ( i = 0; i < n; i++) 
			{
				q = dq * i;
				sq[i] = SqTwoYukawa( q, Z1, Z2, K1, K2, phi, sol_a[j], sol_b[j], sol_c1[j], sol_c2[j], sol_d1[j], sol_d2[j] );
/*				
				if(i<20 && debug) {
					sprintf(buf, "after SqTwoYukawa: s(q) = %g\r",sq[i] );
					XOPNotice(buf);	
				}
 */
			}
			
			// calculate pair correlation function for given
			// structure factor, g(r) is computed at values
			// r(i) = i * dr
			PairCorrelation( phi, dq, sq, &dr, gr, n );
			// determine sum inside the hardcore 
			// 0 =< r < 1 of the pair-correlation function
			sum = 0;
			for (i = 0; i < floor( 1. / dr ); i++ )  {
				sum += fabs( gr[i] );
/*				
				if(i<20 && debug) {
					sprintf(buf, "g(r) in core = %g\r",fabs(gr[i]));
					XOPNotice(buf);
				}
*/				
			}

			if ( sum < min )
			{
				min = sum;
				selected_root = j;
			}
		}	
		free( gr );
		free( sq );
		
		// physical solution was found
		*a  = sol_a [ selected_root ];//sol_a [ selected_root ];
		*b  = sol_b [ selected_root ];
		*c1 = sol_c1[ selected_root ];
		*c2 = sol_c2[ selected_root ];
		*d1 = sol_d1[ selected_root ];
		*d2 = sol_d2[ selected_root ];
		
		return 1;
	}
	else if ( n_roots == 1 ) 
	{
		*a  = sol_a [0];
		*b  = sol_b [0];
		*c1 = sol_c1[0];
		*c2 = sol_c2[0];
		*d1 = sol_d1[0];
		*d2 = sol_d2[0];
		
		return 1;
	}

	// no solution was found
	return 0;
}
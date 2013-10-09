/*
 *  Yukawa.c
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/12/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

#include "2Y_OneYukawa.h"
#include "2Y_cpoly.h"
#include "2Y_utility.h"
#include "2Y_PairCorrelation.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/*
================================================================================================== 
 
 Structure factor for the potential 
 
 V(r) = -kB * T * K * exp[ -Z * (r - 1)] / r for r > 1
 V(r) = inf for r <= 1
 
 The structure factor is parametrized by (a, b, c, d) 
 which depend on (Z, K, phi).  
 
================================================================================================== 
*/

double Y_sigma( double s, double Z, double a, double b, double c, double d )
{
	return -(a / 2. + b + c * exp( -Z )) / s + a * pow( s, -3 ) + b * pow( s, -2 ) + ( c + d ) * pow( s + Z, -1 );
}

double Y_tau( double s, double Z, double a, double b, double c )
{
	return b * pow( s, -2 ) + a * ( pow( s, -3 ) + pow( s, -2 ) ) - pow( s, -1 ) * c * Z * exp( -Z ) * pow( s + Z, -1 );
} 

double Y_q( double s, double Z, double a, double b, double c, double d )
{
	return Y_sigma(s, Z, a, b, c, d ) - exp( -s ) * Y_tau( s, Z, a, b, c );
}

double Y_g( double s, double phi, double Z, double a, double b, double c, double d )
{
	return s * Y_tau( s, Z, a, b, c ) * exp( -s ) / ( 1 - 12 * phi * Y_q( s, Z, a, b, c, d ) );
}

double Y_hq( double q, double Z, double K, double v )
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

double Y_pc( double q, 
			double Z, double K, double phi,
			double a, double b, double c, double d )
{	
	double v = 24 * phi * K * exp( Z ) * Y_g( Z, phi, Z, a, b, c, d );
	
	double a0 = a * a;
	double b0 = -12 * phi *( pow( a + b,2 ) / 2 + a * c * exp( -Z ) );
	
	double t1, t2, t3, t4;
	
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
	t4 = Y_hq( q, Z, K, v );
	return -24 * phi * ( t1 + t2 + t3 + t4 );
}

double SqOneYukawa( double q, 
				 double Z, double K, double phi,
				 double a, double b, double c, double d )
{
	//structure factor one-yukawa potential
	return 1. / ( 1. - Y_pc( q, Z, K, phi, a, b, c, d ) );
}


/*
================================================================================================== 

 The structure factor S(q) for the one-Yukawa potential is parameterized by a,b,c,d which are
 the solution of a system of non-linear equations given Z,K, phi. There are at most 4 solutions 
 from which the physical one is chosen
 
================================================================================================== 
 */

double Y_LinearEquation_1( double Z, double K, double phi, double a, double b, double c, double d )
{
	return b - 12*phi*(-a/8. - b/6. + d*pow(Z,-2) + c*(pow(Z,-2) - exp(-Z)*(0.5 + (1 + Z)*pow(Z,-2))));
}

double Y_LinearEquation_2( double Z, double K, double phi, double a, double b, double c, double d )
{
	return 1 - a - 12*phi*(-a/3. - b/2. + d*pow(Z,-1) + c*(pow(Z,-1) - (1 + Z)*exp(-Z)*pow(Z,-1)));
}

double Y_LinearEquation_3( double Z, double K, double phi, double a, double b, double c, double d )
{
	return K*exp(Z) - Z*d*(1-12*phi*Y_q(Z, Z, a, b, c, d));
}

double Y_NonlinearEquation( double Z, double K, double phi, double a, double b, double c, double d )
{
	return c + d - 12*phi*((c + d)*Y_sigma(Z, Z, a, b, c, d) - c*exp(-Z)*Y_tau(Z, Z, a, b, c));
}

// Check the computed solutions satisfy the system of equations 
int Y_CheckSolution( double Z, double K, double phi, 
					 double a, double b, double c, double d )
{
	double eq_1 = chop( Y_LinearEquation_1 ( Z, K, phi, a, b, c, d ) );
	double eq_2 = chop( Y_LinearEquation_2 ( Z, K, phi, a, b, c, d ) );
	double eq_3 = chop( Y_LinearEquation_3 ( Z, K, phi, a, b, c, d ) );
	double eq_4 = chop( Y_NonlinearEquation( Z, K,  phi, a, b, c, d ) );
	
	// check if all equation are zero
	return eq_1 == 0 && eq_2 == 0 && eq_3 == 0 && eq_4 == 0;
}

int Y_SolveEquations( double Z, double K, double phi, double* a, double* b, double* c, double* d, int debug )
{
	char buf[256];

	// at most there are 4 solutions for a,b,c,d
	double sol_a[4], sol_b[4], sol_c[4], sol_d[4];
	
	double m11 = (3*phi)/2.;
	double m13 = 6*phi*exp(-Z)*(2 + Z*(2 + Z) - 2*exp(Z))*pow(Z,-2);
	double m23 = -12*phi*exp(-Z)*(-1 - Z + exp(Z))*pow(Z,-1);
	double m31 = -6*phi*exp(-Z)*pow(Z,-2)*(2*(1 + Z) + exp(Z)*(-2 + pow(Z,2)));
	double m32 = -12*phi*(-1 + Z + exp(-Z))*pow(Z,-1);
	double m33 = 6*phi*exp(-2*Z)*pow(-1 + exp(Z),2);
	
	double delta = m23*m31 - m13*m32 + m11*(-4*m13*m31 + (4*m23*m31)/3. + (8*m13*m32)/3. - m23*m32) + m33 + (4*(-3 + m11)*m11*m33)/9.;
	double a1 = -(K*(m23 + (4*m11*(-3*m13 + m23))/3.)*exp(Z));
	double a2 = -(m13*(m32 + 4*m11*Z)) + ((3 + 4*m11)*(m33 + m23*Z))/3.;
	double a3 = -2*phi*pow(Z,-2)*(6*m23*m32 - 24*m11*m33 + 2*Z*((3 + 4*m11)*m33 - 3*m13*(m32 + 2*m11*Z)) + (3 + 4*m11)*m23*pow(Z,2));
	
	double b1 = -(K*((-3 + 8*m11)*m13 - 3*m11*m23)*exp(Z))/3.;
	double b2 = m13*(m31 - Z + (8*m11*Z)/3.) - m11*(m33 + m23*Z);
	double b3 = 2*phi*pow(Z,-2)*(m13*Z*(-6*m31 + 3*Z - 8*m11*Z) + 2*m33*(3 - 8*m11 + 3*m11*Z) + 3*m23*(2*m31 + m11*pow(Z,2)));
	
	double c1 = -(K*exp(Z)*pow(3 - 2*m11,2))/9.;
	double c2 = -((3 + 4*m11)*m31)/3. + m11*m32 + Z + (4*(-3 + m11)*m11*Z)/9.;
	double c3 = (-2*phi*pow(Z,-2)*(6*(12*m11*m31 + 3*m32 - 8*m11*m32) - 6*((3 + 4*m11)*m31 - 3*m11*m32)*Z + pow(3 - 2*m11,2)*pow(Z,2)))/3.;
	
	// determine d, as roots of the polynomial, from that build a,b,c
	
	double real_coefficient[5];
	double imag_coefficient[5];
	
	double real_root[4];
	double imag_root[4];
	
	double zeta = 24*phi*pow(-6*phi*Z*cosh(Z/2.) + (12*phi + (-1 + phi)*pow(Z,2))*sinh(Z/2.),2);	
	double A[5];
	int degree,i,j,n_roots;
	double x,y;
	int n,selected_root;
	double qmax,q,dq,min,sum,dr;
	double *sq,*gr;
	
	
	A[0] = -(exp(3*Z)*pow(K,2)*pow(-1 + phi,2)*pow(Z,3) / zeta );
	A[1] = K*Z*exp(Z)*(6*phi*(2 + 4*phi + (2 + phi)*Z) + exp(Z)*
					   ((-24 + Z*(18 + (-6 + Z)*Z))*pow(phi,2) - 2*phi*(6 + (-3 + Z)*pow(Z,2)) + pow(Z,3))) / zeta;
	A[2] = -12*K*phi*exp(Z)*pow(-1 + phi,2)*pow(Z,3)/zeta;
	A[3] = 6*phi*Z*exp(-Z)*(-12*phi*(1 + 2*phi)*(-1 + exp(Z)) + 6*phi*Z*(3*phi + (2 + phi)*exp(Z)) + 
							6*(-1 + phi)*phi*pow(Z,2) + pow(-1 + phi,2)*pow(Z,3))/zeta;
	A[4] = -36*exp(-Z)*pow(-1 + phi,2)*pow(phi,2)*pow(Z,3)/zeta;
/*	
	if ( debug )
	{
		sprintf (buf, "(Z,K,phi) = (%g, %g, %g)\r", K, Z, phi );
		XOPNotice(buf);
		sprintf (buf, "A = (%g, %g, %g, %g, %g)\r", A[0], A[1], A[2], A[3], A[4] );
		XOPNotice(buf);
	}
*/	
	//integer degree of polynomial
	degree = 4;
	
	// vector of real and imaginary coefficients in order of decreasing powers
	for ( i = 0; i <= degree; i++ )
	{
		real_coefficient[i] = A[4-i];
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
			sprintf(buf, "root(%d) = %g + %g i\r", i+1, x, y );
			XOPNotice(buf);
		}
		sprintf(buf, "\r" );
		XOPNotice(buf);
	}
 */
	// determine the set of solutions for a,b,c,d,
	j = 0;
	for ( i = 0; i < degree; i++ ) 
	{
		x = real_root[i];
		y = imag_root[i];
		
		if ( chop( y ) == 0 ) 
		{
			sol_a[j] = ( a1 + a2 * x + a3 * x * x ) / ( delta * x );
			sol_b[j] = ( b1 + b2 * x + b3 * x * x ) / ( delta * x );
			sol_c[j] = ( c1 + c2 * x + c3 * x * x ) / ( delta * x );
			sol_d[j] = x;
	
			j++;
		}
	}

	// number  remaining roots 
	n_roots = j;
	
//	sprintf(buf, "inside Y_solveEquations OK, before malloc: n_roots = %d\r",n_roots);
//	XOPNotice(buf);	
	
	// if there is still more than one root left, than choose the one with the minimum
	// average value inside the hardcore
	
	
	
	if ( n_roots > 1 )
	{
		// the number of q values should be a power of 2
		// in order to speed up the FFT
		n = 1 << 14;		//= 16384
		
		// the maximum q value should be large enough 
		// to enable a reasoble approximation of g(r)
		qmax = 1000.;
		dq = qmax / ( n - 1 );
		
		// step size for g(r) = dr
		
		// allocate memory for pair correlation function g(r)
		// and structure factor S(q)
		// (note that sq and gr are pointers)
		sq = malloc( sizeof( double ) * n );
		gr = malloc( sizeof( double ) * n );
		
		// loop over all remaining roots
		min = 1e99;
		selected_root=0;	
		
//		sprintf(buf, "after malloc: n,dq = %d  %g\r",n,dq);
//		XOPNotice(buf);
				
		for ( j = 0; j < n_roots; j++) 
		{
			// calculate structure factor at different q values
			for ( i = 0; i < n ; i++) 
			{
				q = dq * i;
				sq[i] = SqOneYukawa( q, Z, K, phi, sol_a[j], sol_b[j], sol_c[j], sol_d[j] );
/*				
				if(i<20 && debug) {
					sprintf(buf, "after SqOneYukawa: s(q) = %g\r",sq[i] );
					XOPNotice(buf);	
				}
 */
			}
						
			// calculate pair correlation function for given
			// structure factor, g(r) is computed at values
			// r(i) = i * dr
			PairCorrelation( phi, dq, sq, &dr, gr, n );
			
//			sprintf(buf, "after PairCorrelation: \r");
//			XOPNotice(buf);
			
			// determine sum inside the hardcore 
			// 0 =< r < 1 of the pair-correlation function
			sum = 0;
			for (i = 0; i < floor( 1. / dr ); i++ ) 
			{
				sum += fabs( gr[i] );
/*				
				if(i<20 && debug) {
					sprintf(buf, "g(r) in core = %g\r",fabs(gr[i]));
					XOPNotice(buf);
				}
 */
			}
			
//			sprintf(buf, "after hard core: sum, min = %g %g\r",sum,min);
//			XOPNotice(buf);
			
			if ( sum < min )
			{
				min = sum;
				selected_root = j;
			}
			
			
		}	
		free( gr );
		free( sq );
		
//		sprintf(buf, "after free: selected root = %d\r",selected_root);
//		XOPNotice(buf);
		
		// physical solution was found
		*a = sol_a[ selected_root ];
		*b = sol_b[ selected_root ];
		*c = sol_c[ selected_root ];
		*d = sol_d[ selected_root ];
		
//		sprintf(buf, "after solution found (ret 1): \r");
//		XOPNotice(buf);
		
		return 1;
	}
	else if ( n_roots == 1 ) 
	{
		*a = sol_a[0];
		*b = sol_b[0];
		*c = sol_c[0];
		*d = sol_d[0];
		
		return 1;
	}
	// no solution was found
	return 0;
}

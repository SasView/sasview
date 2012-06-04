/*
 *  PairCorrelation.c
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/9/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

#include "2Y_PairCorrelation.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
//#include <gsl/gsl_errno.h> 
//#include <gsl/gsl_fft_real.h>

/*
=================================================================================================== 

 Source: J.B.Hayter: A Program for the fast bi-directional transforms
 between g(r) and S(Q), ILL internal scientific report, October 1979
 
 The transformation between structure factor and pair correlation 
 function is given by 
 
 g(x) = 1 + 1 / (12*pi*phi*x) * int( [S(q)-q]*q*sin(q*x), { 0, inf } )
 
 where phi is the volume frcation, x and q are dimensionless variables, 
 scaled by the radius a of the particles:
 
 r = x * a;
 Q = q / a
 
 Discretizing the integral leads to
 
 x[k] = 2*pi*k / (N * dq)
 g(x[k]) = 1 + N*dq^3 / (24*pi^2*phi*k) * Im{ sum(S[n]*exp(2*pi*i*n*k/N),{n,0,N-1}) }
 
 where S[n] = n*(S(q[n])-1) with q[n]=n * dq

=================================================================================================== 
*/

/*
int PairCorrelation_GSL( double phi, double dq, double* Sq, double* dr, double* gr, int N )
{
	double* data = malloc( sizeof(double) * N );
	int n;
	for ( n = 0; n < N; n++ )
		data[n] = n * ( Sq[n] - 1 );
	
	// data[k] -> sum( data[n] * exp(-2*pi*i*n*k/N), {n, 0, N-1 })
	int stride = 1;
	int error  = gsl_fft_real_radix2_transform( data, stride, N );
	
	// if no errors detected 
	if ( error == GSL_SUCCESS ) 
	{
		double alpha = N * pow( dq, 3 ) / ( 24 * M_PI * M_PI * phi );
	
	
		*dr = 2 * M_PI / ( N * dq );  
		int k;
		double real, imag;
		for ( k = 0; k < N; k++ )
		{
			// the solutions of the transform is stored in data, 
			// consult GSL manual for more details
			if ( k == 0 || k == N / 2)
			{ 
				real = data[k];
				imag = 0;
			}
			else if ( k < N / 2 ) 
			{
				real = data[k];
				imag = data[N-k];
			}
			else if ( k > N / 2 )
			{
				real =  data[N-k];
				imag = -data[k];	
			}
			
			if ( k == 0 ) 
				gr[k] = 0;
			else
				gr[k] = 1. + alpha / k * (-imag);
		} 
	} 
	// if N is not a power of two
	else if ( error == GSL_EDOM )
	{
		printf( "N is not a power of 2\n" );
	}
	else
	{
		printf( "Could not perform DFT (discrete fourier transform)\n" );
	}
	// release allocated memory
	free( data );
	
	// return error value
	return error;
}
 */


// this uses numerical recipes for the FFT
//
int PairCorrelation( double phi, double dq, double* Sq, double* dr, double* gr, int N )
{
	double* data = malloc( sizeof(double) * N * 2);
	int n,error,k;
	double alpha,real,imag;
	double Pi = 3.14159265358979323846264338327950288;   /* pi */

	
	for ( n = 0; n < N; n++ ) {
		data[2*n] = n * ( Sq[n] - 1 );
		data[2*n+1] = 0;
	}
	//	printf("start of new fft\n");
	
	// data[k] -> sum( data[n] * exp(-2*pi*i*n*k/N), {n, 0, N-1 })
	//	int error  = gsl_fft_real_radix2_transform( data, stride, N );
	error  = 1;
	dfour1( data-1, N, 1 );		//N is the number of complex points
	
	//	printf("dfour1 is done\n");
	
	// if no errors detected 
	if ( error == 1 ) 
	{
		alpha = N * pow( dq, 3 ) / ( 24 * Pi * Pi * phi );
		
		*dr = 2 * Pi / ( N * dq );  
		for ( k = 0; k < N; k++ )
		{
			// the solutions of the transform is stored in data, 
			// consult GSL manual for more details
			if ( 2*k == 0 || 2*k == 2*N / 2)
			{ 
				real = data[2*k];
				imag = 0;
			}
			else if ( 2*k < 2*N / 2 ) 
			{
				real = data[2*k];
				imag = data[2*k+1];
			}
			else if ( 2*k > 2*N / 2 )
			{
				real =  data[2*k];
				imag = -data[2*k+1];	
			}
			
			if ( k == 0 ) 
				gr[k] = 0;
			else
//				gr[k] = 1. + alpha / k * (-imag);		//if using GSL
				gr[k] = 1. + alpha / k * (imag);		//if using NR
		} 
	} 
	
	// release allocated memory
	free( data );
	
//	printf(" done with FFT assignment -- Using Numerical Recipes, not GSL\n");
	
	// return error value
	return error;
}


// isign == 1 means no scaling of output. isign == -1 multiplies output by nn
//
//
#define SWAP(a,b) tempr=(a);(a)=(b);(b)=tempr

void dfour1(double data[], unsigned long nn, int isign)
{
	unsigned long n,mmax,m,j,istep,i;
	double wtemp,wr,wpr,wpi,wi,theta;
	double tempr,tempi;
	
	n=nn << 1;
	j=1;
	for (i=1;i<n;i+=2) {
		if (j > i) {
			SWAP(data[j],data[i]);
			SWAP(data[j+1],data[i+1]);
		}
		m=n >> 1;
		while (m >= 2 && j > m) {
			j -= m;
			m >>= 1;
		}
		j += m;
	}
	mmax=2;
	while (n > mmax) {
		istep=mmax << 1;
		theta=isign*(6.28318530717959/mmax);
		wtemp=sin(0.5*theta);
		wpr = -2.0*wtemp*wtemp;
		wpi=sin(theta);
		wr=1.0;
		wi=0.0;
		for (m=1;m<mmax;m+=2) {
			for (i=m;i<=n;i+=istep) {
				j=i+mmax;
				tempr=wr*data[j]-wi*data[j+1];
				tempi=wr*data[j+1]+wi*data[j];
				data[j]=data[i]-tempr;
				data[j+1]=data[i+1]-tempi;
				data[i] += tempr;
				data[i+1] += tempi;
			}
			wr=(wtemp=wr)*wpr-wi*wpi+wr;
			wi=wi*wpr+wtemp*wpi+wi;
		}
		mmax=istep;
	}
}
#undef SWAP

/*
 *  TwoYukawa.h
 *  TwoYukawa
 *
 *  Created by Marcus Hennig on 5/8/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */
int TY_SolveEquations( double Z1, double Z2, double K1, double K2, double phi, 
				       double a[], double b[], double c1[], double c2[], double d1[], double d2[], 
				       int debug );

int TY_CheckSolution( double Z1, double Z2, double K1, double K2, double phi, 
				      double a, double b, double c1, double c2, double d1, double d2 );

double SqTwoYukawa( double q, 
			        double Z1, double Z2, double K1, double K2, double phi,
			        double a, double b, double c1, double c2, double d1, double d2 );

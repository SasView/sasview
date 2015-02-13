/*
 *  Yukawa.h
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/12/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */
int Y_CheckSolution( double Z, double K, double phi, double a, double b, double c, double d );
int Y_SolveEquations( double Z, double K, double phi, 
					  double* a, double* b, double* c, double* d, int debug );
double SqOneYukawa( double q, 
				double Z, double K, double phi,
				double a, double b, double c, double d );

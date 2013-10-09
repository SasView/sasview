/*
 *  PairCorrelation.h
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/9/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

//int PairCorrelation_GSL( double phi, double dq, double* Sq, double* dr, double* gr, int N );
int PairCorrelation( double phi, double dq, double* Sq, double* dr, double* gr, int N );

void dfour1(double data[], unsigned long nn, int isign);
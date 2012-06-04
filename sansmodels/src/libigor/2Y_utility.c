/*
 *  utility.c
 *  twoyukawa
 *
 *  Created by Marcus Hennig on 5/13/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

#include "2Y_utility.h"
double chop( double x )
{
	if ( fabs(x) < 1E-6 )
		return 0;
	else 
		return x;
}
/*
 *  StandardHeaders.h
 *  SANSAnalysis
 *
 *  Created by Andrew Jackson on 4/23/07.
 *
 */

#include <math.h>
#include <ctype.h>

/** 
 * VC7 does not have fmax and trunc.
 * Define them here.
 * Added by M. Doucet (4/25/07)
 */

#ifdef _MSC_VER

#ifndef _INC_FMINMAX
#define _INC_FMINMAX

#ifndef fmax
#define fmax(a,b)            (((a) > (b)) ? (a) : (b))
#endif

#ifndef fmin
#define fmin(a,b)            (((a) < (b)) ? (a) : (b))
#endif

#ifndef trunc
#define trunc(a)             (((a) < (0)) ? (ceil(a)) : (floor(a)))
#endif

#endif

#endif

    

    

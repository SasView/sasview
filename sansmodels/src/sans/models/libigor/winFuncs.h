#if !defined(WINFUNCS_H)
#define WINFUNCS_H
/* winFuncs.h
   Definitions for missing math lib functions
   Andrew Jackson, October 2007
   */

double fmax(double x, double y);
//long double fmaxl (long double x, long double y);
//float fmaxf (float x, float y);

double fmin(double x, double y);

double trunc(double x);
//long double truncl(long double x);
//float truncf(float x);

double erf(double x);
//long double erfl(long double x);
//float erff (float x);
//double erfc(double x);
//long double erfcl(long double x);
//float erfcf(float x;


// Define INFINITY and NAN
typedef union { unsigned char __c[4]; float __f; } __huge_valf_t;

# if __BYTE_ORDER == __BIG_ENDIAN
#  define __HUGE_VALF_bytes { 0x7f, 0x80, 0, 0 }
# endif
# if __BYTE_ORDER == __LITTLE_ENDIAN
#  define __HUGE_VALF_bytes { 0, 0, 0x80, 0x7f }
# endif

static __huge_valf_t __huge_valf = { __HUGE_VALF_bytes };
# define INFINITY  (__huge_valf.__f)


# if __BYTE_ORDER == __BIG_ENDIAN
#  define __nan_bytes   { 0x7f, 0xc0, 0, 0 }
# endif
# if __BYTE_ORDER == __LITTLE_ENDIAN
#  define __nan_bytes   { 0, 0, 0xc0, 0x7f }
# endif

static union { unsigned char __c[4]; float __d; } __nan_union;
# define NAN  (__nan_union.__d)

#endif

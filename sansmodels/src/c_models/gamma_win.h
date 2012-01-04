// Visit http://www.johndcook.com/stand_alone_code.html for the source of this code and more like it.

#ifndef GAMMA_H
#define GAMMA_H

// Note that the functions Gamma and LogGamma are mutually dependent.
#ifdef __cplusplus
extern "C" {
#endif

double lgamma(double);
double gamma(double);

#ifdef __cplusplus
}
#endif

#endif


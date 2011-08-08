/** \file myutil.cc */
#include <cstdlib>
#include <ctime> 
#include "myutil.h"

using namespace std;

void seed_rnd() {
	srand((unsigned)time(NULL)); 
}

double ran1()
{
	return (double)rand() / (double) RAND_MAX;
}


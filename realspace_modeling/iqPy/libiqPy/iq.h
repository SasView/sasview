/** \file iq.h   class IQ  */

#ifndef IQ_H
#define IQ_H

#include <string>
/**tnt: template numerical toolkit, http://math.nist.gov/tnt/ */
#include "tnt/tnt.h"
using namespace TNT;

class IQ{
  
 public:
  IQ(int numI);
  IQ(int numI,double qmin, double qmax);

  void SetQmin(double qmin);
  void SetQmax(double qmax);
  void SetContrast(double delrho);
  void SetVolFrac(double vol_frac);
  void SetIQArray(Array2D<double> iq_array);

  double GetQmin();
  double GetQmax();
  double GetContrast();
  double GetVolFrac();
  int GetNumI();

  void OutputIQ(std::string fiq);

  Array2D<double> iq_data;

 private:
  IQ();
  double qmin_;
  double qmax_;
  double delrho_;
  int numI_;
  double vol_frac_;


};


#endif

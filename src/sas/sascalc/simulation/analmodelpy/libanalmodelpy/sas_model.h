/** \file sas_model.h    class SASModel virtual base class */

#ifndef SASMODEL_H
#define SASMODEL_H

#include "iq.h"

class SASModel{
 public:

  virtual void CalculateIQ(IQ *iq) = 0;

};

#endif

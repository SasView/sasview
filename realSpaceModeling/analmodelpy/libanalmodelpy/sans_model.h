/** \file sans_model.h    class SANSModel virtual base class */

#ifndef SANSMODEL_H
#define SANSMODEL_H

#include "iq.h"

class SANSModel{
 public:

  virtual void CalculateIQ(IQ *iq) = 0;

};

#endif

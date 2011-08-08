/** \file analytical_model.h class AnalyticalModel:SANSModel */

#ifndef ANALYTICALMODEL_H
#define ANALYTICALMODEL_H

#include "sans_model.h"
#include "geo_shape.h"
#include "iq.h"

class AnalyticalModel : public SANSModel{

 public:
  AnalyticalModel(const GeoShape &);
  ~AnalyticalModel();

  void CalculateIQ(IQ *);

 private:
  AnalyticalModel();
  GeoShape *shape_;
};

#endif

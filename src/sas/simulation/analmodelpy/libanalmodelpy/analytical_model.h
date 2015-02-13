/** \file analytical_model.h class AnalyticalModel:SASModel */

#ifndef ANALYTICALMODEL_H
#define ANALYTICALMODEL_H

#include "sas_model.h"
#include "geo_shape.h"
#include "iq.h"

class AnalyticalModel : public SASModel{

 public:
  AnalyticalModel(const GeoShape &);
  ~AnalyticalModel();

  void CalculateIQ(IQ *);

 private:
  AnalyticalModel();
  GeoShape *shape_;
};

#endif

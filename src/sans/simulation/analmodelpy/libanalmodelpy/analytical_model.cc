/** \file analytical_model.cc  */

#include "sphere.h"
#include "hollow_sphere.h"
#include "analytical_model.h"

AnalyticalModel::AnalyticalModel(const GeoShape &geo_shape)
{
  switch (geo_shape.GetShapeType()){
    case SPHERE:
      shape_ = new Sphere(static_cast<const Sphere&>(geo_shape));
      break;
    case HOLLOWSPHERE:
      shape_ = new HollowSphere(static_cast<const HollowSphere&>(geo_shape));
      break;
    case CYLINDER:
      break;
  }
}

AnalyticalModel::~AnalyticalModel() 
{
  if (shape_ != NULL) delete shape_;
}

void AnalyticalModel::CalculateIQ(IQ * iq)
{
  shape_->GetFormFactor(iq);
}

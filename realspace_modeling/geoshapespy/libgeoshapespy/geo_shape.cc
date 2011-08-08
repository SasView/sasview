#include "geo_shape.h"

void GeoShape::SetOrientation(double angX,double angY, double angZ){
  orientation_[0]=angX;
  orientation_[1]=angY;
  orientation_[2]=angZ;
}

void GeoShape::SetCenter(double cenX,double cenY,double cenZ){
  center_[0]=cenX;
  center_[1]=cenY;
  center_[2]=cenZ;
}

vector<double> GeoShape::GetOrientation() const {
  return orientation_;
}

vector<double> GeoShape::GetCenter() const {
  return center_;
}

Point3D GeoShape::GetCenterP() const {
  Point3D p(center_[0],center_[1],center_[2]);
  return p;
}

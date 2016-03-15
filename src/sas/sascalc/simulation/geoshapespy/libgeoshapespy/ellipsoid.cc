/** \file Ellipsoid.cc */
#include <cmath>
#include <cassert>
#include <algorithm>
//MS library does not define min max in algorithm
//#include "minmax.h"
#include "ellipsoid.h"
#include "myutil.h"

using namespace std;

Ellipsoid::Ellipsoid()
{
  rx_ = 0;
  ry_ = 0;
  rz_ = 0;
}

Ellipsoid::Ellipsoid(double rx, double ry, double rz)
{
  rx_ = rx;
  ry_ = ry;
  rz_ = rz;
  xedge_plus_ = Point3D(rx,0,0);
  xedge_minus_ = Point3D(-rx,0,0);
  yedge_plus_ = Point3D(0,ry,0);
  yedge_minus_ = Point3D(0,-ry,0);
  zedge_plus_ = Point3D(0,0,rz);
  zedge_minus_ = Point3D(0,0,-rz);
}

Ellipsoid::~Ellipsoid()
{
}

void Ellipsoid::SetRadii(double rx, double ry, double rz)
{
  rx_ = rx;
  ry_ = ry;
  rz_ = rz;
}

double Ellipsoid::GetRadiusX()
{
  return rx_;
}

double Ellipsoid::GetRadiusY()
{
  return ry_;
}

double Ellipsoid::GetRadiusZ()
{
  return rz_;
}

double Ellipsoid::GetMaxRadius()
{
  double maxr = max(max(rx_,ry_),max(ry_,rz_));
  return maxr;
}

ShapeType Ellipsoid::GetShapeType() const
{
  return ELLIPSOID;
}

double Ellipsoid::GetVolume()
{
  double V = (4./3.)*pi*rx_*ry_*rz_;
  return V;
}

void Ellipsoid::GetFormFactor(IQ * iq)
{
  /** number of I for output, equal to the number of rows of array IQ*/
  /** to be finished */
}

Point3D Ellipsoid::GetAPoint(double sld)
{
  static int max_try = 100;
  for (int i = 0; i < max_try; ++i) {
    double x = (ran1()-0.5) * 2 * rx_;
    double y = (ran1()-0.5) * 2 * ry_;	
    double z = (ran1()-0.5) * 2 * rz_;

    if ((square(x/rx_) + square(y/ry_) + square(z/rz_)) <= 1){
      Point3D apoint(x,y,z,sld);
      return apoint;
    }
  }

  std::cerr << "Max try "
            << max_try
            << " is reached while generating a point in ellipsoid" << std::endl;
  return Point3D(0, 0, 0);
}

bool Ellipsoid::IsInside(const Point3D& point) const
{
  //x, y, z axis are internal axis
  bool isOutsideX = false;
  Point3D pointOnX = point.getInterPoint(GetXaxisPlusEdge(),GetXaxisMinusEdge(),&isOutsideX);
  bool isOutsideY = false;
  Point3D pointOnY = point.getInterPoint(GetYaxisPlusEdge(),GetYaxisMinusEdge(),&isOutsideY);
  bool isOutsideZ = false;
  Point3D pointOnZ = point.getInterPoint(GetZaxisPlusEdge(),GetZaxisMinusEdge(),&isOutsideZ);

  if (isOutsideX || isOutsideY || isOutsideZ){
    //one is outside axis is true -> the point is not inside
    return false;    
  }
  else{
    Point3D pcenter = GetCenterP();
    double distX = pointOnX.distanceToPoint(pcenter);
    double distY = pointOnY.distanceToPoint(pcenter);
    double distZ = pointOnZ.distanceToPoint(pcenter);
    return ((square(distX/rx_)+square(distY/ry_)+square(distZ/rz_)) <= 1);
  }

}

Point3D Ellipsoid::GetXaxisPlusEdge() const
{
  Point3D new_edge(xedge_plus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

Point3D Ellipsoid::GetXaxisMinusEdge() const
{
  Point3D new_edge(xedge_minus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

Point3D Ellipsoid::GetYaxisPlusEdge() const
{
  Point3D new_edge(yedge_plus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

Point3D Ellipsoid::GetYaxisMinusEdge() const
{
  Point3D new_edge(yedge_minus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

Point3D Ellipsoid::GetZaxisPlusEdge() const
{
  Point3D new_edge(zedge_plus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

Point3D Ellipsoid::GetZaxisMinusEdge() const
{
  Point3D new_edge(zedge_minus_);
  new_edge.Transform(GetOrientation(),GetCenter());
  return new_edge;
}

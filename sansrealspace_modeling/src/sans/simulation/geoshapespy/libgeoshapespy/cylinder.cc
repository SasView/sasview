/** \file Cylinder.cc */
#include <cmath>
#include <cassert>
#include "cylinder.h"
#include "myutil.h"

Cylinder::Cylinder()
{
  r_ = 0;
}

Cylinder::Cylinder(double radius,double length)
{
  r_ = radius;
  l_ = length;
  topcenter_ = Point3D(0,length/2,0);
  botcenter_ = Point3D(0,-length/2,0);
}

Cylinder::~Cylinder()
{
}

void Cylinder::SetRadius(double r)
{
  r_ = r;
}

void Cylinder::SetLength(double l)
{
  l_ = l;
}

double Cylinder::GetRadius()
{
  return r_;
}

double Cylinder::GetLength()
{
  return l_;
}

double Cylinder::GetMaxRadius()
{
  double maxr = sqrt(4*r_*r_ + l_*l_)/2;
  return maxr;
}

ShapeType Cylinder::GetShapeType() const
{
  return CYLINDER;
}

double Cylinder::GetVolume()
{
  double V = pi * square(r_) * l_;
  return V;
}

void Cylinder::GetFormFactor(IQ * iq)
{
  /** number of I for output, equal to the number of rows of array IQ*/
  /** to be finished */
}

Point3D Cylinder::GetAPoint(double sld)
{
  /** cylinder long axis is along Y to match vtk actor */
  static int max_try = 100;
  for (int i = 0; i < max_try; ++i) {
    double x = (ran1()-0.5) * 2 * r_;
    double z = (ran1()-0.5) * 2 * r_;	
    double y = (ran1()-0.5) * l_;

    Point3D apoint(x,y,z,sld);
    //check the cross section on xy plane within a sphere at (0,)
    if (apoint.distanceToPoint(Point3D(0,y,0)) <= r_ ) 
      return apoint;
  }

  std::cerr << "Max try "
            << max_try
            << " is reached while generating a point in cylinder" << std::endl;
  return Point3D(0, 0, 0);
}

bool Cylinder::IsInside(const Point3D& point) const
{
  bool isOutside = false;
  double distToLine = point.distanceToLine(GetTopCenter(),GetBotCenter(),&isOutside);

  return (distToLine <= r_ && !isOutside);
}

Point3D Cylinder::GetTopCenter() const
{
  Point3D new_center(topcenter_);
  new_center.Transform(GetOrientation(),GetCenter());
  return new_center;
}

Point3D Cylinder::GetBotCenter() const
{
  Point3D new_center(botcenter_);
  new_center.Transform(GetOrientation(),GetCenter());
  return new_center;
}

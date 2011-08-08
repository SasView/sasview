/** \file hollowsphere.h class HollowSphere:GeoShape */

#ifndef HOLLOWSPHERE_H
#define HOLLOWSPHERE_H

#include "geo_shape.h"

/** class Sphere, subclass of GeoShape */
class HollowSphere : public GeoShape {
 public:

  /** initialize */
  HollowSphere();

  /** constructor with radius&length initialization */
  HollowSphere(double radius, double thickness);

  /** get the radius of the sphere to cover this shape */
  double GetMaxRadius();

  /** calculate the sphere form factor, no scale, no background*/
  void GetFormFactor(IQ * iq);

  /** using a equation to check whether a point with XYZ lies
      within the sphere with center (0,0,0)
  */
  Point3D GetAPoint(double sld);

  /** check whether point is inside hollow sphere*/
  bool IsInside(const Point3D& point) const;

  double GetVolume();

  //get the shape type, return sphere 
  ShapeType GetShapeType() const;

 private:
  //outer radius, and the thickness of the shell
  double ro_, th_;

};

#endif

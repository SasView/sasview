/** \file sphere.h class Sphere:GeoShape */

#ifndef SPHERE_H
#define SPHERE_H

#include "geo_shape.h"

/** class Sphere, subclass of GeoShape */
class Sphere : public GeoShape {
 public:

  /** initialize */
  Sphere();

  /** constructor with radius initialization */
  Sphere(double radius);

  ~Sphere();

  /** set parameter radius */
  void SetRadius(double r);

  /** get the radius */
  double GetRadius();

  /** Get the radius of the sphere to cover this shape */
  double GetMaxRadius();

  /** get the volume */
  double GetVolume();

  /** calculate the sphere form factor, no scale, no background*/
  void GetFormFactor(IQ * iq);

  /** using a equation to check whether a point with XYZ lies
      within the sphere with center (0,0,0)
  */
  Point3D GetAPoint(double sld);

  /** check whether a point is inside the sphere at any position
      in the 3D space
  */
  bool IsInside(const Point3D& point) const;

  ShapeType GetShapeType() const;

 private:
  double r_;

};

#endif

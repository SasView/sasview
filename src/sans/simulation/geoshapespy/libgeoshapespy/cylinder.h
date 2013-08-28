/** \file cylinder.h class Cylinder:GeoShape */

#ifndef Cylinder_H
#define Cylinder_H

#include "geo_shape.h"

/** class Cylinder, subclass of GeoShape */
class Cylinder : public GeoShape {
 public:

  /** initialize */
  Cylinder();

  /** constructor with radius initialization */
  Cylinder(double radius,double length);

  ~Cylinder();

  /** set parameter radius */
  void SetRadius(double r);

  /** set parameter length */
  void SetLength(double l);

  /** get the radius */
  double GetRadius();
  
  /** get the length */
  double GetLength();

  /** get the radius of the sphere to cover this shape */
  double GetMaxRadius();

  /** get the volume */
  double GetVolume();

  /** calculate the cylinder form factor, no scale, no background*/
  void GetFormFactor(IQ * iq);

  /** using a equation to check whether a point with XYZ lies
      within the cylinder with center (0,0,0)
  */
  Point3D GetAPoint(double sld);

  /** check whether a point is inside the cylinder at any position 
      in the 3D space
  */
  bool IsInside(const Point3D& point) const;

  ShapeType GetShapeType() const;

 protected:
  Point3D GetTopCenter() const;
  Point3D GetBotCenter() const;

 private:
  double r_, l_;
  Point3D topcenter_,botcenter_;

};

#endif

/** \file cylinder.h class Cylinder:GeoShape */

#ifndef Ellipsoid_H
#define Ellipsoid_H

#include "geo_shape.h"

/** class Ellipsoid, subclass of GeoShape */
class Ellipsoid : public GeoShape {
 public:

  /** initialize */
  Ellipsoid();

  /** constructor with radii initialization */
  Ellipsoid(double rx,double ry, double rz);

  ~Ellipsoid();

  /** set parameter radii */
  void SetRadii(double rx, double ry, double rz);

  /** get the radii */
  double GetRadiusX();
  double GetRadiusY();
  double GetRadiusZ();
  
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
  //get a point on three axis for function IsInside,using the edge point
  Point3D GetXaxisPlusEdge() const;
  Point3D GetXaxisMinusEdge() const;
  Point3D GetYaxisPlusEdge() const;
  Point3D GetYaxisMinusEdge() const;
  Point3D GetZaxisPlusEdge() const;
  Point3D GetZaxisMinusEdge() const;

 private:
  double rx_,ry_,rz_;
  Point3D xedge_plus_,xedge_minus_;
  Point3D yedge_plus_,yedge_minus_;
  Point3D zedge_plus_,zedge_minus_;
};

#endif

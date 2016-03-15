/*! \file a abstract class GeoShape 
*/
#ifndef GEOSHAPE_H
#define GEOSHAPE_H

#include "iq.h"
#include "Point3D.h"
#include <vector>

using namespace std;

#define triple(x) ((x) * (x) * (x))
#define square(x) ((x) * (x))

enum ShapeType{ SPHERE, HOLLOWSPHERE, CYLINDER , ELLIPSOID,SINGLEHELIX};

/**
 *  class GeoShape, abstract class, parent class for Sphere, Cylinder ....
 */

class GeoShape{
 public:

  GeoShape(){
    vector<double> init(3,0.0);
    orientation_ = init;
    center_ = init;
  }
  
  virtual ~GeoShape() {}

  /** calculate the form factor for a simple shape */
  virtual void GetFormFactor(IQ * iq) = 0;

  /** Get a point that is within the simple shape*/
  virtual Point3D GetAPoint(double sld) = 0;

  /** check whether a point is inside the shape*/
  virtual bool IsInside(const Point3D& point) const = 0;

  virtual double GetVolume() = 0;

  virtual ShapeType GetShapeType() const = 0;

  /** get the radius of the sphere to cover the shape*/
  virtual double GetMaxRadius() = 0;

  void SetOrientation(double angX, double angY, double angZ);

  void SetCenter(double cenX, double cenY, double cenZ);

  vector<double> GetOrientation() const;

  vector<double> GetCenter() const;

  Point3D GetCenterP() const;

 private:
  vector<double> orientation_;
  
 protected:
  vector<double> center_;
 
};

#endif

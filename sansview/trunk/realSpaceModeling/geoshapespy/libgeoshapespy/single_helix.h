/** \file cylinder.h class Cylinder:GeoShape */

#ifndef SingleHelix_H
#define SingleHelix_H

#include "geo_shape.h"

/** class SingleHelix, subclass of GeoShape */
class SingleHelix : public GeoShape {
 public:

  /** initialize */
  SingleHelix();

  /** constructor with radius initialization */
  SingleHelix(double helix_radius,double tube_radius,double pitch,double turns);

  ~SingleHelix();

  /** set parameter helix_radius */
  void SetHelixRadius(double hr);

  /** set parameter tube_radius */
  void SetTubeRadius(double tr);

  /** set parameter pitch */
  void SetPitch(double pitch);

  /** set parameter number of turns */
  void SetTurns(double turns);

  /** get the helix_radius */
  double GetHelixRadius();

  /** get the tube_radius */
  double GetTubeRadius();
  
  /** get the pitch */
  double GetPitch();

  /** get the number of turns */
  double GetTurns();

  /** get the radius of the sphere to cover this shape */
  double GetMaxRadius();

  /** get the volume */
  double GetVolume();

  /** calculate the single helix form factor, no scale, no background*/
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
  //Point3D GetTopCenter() const;
  //Point3D GetBotCenter() const;

 private:
  double hr_,tr_, pitch_, turns_,zr_;
  Point3D topcenter_,botcenter_;

};

#endif

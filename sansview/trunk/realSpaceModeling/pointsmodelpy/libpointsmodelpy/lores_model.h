/** \file lores_model.h child class of PointsModel*/

#ifndef LORESMODEL_H
#define LORESMODEL_H

#include <deque>
#include "points_model.h"
#include "geo_shape.h"
//temporary
#include <fstream>

/**
 *  Class LORESModel, low resolution models
 */

class LORESModel : public PointsModel {
 private:
  typedef vector<Point3D> PointsVector;

  struct RealSpaceShape {
    GeoShape* shape;
    PointsVector points;

    RealSpaceShape(GeoShape* s = NULL) : shape(s) {
    }

    ~RealSpaceShape() {
      if (shape) delete shape;
    }
  };

  typedef deque<RealSpaceShape*> RealSpaceShapeCollection;

 public:
  LORESModel(double density = 1.0);
  ~LORESModel();

  // Change density
  void SetDensity(double density);
  double GetDensity();

  // Add new shape
  void Add(GeoShape& geo_shape, double sld = 1);

  // Delete ith shape at shapes_
  void Delete(size_t i);

  int GetPoints(Point3DVector &);
  //Write points to a file, mainly for testing right now
  void WritePoints2File(Point3DVector &);

  //get the maximum possible dimension
  double GetDimBound();

  //will be used in determining the maximum distance for
  //P(r) calculation for a complex model (merge several 
  //pointsmodel instance together
  vector<double> GetCenter();

 protected:
  GeoShape* GetGeoShape(GeoShape& geo_shape);
  void FillPoints(RealSpaceShape* real_shape, double sld);
  bool IsInside(const Point3D& point);
  void DistributePoint(const Point3D& point, size_t i);

 private:
  RealSpaceShapeCollection shapes_;
  int npoints_;
  double density_;
  
};

#endif

/** \file complex_model.h child class of PointsModel */

#ifndef COMPLEX_MODEL_H
#define COMPLEX_MODEL_H

#include "points_model.h"
#include <string>
#include <map>

/**
 *  Class ComplexModel : container class for LORESModel & PDBModel
 *  The main functionality is to merge points from instances of 
 *  LORESModel & PDBModel
 */

class ComplexModel : public PointsModel {
 public:
  ComplexModel();
  
  //add PointsModel instance
  void Add(PointsModel *);

  //Parse all coordinates from ATOM section 
  //of the PDB file into vector of points
  int GetPoints(Point3DVector &);

  //Get distance boundary for the pointsmodel instances
  double GetDimBound();

  vector<double> GetCenter();

 private:
  vector<PointsModel *> models_;
};

#endif

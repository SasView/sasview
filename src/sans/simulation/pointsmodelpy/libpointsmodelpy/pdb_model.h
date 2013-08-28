/** \file pdb_model.h child class of PointsModel */

#ifndef PDB_MODEL_H
#define PDB_MODEL_H

#include "points_model.h"
#include <string>
#include <map>

/**
 *  Class PDBModel, PDB models
 */

class PDBModel : public PointsModel {
 public:
  PDBModel();
  
  //add pdb file
  void AddPDB(const string &);
  void AddPDB(const char*);

  //Parse all coordinates from ATOM section 
  //of the PDB file into vector of points
  int GetPoints(Point3DVector &);

  //will be used in determining the maximum distance for
  //P(r) calculation for a complex model (merge several 
  //pointsmodel instance together
  vector<double> GetCenter();

  //get the maximum possible dimension= dist between XYZmax XYZmin
  //May improve to directly get the dimension from unit cell
  //if the technique is crystallography
  double GetDimBound();

 private:
  vector<string> pdbnames_;
  map<string,double> res_sld_;
  double x_max_,x_min_,y_max_,y_min_,z_max_,z_min_;
};

#endif


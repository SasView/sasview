/** \file points_model.h child class of SASmodel*/

#ifndef POINTSMODEL_H
#define POINTSMODEL_H

#include <vector>
#include "tnt/tnt.h"
#include <string>
#include "Point3D.h"
#include "iq.h"
#include "sas_model.h"

using namespace std;

class PointsModel : public SASModel{
 public:
  PointsModel();
  virtual ~PointsModel();

  void CalculateIQ(IQ *iq);
  double CalculateIQ(double q);
  double CalculateIQError(double q);
  
  // Old lengthy 2D simulation (unchecked) 
  void CalculateIQ_2D(IQ *iq,double phi);
  double CalculateIQ_2D(double qx, double qy);
  
  // Fast 2D simulation
  double CalculateIQ_2D(const vector<Point3D>&, double qx, double qy);
  double CalculateIQ_2D_Error(const vector<Point3D>&, double qx, double qy);
  
  //given a set of points, calculate distance correlation
  //function, and return the max dist
  double DistDistribution(const vector<Point3D>&);
  void DistDistributionXY(const vector<Point3D>&);

  Array2D<double> GetPr();
  void OutputPR(const std::string &);
  void OutputPR_XY(const std::string &);

  virtual int GetPoints(Point3DVector &) = 0;
  void OutputPDB(const vector<Point3D>&,const char*);

  //will be used in calculating P(r), the maximum distance
  virtual double GetDimBound() = 0;
  //will be used to determin the maximum distance for
  //several pointsmodel instances
  virtual vector<double> GetCenter();

 protected:
  double CalculateRstep(int num_points, double rmax);
  double rmax_, rstep_,cormax_,cormax_xy_;
  int r_grids_num_;
  vector<double> center_;

 private:
  Array2D<double> pr_,pr_xy_;
  vector<double> product_sld_;
};

#endif

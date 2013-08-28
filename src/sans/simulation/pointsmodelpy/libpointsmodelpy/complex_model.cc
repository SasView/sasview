/** \file complex_model.cc */

#include "complex_model.h"
#include <algorithm>
#include <stdexcept>

using namespace std;

ComplexModel::ComplexModel(){

}

void ComplexModel::Add(PointsModel *pm)
{
  models_.push_back(pm);
}

double ComplexModel::GetDimBound()
{
  //Get the vector of centers of pointsmodel instances
  //and a vector of individual boundary
  vector<PointsModel *>::iterator itr;
  vector<Point3D> veccenter;
  vector<double> bounds;

  for(itr = models_.begin(); itr != models_.end(); ++itr){
    if ((*itr)->GetDimBound() != 0){
      Point3D pp((*itr)->GetCenter()[0],(*itr)->GetCenter()[1],(*itr)->GetCenter()[2]);
      veccenter.push_back(pp);
      bounds.push_back((*itr)->GetDimBound());
    }
  }

  //max bound
  double maxbound = *max_element(bounds.begin(),bounds.end());

  //max distance
  vector<double> vecdist;
  size_t num = veccenter.size();

  if (num > 1){
    for (size_t i = 0; i != num; ++i){
      for (size_t j= 1; j != num; ++j){
        double dist = veccenter[i].distanceToPoint(veccenter[j]);
        vecdist.push_back(dist);
      }
    }
  }
  else{
    vecdist.push_back(maxbound);
  }

  double maxcenterdist = *max_element(vecdist.begin(),vecdist.end());

  double finalbound = maxbound + maxcenterdist;

  return finalbound;
}

vector<double> ComplexModel::GetCenter()
{
  double sumx = 0, sumy = 0, sumz = 0;
  size_t num = 0;

  vector<PointsModel *>::iterator itr;
  for(itr = models_.begin(); itr != models_.end(); ++itr){
    sumx += (*itr)->GetCenter()[0];
    sumy += (*itr)->GetCenter()[1];
    sumz += (*itr)->GetCenter()[2];
    ++num;
  }

  vector<double> v(3);
  v[0] = sumx/num;
  v[1] = sumy/num;
  v[2] = sumz/num;
  center_ = v;
  return center_;
}

int ComplexModel::GetPoints(Point3DVector &vp)
{
  if (vp.size() != 0){
    throw runtime_error("GetPoints(Point3DVector &VP):VP has to be empty"); 
  }

  vector<PointsModel *>::iterator itr;

  for(itr = models_.begin(); itr != models_.end(); ++itr){
    vector<Point3D> temp;
    (*itr)->GetPoints(temp);    	
    if (temp.size() != 0){
      vp.insert(vp.end(),temp.begin(),temp.end());
    }
  }
  return vp.size();
}

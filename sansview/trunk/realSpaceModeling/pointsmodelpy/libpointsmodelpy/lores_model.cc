/** \file lores_model.cc */

#include <algorithm>
#include <stdexcept>
#include "lores_model.h"
#include "sphere.h"
#include "hollow_sphere.h"
#include "cylinder.h"
#include "ellipsoid.h"
#include "single_helix.h"
#include "Point3D.h"

LORESModel::LORESModel(double density)
{
  density_ = density;
}

GeoShape* LORESModel::GetGeoShape(GeoShape& geo_shape)
{
  GeoShape* shape = NULL;

  switch (geo_shape.GetShapeType()){
    case SPHERE:
      shape = new Sphere(static_cast<const Sphere&>(geo_shape));
      break;
    case HOLLOWSPHERE:
      shape = new HollowSphere(static_cast<const HollowSphere&>(geo_shape));
      break;
    case CYLINDER:
      shape = new Cylinder(static_cast<const Cylinder&>(geo_shape));
      break;
    case ELLIPSOID:
      shape = new Ellipsoid(static_cast<const Ellipsoid&>(geo_shape));
      break;
    case SINGLEHELIX:
      shape = new SingleHelix(static_cast<const SingleHelix&>(geo_shape));
      break;
  
  }

  return shape;
}

LORESModel::~LORESModel()
{
  for (RealSpaceShapeCollection::iterator it = shapes_.begin();
       it != shapes_.end(); ++it) {
    delete *it;
  }
}

void LORESModel::SetDensity(double density)
{
  density_ = density;
}

double LORESModel::GetDensity()
{
  return density_;
}

// Add a shape into LORES Model
void LORESModel::Add(GeoShape& geo_shape,
                     double sld) {
  GeoShape* shape = GetGeoShape(geo_shape);
  assert(shape != NULL);

  RealSpaceShape* real_shape = new RealSpaceShape(shape);
  FillPoints(real_shape, sld);
  shapes_.push_back(real_shape);
}

// Delete ith shape in shapes_ list
// If we have 3 shapes in our model, the index starts
// from 0, which means we need to call Delete(0) to delete
// the first shape, and call Delete(1) to delete the second
// shape, etc..
void LORESModel::Delete(size_t i) {
  if (i >= shapes_.size()) {
    std::cerr << "Delete shapes out of scope" << std::endl;
    return;
  }

  RealSpaceShape* real_shape = shapes_[i];
  if (i + 1 < shapes_.size()) {
    // if it is not the last shape, we have to distribute its points
    // to the shapes after i-th shape.
    const Point3DVector& points = real_shape->points;
    for (Point3DVector::const_iterator pit = points.begin();
         pit != points.end(); ++pit)
      DistributePoint(*pit, i + 1);
  }

  shapes_.erase(shapes_.begin() + i);
  delete real_shape;
}

// Get the points in the realspaceshapecollection
int LORESModel::GetPoints(Point3DVector &pp)
{
  if (pp.size() != 0){
    throw runtime_error("GetPoints(Point3DVector &VP):VP has to be empty"); 
  }

  if (shapes_.size() != 0){
    for (size_t j = 0; j <shapes_.size(); ++j ){
      pp.insert(pp.end(),shapes_[j]->points.begin(),shapes_[j]->points.end());
    }
  }
  return pp.size();
}

//Write points to a file, mainly for testing right now
void LORESModel::WritePoints2File(Point3DVector &vp){
  ofstream outfile("test.coor");
  for(size_t i=0; i<vp.size(); ++i){
    outfile<<vp[i].getX()<<" "<<vp[i].getY()<<" "<<vp[i].getZ()<<" "<<vp[i].getSLD()<<endl;
  }
}

double LORESModel::GetDimBound()
{
  if(shapes_.size() == 0)
    return 0;

  //find maximum distance between centers of shapes
  //get the vector of centers
  vector<Point3D> vec_center;
  for (size_t m = 0; m < shapes_.size(); ++m){
    assert(shapes_[m]->shape != NULL);
    vector<double> center(3);
    center = shapes_[m]->shape->GetCenter();
    Point3D p_center;
    p_center.set(center[0],center[1],center[2]);
    vec_center.push_back(p_center);
  }
  size_t vecsize = vec_center.size();

  //get the maximum distance among centers
  double max_cen_dist;
  if (vecsize == 1){
    max_cen_dist = 0;
  }
  else{
    vector<double> vecdist;
    for (size_t m1=0; m1<vecsize -1; ++m1){
      for (size_t m2 = m1+1; m2<vecsize; ++m2){
	double dist = vec_center[m1].distanceToPoint(vec_center[m2]);
	vecdist.push_back(dist);
      }
    }
    max_cen_dist = *max_element(vecdist.begin(), vecdist.end());
  }
  //find the maximum radius for individual shape
  vector<double> maxradii;
  for (size_t n = 0; n < shapes_.size(); ++n){
    assert(shapes_[n]->shape != NULL);
    double maxradius = shapes_[n]->shape->GetMaxRadius();
    maxradii.push_back(maxradius);
  }
  double max_maxradius = *max_element(maxradii.begin(),maxradii.end());
  
  return 2*(max_cen_dist/2 + max_maxradius);
}


// Distribute points of the shape we are going to delete
void LORESModel::DistributePoint(const Point3D& point, size_t i)
{
  for (size_t k = i; k < shapes_.size(); ++k) {
    assert(shapes_[k]->shape != NULL);
    if (shapes_[k]->shape->IsInside(point)) {
      shapes_[k]->points.push_back(point);
      return;
    }
  }
}

void LORESModel::FillPoints(RealSpaceShape* real_shape, double sld)
{
  assert(real_shape != NULL);

  GeoShape* shape = real_shape->shape;
  assert(shape != NULL);

  int npoints = static_cast<int>(density_ * shape->GetVolume());

  for (int i = 0; i < npoints; ++i){
    Point3D apoint = shape->GetAPoint(sld);
    apoint.Transform(shape->GetOrientation(),shape->GetCenter());
    if (!IsInside(apoint)){
      real_shape->points.push_back(apoint);
    }
  }

}

bool LORESModel::IsInside(const Point3D& point)
{
  for (RealSpaceShapeCollection::const_iterator it = shapes_.begin();
       it != shapes_.end(); ++it) {
    const GeoShape* shape = (*it)->shape;
    assert(shape != NULL);

    if (shape->IsInside(point)) {
       return true;
    }
  }

  return false;
}

vector<double> LORESModel::GetCenter()
{
  //get the vector of centers from the list of shapes
  size_t numshapes = 0;
  double sumx = 0, sumy = 0, sumz = 0;
  for (size_t m = 0; m < shapes_.size(); ++m){
    assert(shapes_[m]->shape != NULL);
    vector<double> center(3);
    center = shapes_[m]->shape->GetCenter();

    sumx += center[0];
    sumy += center[1];
    sumz += center[2];

    ++numshapes;
  }

  vector<double> shapescenter(3);
  shapescenter[0]= sumx/numshapes;
  shapescenter[1]= sumy/numshapes;
  shapescenter[2]= sumz/numshapes;

  center_ = shapescenter;
  return center_;
}

/** \file Sphere.cc */
#include <cmath>
#include <cassert>
#include "sphere.h"
#include "myutil.h"

Sphere::Sphere()
{
  r_ = 0;
}

Sphere::Sphere(double radius)
{
  r_ = radius;
}

Sphere::~Sphere()
{
}

void Sphere::SetRadius(double r)
{
  r_ = r;
}

double Sphere::GetRadius()
{
  return r_;
}

double Sphere::GetMaxRadius()
{
  double maxr = r_;
  return maxr;
}

ShapeType Sphere::GetShapeType() const
{
  return SPHERE;
}

double Sphere::GetVolume()
{
  double V = 4 * pi / 3 * triple(r_);
  return V;
}

void Sphere::GetFormFactor(IQ * iq)
{
  /** number of I for output, equal to the number of rows of array IQ*/
  int numI = iq->iq_data.dim1();
  double qmin = iq->GetQmin();
  double qmax = iq->GetQmax();

  assert(numI > 0);
  assert(qmin > 0);
  assert(qmax > 0);
  assert( qmax > qmin );
  
  double logMin = log10(qmin);
  double z = logMin;
  double logMax = log10(qmax);
  double delta = (logMax - logMin) / (numI-1);

  for(int i = 0; i < numI; ++i) {

    /** temp for Q*/
    double q = pow(z, 10);
 
    double bes = 3.0 * (sin(q*r_) - q*r_*cos(q*r_)) / triple(q) / triple(r_);

    /** double f is the temp for I, should be equal to one when q is 0*/
    double f = bes * bes;

    /** IQ[i][0] is Q,Q starts from qmin (non zero),q=0 handle separately IQ[i][1] is IQ*/
    iq->iq_data[i][0]= q;
    iq->iq_data[i][1]= f;

    z += delta;
  }  
}

Point3D Sphere::GetAPoint(double sld)
{
  static int max_try = 100;
  for (int i = 0; i < max_try; ++i) {
    double x = (ran1()-0.5) * 2 * r_;
    double y = (ran1()-0.5) * 2 * r_;	
    double z = (ran1()-0.5) * 2 * r_;

    Point3D apoint(x,y,z,sld);
    if (apoint.distanceToPoint(Point3D(0,0,0)) <=r_ ) //dist to origin give sphere shape
      return apoint;
  }

  std::cerr << "Max try "
            << max_try
            << " is reached while generating a point in sphere" << std::endl;
  return Point3D(0, 0, 0);
}

bool Sphere::IsInside(const Point3D& point) const
{
  return point.distanceToPoint(Point3D(center_[0], center_[1], center_[2])) <= r_;
  cout << "distance = " << point.distanceToPoint(Point3D(center_[0], center_[1], center_[2])) << endl;
}

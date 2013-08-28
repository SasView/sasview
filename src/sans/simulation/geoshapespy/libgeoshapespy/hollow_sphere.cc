/** \file hollowsphere.cc  */
#include <cmath>
#include <cassert>
#include "hollow_sphere.h"

HollowSphere::HollowSphere()
{
  ro_ = 0;
  th_ = 0;
}

HollowSphere::HollowSphere(double radius, double thickness)
{
  ro_ = radius;
  th_ = thickness;
}

double HollowSphere::GetMaxRadius()
{
  double maxr = ro_;
  return maxr;
}

void HollowSphere::GetFormFactor(IQ * iq)
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

  //not finished yet, need to find the part which is equal to 1
  for(int i = 0; i < numI; ++i) {

    /** temp for Q*/
    double q = pow(z,10);

    double ri_ = ro_ - th_ ;

    double bes1 = 3.0 * (sin(q*ri_) - q*ri_*cos(q*ri_)) / triple(q) / triple(ri_);
    double bes2 = 3.0 * (sin(q*ro_) - q*ro_*cos(q*ro_)) / triple(q) / triple(ro_);
    double bes = (triple(ro_)*bes1 - triple(ri_)*bes2)/(triple(ro_) - triple(ri_));
    /** double f is the temp for I, should be equal to one when q is 0*/
    double f = bes * bes;

    /** IQ[i][0] is Q,Q starts from qmin (non zero),q=0 handle separately IQ[i][1] is I */
    iq->iq_data[i][0]= q;
    iq->iq_data[i][1]= f;

    z += delta;
  }

}

Point3D HollowSphere::GetAPoint(double sld)
{
  return Point3D(0,0,0);
}

double HollowSphere::GetVolume()
{
  return 0;
}

bool HollowSphere::IsInside(const Point3D& point) const
{
  return true;
}

ShapeType HollowSphere::GetShapeType() const
{
  return HOLLOWSPHERE;
}


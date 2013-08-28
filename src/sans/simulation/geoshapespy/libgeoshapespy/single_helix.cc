/** \file SingleHelix.cc */
#include <cmath>
#include <cassert>
#include "single_helix.h"
#include "myutil.h"

SingleHelix::SingleHelix()
{
  hr_ = 0;
  tr_ = 0;
  pitch_ = 0;
  turns_ = 0;
}

SingleHelix::SingleHelix(double helix_radius,double tube_radius,double pitch,double turns)
{
  hr_ = helix_radius;
  tr_ = tube_radius;
  pitch_ = pitch;
  turns_ =  turns;
}

SingleHelix::~SingleHelix()
{
}

void SingleHelix::SetHelixRadius(double hr)
{
  hr_ = hr;
}

void SingleHelix::SetTubeRadius(double tr)
{
  tr_ = tr;
}

void SingleHelix::SetPitch(double pitch)
{
  pitch_ = pitch;
}

void SingleHelix::SetTurns(double turns)
{
  turns_ = turns;
}

double SingleHelix::GetHelixRadius()
{
  return hr_;
}

double SingleHelix::GetTubeRadius()
{
  return tr_;
}

double SingleHelix::GetPitch()
{
  return pitch_;
}

double SingleHelix::GetTurns()
{
  return turns_;
}

double SingleHelix::GetMaxRadius()
{
  // put helix into a cylinder
  double r_ = hr_ + tr_;
  double l_ = pitch_*turns_ + 2*tr_;
  double maxr = sqrt(4*r_*r_ + l_*l_)/2;
  return maxr;
}

ShapeType SingleHelix::GetShapeType() const
{
  return SINGLEHELIX;
}

double SingleHelix::GetVolume()
{
  double V = pi*square(tr_)*sqrt(square(2*pi*hr_)+square(turns_*pitch_));
  return V;
}

void SingleHelix::GetFormFactor(IQ * iq)
{
  /** number of I for output, equal to the number of rows of array IQ*/
  /** to be finished */
}

Point3D SingleHelix::GetAPoint(double sld)
{
  int max_try = 100;
  int i = 0;
  double point1 = 0, point2 = 0, point3 = 0;
 
  do{
    i++;
    if (i > max_try)
	break;
    zr_ = tr_*sqrt(1+square((pitch_/(2*pi*hr_))));
    point1 = (ran1()-0.5)*2*tr_;
    point2 = (ran1()-0.5)*2*zr_;
    point3 = (ran1()-0.5)*4*pi*turns_;
  } while (((square(point1/hr_)+square(point2/zr_))>1) || (point2+pitch_*point3/(2*pi)<0));

  double x = (point1 + hr_)*cos(point3);
  double y = (point1 + hr_)*sin(point3);
  //"-pitch_*turns_/2" is just to corretly center the helix
  double z = point2 + pitch_*point3/(2*pi)-pitch_*turns_/2;

  Point3D apoint(x,y,z,sld);
  return apoint;

  
  std::cerr << "Max try "
            << max_try
            << " is reached while generating a point in cylinder" << std::endl;
  
  return Point3D(0,0,0);
}

bool SingleHelix::IsInside(const Point3D& point) const
{
  double x = point.getX()-center_[0];
  double y = point.getY()-center_[1];
  double z = point.getZ()-center_[2];

  double p3 = atan(y/x);
  double p2 = z-(pitch_*p3)/(2*pi);
  double p1 = x/cos(p3)-hr_;

  if ((square(p1/tr_)+square(p2/zr_))>1 || p2+pitch_*p3/(2*pi))
    return false;
  else
    return true;
}


#include "transformation.h"
#include <math.h>
#include <stdexcept>

void RotateX(const double ang_x,Point3D &a_point)
{
  double sinA_ = sin(ang_x);
  double cosA_ = cos(ang_x);
  double pointX_ = a_point.getX();
  double pointY_ = a_point.getY();
  double pointZ_ = a_point.getZ();

  double x_new_ = pointX_;
  double y_new_ = pointY_*cosA_ - pointZ_*sinA_;
  double z_new_ = pointY_*sinA_ - pointZ_*cosA_;

  a_point.set(x_new_, y_new_, z_new_);
}

void RotateY(const double ang_y,Point3D &a_point)
{
  double sinA_ = sin(ang_y);
  double cosA_ = cos(ang_y);
  double pointX_ = a_point.getX();
  double pointY_ = a_point.getY();
  double pointZ_ = a_point.getZ();

  double x_new_ = pointX_*cosA_ + pointZ_*sinA_;
  double y_new_ = pointY_;
  double z_new_ = -pointX_*sinA_ + pointZ_*cosA_;

  a_point.set(x_new_, y_new_, z_new_);
}

void RotateZ(const double ang_z,Point3D &a_point)
{
  double sinA_= sin(ang_z);
  double cosA_ = cos(ang_z);
  double pointX_ = a_point.getX();
  double pointY_ = a_point.getY();
  double pointZ_ = a_point.getZ();

  double x_new_ = pointX_*cosA_ - pointY_*sinA_;
  double y_new_ = pointX_*sinA_+ pointY_*cosA_;
  double z_new_ = pointZ_;

  a_point.set(x_new_, y_new_, z_new_);
}

void Translate(const double trans_x, const double trans_y, const double trans_z, Point3D &a_point)
{
  double x_new_ = a_point.getX() + trans_x;
  double y_new_ = a_point.getY() + trans_y;
  double z_new_ = a_point.getZ() + trans_z;

  a_point.set(x_new_, y_new_, z_new_);
}

void RotateMatrix(const vector<double> &rotmatrix, Point3D &a_point)
{
  if (rotmatrix.size() != 9)
    throw std::runtime_error("The size for rotation matrix vector has to be 9.");

  double xold = a_point.getX();
  double yold = a_point.getY();
  double zold = a_point.getZ();

  double x_new_ = rotmatrix[0]*xold + rotmatrix[1]*yold + rotmatrix[2]*zold;
  double y_new_ = rotmatrix[3]*xold + rotmatrix[4]*yold + rotmatrix[5]*zold;
  double z_new_ = rotmatrix[6]*xold + rotmatrix[7]*yold + rotmatrix[8]*zold;

  a_point.set(x_new_, y_new_, z_new_);
}

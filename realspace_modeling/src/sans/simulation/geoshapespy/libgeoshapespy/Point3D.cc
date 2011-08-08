//Point3D.cpp  

#include <cmath>
#include <cstdlib>
#include <stdexcept>
#include "Point3D.h"

using namespace std;

Point3D::Point3D(double a, double b, double c, double sld)
{
  x = a;
  y = b;
  z = c;
  sld_ =  sld;
}

ostream& operator<< (ostream& os, const Point3D& p)
{
  os << "(" << p.getX() << ", " << p.getY() << ", " << p.getZ() << "," << p.getSLD() << ")";

  return os;
}

double Point3D::distanceToPoint(const Point3D &p) const
{
	double dx=x-p.x;
	double dy=y-p.y;
	double dz=z-p.z;
	return sqrt(dx*dx+dy*dy+dz*dz);
}

double Point3D::distanceToLine(const Point3D &p1, const Point3D &p2, bool * pIsOutside /* 0 */) const
{
	double u = ((x-p1.x)*(p2.x-p1.x) + (y-p1.y)*(p2.y-p1.y) + (z-p1.z)*(p2.z-p1.z))/(p1.distanceToPoint(p2)*p1.distanceToPoint(p2));
	
	if(pIsOutside != 0) {
		if ( u < 0 || u > 1)
			*pIsOutside=true;
		else 
			*pIsOutside=false;
	}

	double interX=p1.x+u*(p2.x-p1.x);
	double interY=p1.y+u*(p2.y-p1.y);
	double interZ=p1.z+u*(p2.z-p1.z);
	
	return sqrt((x-interX)*(x-interX)+(y-interY)*(y-interY)+(z-interZ)*(z-interZ));
}

// p1 and p2 determine a line, they are two end points
Point3D Point3D::getInterPoint(const Point3D &p1, const Point3D &p2, bool * pIsOutside /* 0 */) const
{
	double u = ((x-p1.x)*(p2.x-p1.x) + (y-p1.y)*(p2.y-p1.y) + (z-p1.z)*(p2.z-p1.z))/(p1.distanceToPoint(p2)*p1.distanceToPoint(p2));
	
	if(pIsOutside != 0) {

		if ( u < 0 || u > 1)
			*pIsOutside=true;
		else 
			*pIsOutside=false;
	}

	return Point3D(p1.x+u*(p2.x-p1.x), p1.y+u*(p2.y-p1.y), p1.z+u*(p2.z-p1.z));
}

void Point3D::set(double x1, double y1, double z1)
{
	x = x1;
	y = y1;
	z = z1;
}

double Point3D::norm() const
{
	return sqrt(x * x + y * y + z * z);
}

double Point3D::normalize()
{
	double v = norm();
	
	if(v != 0) {
		x /= v;
		y /= v;
		z /= v;
	}
	
	return v;
}

Point3D Point3D::normVector() const
{
	Point3D p;	
	double v = norm();
	
	if(v != 0) {
		p.x = x / v;
		p.y = y / v;
		p.z = z / v;
	}

	return p;
}

double Point3D::dotProduct(const Point3D &p) const
{
	return x * p.x + y * p.y + z * p.z;
}

Point3D Point3D::minus(const Point3D &p) const
{
	return Point3D(x - p.x, y - p.y, z - p.z);
}

Point3D Point3D::plus(const Point3D &p) const
{
	return Point3D(x + p.x, y + p.y, z + p.z);
}

Point3D& Point3D::operator=(const Point3D &p)
{
	x = p.x;
	y = p.y;
	z = p.z;
	sld_ = p.sld_;

	return *this;
}

void Point3D::scale(double s)
{
	x *= s;
	y *= s;
	z *= s;
}

Point3D Point3D::multiplyProduct(const Point3D &p)
{
	return Point3D(y * p.z - z * p.y, z * p.x - x * p.z, x * p.y - y * p.x);
}

void Point3D::Transform(const vector<double> &orien, const vector<double> &center){
  if(orien[1]) RotateY(Degree2Radian(orien[1]));
  if(orien[0]) RotateX(Degree2Radian(orien[0]));
  if(orien[2]) RotateZ(Degree2Radian(orien[2]));

  Translate(center[0],center[1],center[2]);
}

void Point3D::RotateX(const double ang_x)
{
  double sinA_ = sin(ang_x);
  double cosA_ = cos(ang_x);

  //x doesn't change;
  double y_new= y*cosA_ - z*sinA_;
  double z_new= y*sinA_ + z*cosA_;

  y = y_new;
  z = z_new;
}

void Point3D::RotateY(const double ang_y)
{
  double sinA_ = sin(ang_y);
  double cosA_ = cos(ang_y);
 
  double x_new = z*sinA_ + x*cosA_;
  //y doesn't change
  double z_new = z*cosA_ - x*sinA_;

  x = x_new;
  z = z_new;
}

void Point3D::RotateZ(const double ang_z)
{
  double sinA_ = sin(ang_z);
  double cosA_ = cos(ang_z);

  double x_new = x*cosA_ - y*sinA_;
  double y_new = x*sinA_ + y*cosA_;
  //z doesn't change

  x = x_new;
  y = y_new;
}

void Point3D::Translate(const double trans_x, const double trans_y, const double trans_z)
{
  double x_new = x + trans_x;
  double y_new = y + trans_y;
  double z_new = z + trans_z;

  x = x_new;
  y = y_new;
  z = z_new;
}

double Point3D::Degree2Radian(const double degree)
{
  return degree/180*pi;
}

void Point3D::TransformMatrix(const vector<double> &rotmatrix, const vector<double> &center)
{
  if (rotmatrix.size() != 9 || center.size() != 3)
    throw std::runtime_error("The size for rotation matrix vector has to be 9.");

  double xold = x;
  double yold = y;
  double zold = z;

  x = rotmatrix[0]*xold + rotmatrix[1]*yold + rotmatrix[2]*zold;
  y = rotmatrix[3]*xold + rotmatrix[4]*yold + rotmatrix[5]*zold;
  z = rotmatrix[6]*xold + rotmatrix[7]*yold + rotmatrix[8]*zold;

  Translate(center[0],center[1],center[2]);
}

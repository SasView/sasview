//class point3D    1/29/2004 Jing
//properties: copy point coordinates
//	      calculate point to point distance 
//	      shortest distance from a point to a line 


#ifndef __POINT3D_
#define __POINT3D_

#include <iostream>
#include <vector>

using namespace std;

const double pi = 3.1415926;

class Point3D
{
  public:
        Point3D() {}

	//assign values with SLD to a point
	Point3D(double a, double b, double c, double sld = 0);

	// output
	friend std::ostream& operator<<(std::ostream&, const Point3D&);

	//distance to a point
  	double distanceToPoint(const Point3D &p) const;
  	
  	//distance to a line
  	double distanceToLine(const Point3D &p1, const Point3D &p2, bool *pv = 0) const; 

	// get the point lying on the axis from a point
	Point3D getInterPoint(const Point3D &p1, const Point3D &p2, bool *pv = 0) const;

	// normalization
	Point3D normVector() const;

	// get length
	double norm() const;
	
	double normalize();
	
	// assignment operator
	Point3D& operator=(const Point3D &p);
	
	// scale this point with s
	void scale(double s);
	
	// multiplication product of two vectors
	Point3D multiplyProduct(const Point3D &p);

	// p0 - p
	Point3D minus(const Point3D &p) const;

	// p0 + p
	Point3D plus(const Point3D &p) const;

	// dot product
	double dotProduct(const Point3D &p) const;

	//if you do not care if the point falls into the range of line,you can directly use distanceToLine(p1,p2)
	void set(double x1, double y1, double z1);

	double getX() const { return x; }
	double getY() const { return y; }
	double getZ() const { return z; }
	double getSLD() const { return sld_; }

        //Transformation
        void Transform(const vector<double> &orien, const vector<double> &center);
        void TransformMatrix(const vector<double> &rotmatrix, const vector<double> &center);
  private:
  	double x, y, z;
	double sld_;

        void RotateX(const double ang_x);
        void RotateY(const double ang_y);
        void RotateZ(const double ang_z);
        void Translate(const double trans_x, const double trans_y, const double trans_z);
        double Degree2Radian(const double degree);
};

typedef std::vector<Point3D> Point3DVector;

#endif

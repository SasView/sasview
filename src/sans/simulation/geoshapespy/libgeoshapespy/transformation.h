/** \file transformation.h: a few functions to do the transformation */

#ifndef TRANSFORMATION_H
//Transform operation on a Point3D
//Not in use, similar transformation are implemented as Point3D class functions

#define TRANSFORMATION_H

#include <vector>
#include "Point3D.h"

void RotateX(const double ang_x,Point3D &);
void RotateY(const double ang_y,Point3D &);
void RotateZ(const double ang_z,Point3D &);
void Translate(const double trans_x, const double trans_y, const double trans_z, Point3D &);

//rotate a point by given a rotation 3X3 matrix
//vec[0]=R00, vec[1]=R01.......vec[8]=R22
void RotateMatrix(const vector<double> &, Point3D &);

#endif

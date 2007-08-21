#include <iostream>
#include <vector>
#include "Point3D.h"


using namespace std;

int main(){

  cout << "test 1:initialize a point, set orientation, set center"
       << " and perform transform" <<endl;
  Point3D apoint(3,4,5);

  vector<double> orient(3),center(3);
  for (int i = 0; i!=3; ++i){
    center[i] = 0;
  }
  orient[0]=10;
  orient[1]=0;
  orient[2]=30;

  apoint.Transform(orient,center);

  cout << apoint.getX() <<" "<<apoint.getY()<<" "<<apoint.getZ()<<endl;
  cout << orient[0] <<" "<<orient[1]<<" "<<orient[2]<<endl;

  cout << "test 2: initialize a point, and perform transformation \n"
       << "through a rotation matrix and a translation" <<endl;

  vector<double> rotmatrix(9,1);
  for (size_t i = 0; i != rotmatrix.size(); ++i){
    cout << rotmatrix[i] <<" ";
  }

  Point3D pp(1,1,1);
  pp.TransformMatrix(rotmatrix, center);

  cout << pp.getX() <<" "<<pp.getY()<<" "<<pp.getZ()<<endl;
  return 0;
}

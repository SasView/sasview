#include "sphere.h"
#include <iostream>

int main(){
  Sphere sph1(10);
  sph1.SetOrientation(10,20,30);
  sph1.SetCenter(1,5,10);

  vector<double> v1 = sph1.GetOrientation();
  cout << v1[0] <<endl;

  return 0;
}

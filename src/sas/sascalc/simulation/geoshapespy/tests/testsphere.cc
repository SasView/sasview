#include <cassert>
#include <iostream>
#include "sphere.h"
#include "iq.h"

using namespace std;

void TestGetAnalyticalIQ() {
  Sphere sphere(1.0);

  IQ iq1(10,0.001, 0.3);
  sphere.GetFormFactor(&iq1);

  for (int i = 0; i< iq1.iq_data.dim1(); i++)
    cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][1] <<endl;
}

void TestGetShapeType() {
  Sphere sphere;
  assert(sphere.GetShapeType() == SPHERE);
}

void TestGetVolume() {
  Sphere s(1);
  cout << "volume is " << s.GetVolume();
}

int main(){
  TestGetAnalyticalIQ();
  TestGetShapeType();
  TestGetVolume();

  printf("PASS.\n");

  return 0;
}

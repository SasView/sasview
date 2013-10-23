#include <cassert>
#include <iostream>
#include "analytical_model.h"
#include "sphere.h"

using namespace std;

void TestAnalyticalModel() {
  Sphere sphere(1.0);
  AnalyticalModel am(sphere);

  IQ iq1(10,0.001, 0.3);
  am.CalculateIQ(&iq1);

  for (int i = 0; i < iq1.iq_data.dim1(); ++i)
    cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][1] <<endl;  
}

int main(){
  TestAnalyticalModel();
  printf("PASS.\n");
}

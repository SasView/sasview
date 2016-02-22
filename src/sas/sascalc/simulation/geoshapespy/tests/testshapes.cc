#include <cassert>
#include <iostream>
#include <vector>
#include "sphere.h"
#include "cylinder.h"
#include "hollow_sphere.h"
#include "ellipsoid.h"
#include "single_helix.h"
#include "iq.h"

using namespace std;

void TestGetFormFactor_sphere() {
  Sphere sphere(1.0);

  IQ iq1(10,0.001, 0.3);
  sphere.GetFormFactor(&iq1);

  for (int i = 0; i< iq1.iq_data.dim1(); i++)
    cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][1] <<endl;
}

void TestGetShapeType_sphere() {
  Sphere sphere;
  //if (assert(sphere.GetShapeType() == SPHERE))
  //  cout << " it is a sphere" << endl;
  cout << sphere.GetShapeType() << endl;
}

void TestGetShapeType(GeoShape &gs){
  cout <<gs.GetShapeType() << endl;
}

void TestGetVolume_sphere() {
  Sphere s(1);
  cout << "volume is " << s.GetVolume();
}

void TestGetAPoint_sphere(){
  Sphere asphere(10);
  cout << asphere.GetAPoint(1) << endl;
}

void TestGetFormFactor_HS(){

  HollowSphere hs(10, 2);

  IQ iq1(10, 0.001, 0.3);
  hs.GetFormFactor(&iq1);

  for (int i = 0; i< iq1.iq_data.dim1(); i++)
    cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][1] <<endl;


}

void TestGetShapeType_HS(){
  HollowSphere hs1;
  assert(hs1.GetShapeType() == HOLLOWSPHERE);
}

void TestIsInside_sphere(){
  cout << "Testing IsInside(): ";
  Sphere s1(10);
  Point3D pp(20,30,30);
  Point3D pp2(1,1,1);

  cout << s1.IsInside(pp) <<" " << s1.IsInside(pp2) << " ";
  cout << "Finished testing IsInside()" <<endl;
}

void TestCylinder(){
  Cylinder c1(10,20);
  Point3D p1 = c1.GetAPoint(1);
  Point3D p4 = c1.GetAPoint(1);
  cout << "Got two points inside the cylinder" << endl;
  cout << "the distance is: " << p1.distanceToPoint(p4);
  cout << p1 << endl;
  cout << "is this point inside?:" << c1.IsInside(p1) << endl;
  
  Point3D p2(20,20,20);
  cout << "this point should be outside:" << c1.IsInside(p2) <<endl;

  c1.SetOrientation(10,10,10);
  c1.SetCenter(20,20,20);

  vector<double> ori;
  ori.push_back(10);
  ori.push_back(10);
  ori.push_back(20);

  vector<double> cen;
  cen.push_back(20);
  cen.push_back(20);
  cen.push_back(20);

  p1.Transform(ori,cen);
  cout << "is the p1 still inside after orientation?" << c1.IsInside(p1) << endl;
  cout << "p1 p2 distance: " <<p1.distanceToPoint(p4) << endl;

  Point3D p3(0,0,0);
  cout <<" this origin point should be outside after transformation:" << c1.IsInside(p3) <<endl;

  Point3D pp1(6.8,-2.11,11);
  cout <<"is pp1 inside? "<< c1.IsInside(pp1) << endl;

}

void TestEllipsoid(){
  Ellipsoid e1(5,10,15);
  cout << "generated an ellipsoid:"<<e1.GetRadiusX()<<" ";
  cout <<e1.GetRadiusY()<<" " << e1.GetRadiusZ() << endl;
  cout << "maximum radius is: " << e1.GetMaxRadius() << endl;
  cout << "volume is : " << e1.GetVolume() << endl;
  cout << "Get a point: " << e1.GetAPoint(1.0) << endl;

  Point3D p1(1,2,3);
  Point3D p2(6,11,16);
  Point3D p3(100,100,100);
  cout <<"is " << p1 << " inside? " << e1.IsInside(p1) << endl;
  cout <<"is " << p2 << " inside? " << e1.IsInside(p2) << endl;

  e1.SetCenter(10,10,10);
  Point3D p4(11,12,13);
  cout <<"is " << p2 << " inside after moved? " << e1.IsInside(p2) << endl;

  e1.SetOrientation(90,90,90);
  cout <<"is " << p3 << " inside after rotated? " << e1.IsInside(p3) << endl;

}

void TestSingleHelix(){

  cout <<" Testing single helix" << endl;
  SingleHelix sh(10,3,30,1);
  cout << "Get a point" << sh.GetAPoint(1.0) << endl;  

  Point3D p1(1,1,-50); //cannot be in sh(10,3,30,1)
  cout <<"is " << p1 <<" inside?" << sh.IsInside(p1)<< endl;
  Point3D p2(-3.15922, -11.6193, 20.5302); //should be inside
  cout <<"is " << p2 <<" inside?" << sh.IsInside(p2)<< endl;

}

int main(){
 
  //cout << "testing sphere :\n" ;
  //TestGetAPoint_sphere();
  //TestGetShapeType_sphere();
  //testing getting shape type from parent
  //Sphere ss(1);
  //TestGetShapeType(ss);
  //TestGetVolume_sphere();
  //TestIsInside_sphere();

  //cout << "testing hollowsphere: \n" ;	
  //TestGetFormFactor_HS();
  //TestGetShapeType_HS();
  //  TestGetVolume();
  
  //cout << "testing cylinder:\n";
  //TestCylinder();
  
  //cout << "testing ellipsoid :\n";
  //TestEllipsoid();

  TestSingleHelix();
  printf("PASS.\n");

  return 0;
}

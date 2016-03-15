#include <cstdlib>
#include <iostream>
#include <fstream>
#include <vector>
#include "lores_model.h"
#include "sphere.h"
#include "cylinder.h"
#include "ellipsoid.h"
#include "Point3D.h"

using namespace std;

void test_calculateIQ(LORESModel &lm);

void WritePointsCoor(vector<Point3D> &vp){
  ofstream outfile("testcc.coor");
  for(size_t i=0; i<vp.size(); ++i){
    outfile<<vp[i].getX()<<" "<<vp[i].getY()<<" "<<vp[i].getZ()<<" "<<1.0<<endl;
  }
}

void test_lores(){

  LORESModel lm(0.5);
  cout << "density is:" << lm.GetDensity() << endl;
   
  Sphere s1(10);
  s1.SetOrientation(10,10,20);
  s1.SetCenter(10,10,10);
  lm.Add(s1,1.0);
   
  Cylinder c1(5,20);
  c1.SetCenter(0,0,0);
  c1.SetOrientation(10,20,30);
  lm.Add(c1,1.0);
  
  /*
  Cylinder c2(40,100);
  c2.SetCenter(-30,-40,-35);
  lm.Add(c2,1.0);
  */
  /*
  Ellipsoid e1(20,15,10);
  e1.SetCenter(0,0,0);
  e1.SetOrientation(10,10,20);
  lm.Add(e1,1.0);
  */
  /*test multiple spheres
  int range = 20;
  int r = 5;
  for (int k = 0; k < 1000; ++k) {
    Sphere s(r + rand() % r);
    s.SetCenter(rand() % range, rand() % range, rand() % range);
    lm.Add(s, 1.0);
  }
  */
  /*
  Sphere s1(10);
  cout << "sphere information:" << s1.GetVolume() << " " << s1.GetRadius() <<endl;
  s1.SetOrientation(10,20,10);
  s1.SetCenter(1,5,2);
  lm.Add(s1,1.0); 

  Sphere s2(15);
  s2.SetCenter(20,20,20);
  lm.Add(s2,2.0);

  Sphere s3(5);
  s3.SetCenter(0,0,0);
  lm.Add(s3,2.0);

  Sphere s4(5);
  s4.SetCenter(0,0,10);
  lm.Add(s4,2.0);

  Sphere s5(10);
  s5.SetCenter(20,0,0);
  lm.Add(s5,2.0);
  */

  test_calculateIQ(lm);
}

void test_calculateIQ(LORESModel &lm){

  IQ iq1(10,0.001,0.3);
  cout << "iq information:" << iq1.GetQmin() <<endl;

  vector<Point3D> vp;
  lm.GetPoints(vp);
  WritePointsCoor(vp);
  cout << "vp size:" <<vp.size()<<endl;
  cout << "save into pdb file" << endl;
  lm.OutputPDB(vp,"model.pdb");

  //  for (vector<Point3D>::iterator iter = vp.begin(); 
  //     iter != vp.end(); ++iter){
  //  cout << *iter << endl;
  //}

  lm.DistDistribution(vp);
  Array2D<double> pr(lm.GetPr());
  //for(int i = 0; i< pr.dim1(); ++i)
  //  cout << pr[i][0] << " " << pr[i][1] << " " << pr[i][2] << endl;
  lm.OutputPR("test.pr");
  cout << "pass ddfunction, and print out the pr file" <<endl;

  lm.CalculateIQ(&iq1); 
  cout <<"I(Q): \n" ;
  //for (int i = 0; i< iq1.iq_data.dim1(); i++)
  //  cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][1] <<endl;
}

void test_lores2d(){

  LORESModel lm(0.1);

  Cylinder c1(5,20);
  c1.SetCenter(0,0,0);
  c1.SetOrientation(10,20,30);
  lm.Add(c1,1.0);

  vector<Point3D> vp;
  lm.GetPoints(vp);

  lm.DistDistributionXY(vp);
  lm.OutputPR_XY("test2d.pr");

  IQ iq(10,0.001,0.3);
  lm.CalculateIQ_2D(&iq,10);

  iq.OutputIQ("test2d.iq");
}

void test_lores2d_qxqy(){

  LORESModel lm(0.1);

  Cylinder c1(5,20);
  c1.SetCenter(0,0,0);
  c1.SetOrientation(10,20,30);
  lm.Add(c1,1.0);

  vector<Point3D> vp;
  lm.GetPoints(vp);

  lm.DistDistributionXY(vp);  

  double aI = lm.CalculateIQ_2D(0.1,0.2);

  cout << " a single I is: "<<aI<<" at Qx,Qy = 0.1,0.2" <<endl;
}

void test_GetCenter()
{
  LORESModel lm(0.1);

  Sphere s1(10);
  s1.SetCenter(-1,-1,-1);
  Sphere s2(20);
  s2.SetCenter(1,1,1);

  lm.Add(s1,1.0);
  lm.Add(s2,1.0);

  vector<double> center(3);
  center = lm.GetCenter();

  cout << "center should be (0,0,0) after adding two spheres:"<<endl;
  cout << center[0] <<" "<< center[1] <<" "<< center[2]<<endl;

}

void test_CalSingleI(){
  LORESModel lm(0.1);

  Cylinder cyn(10,40);  

  lm.Add(cyn,1.0);

  vector<Point3D> vp;
  lm.GetPoints(vp);

  lm.DistDistribution(vp);

  double result = lm.CalculateIQ(0.1);
  cout << "The I(0.1) is: " << result << endl;      
}

int main(){

  printf("this\n");
  cout << "Start" << endl;
  //test_lores();
  cout <<"testing DistDistributionXY"<<endl;
  test_lores2d();

  cout <<"testing GetCenter (center of the list of shapes)"<<endl;
  test_GetCenter();

  cout <<"testing calculate_2d(Qx,Qy)"<<endl;
  test_lores2d_qxqy();
  cout << "Pass" << endl;

  cout <<"testing CalculateIQ(q)"<<endl;
  test_CalSingleI();

  return 0;
}

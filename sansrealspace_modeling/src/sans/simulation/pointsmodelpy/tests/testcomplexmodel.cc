#include "complex_model.h"
#include "lores_model.h"
#include "sphere.h"
#include "pdb_model.h"
#include <vector>
#include "Point3D.h"
#include <string>

int main(){

  //Get a few points from a lores model
  vector<Point3D> vplores;
  LORESModel lm(0.1);
  Sphere s1(10);
  lm.Add(s1,1);
  lm.GetPoints(vplores);
  
  //get a few points from a pdb model
  vector<Point3D> vppdb;
  string pdbfile("ff0.pdb");
  PDBModel p1;
  p1.AddPDB(pdbfile);
  p1.GetPoints(vppdb);
  //should be error,argument vector has to be empty
  //p1.GetPoints(vppdb);

  //merge points
  vector<Point3D> vptotal;
  ComplexModel cm;
  cm.Add(&lm);
  cm.Add(&p1);
  cout << "boundary"<< cm.GetDimBound() <<endl;

  cm.GetPoints(vptotal);

  cm.DistDistribution(vptotal);
  cm.OutputPR("testcomplexcc.pr");
  //pm.AddPoints(vptotal,vplores,vppdb);

  return 0;
}

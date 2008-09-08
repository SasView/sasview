#include "pdb_model.h"
#include "Point3D.h"
#include <vector>
#include <string>
#include "iq.h"

typedef vector<Point3D> PointsVector;

int main(){

  //Test PDB with adding one normal pdb file
  PointsVector vp;
  IQ iq(100,0.001,0.3);

  string name("test.pdb");

  //initialize a PDBModel with a pdb file name
  PDBModel mpdb;
  mpdb.AddPDB(name);
  //parse coordinates in pdb file into a vector
  //of points
  mpdb.GetPoints(vp);
  //output the vector of points into a pseudo pdb
  //file, for testing only
  mpdb.OutputPDB(vp,"testpdb.pdb");
  mpdb.DistDistribution(vp);
  mpdb.OutputPR("test.pr");
  mpdb.CalculateIQ(&iq);
  iq.OutputIQ("test.iq");
  cout << "check test.pr and test.iq files" <<endl;


  //second test: add second pdb file
  vector<Point3D> vp2;
  string second("test2.pdb");
  mpdb.AddPDB(second);
  mpdb.GetPoints(vp2);
  mpdb.OutputPDB(vp2,"testpdb2.pdb");
  cout <<"check whether testpdb2.pdb has 12 points" <<endl;

  return 0;
}

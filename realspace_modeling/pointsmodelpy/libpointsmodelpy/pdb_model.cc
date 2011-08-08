/** \file pdb_model.cc */

#include "pdb_model.h"
#include <fstream>
#include <string>
#include <cstdlib>
#include <cmath>
#include <stdexcept>

using namespace std;

typedef map<string,double>::const_iterator mymapitr;

PDBModel::PDBModel(){
  res_sld_["ALA"] = 1.645;  res_sld_["ARG"] = 3.466;
  res_sld_["ASN"] = 3.456;  res_sld_["ASP"] = 3.845;
  res_sld_["CYS"] = 1.930;  res_sld_["GLU"] = 3.762;
  res_sld_["GLN"] = 3.373;  res_sld_["GLY"] = 1.728;
  res_sld_["HIS"] = 4.959;  res_sld_["LLE"] = 1.396;
  res_sld_["LEU"] = 1.396;  res_sld_["LYS"] = 1.586;
  res_sld_["MET"] = 1.763;  res_sld_["PHE"] = 4.139;
  res_sld_["PRO"] = 2.227;  res_sld_["SER"] = 2.225;
  res_sld_["THR"] = 2.142;  res_sld_["TRP"] = 6.035;
  res_sld_["TYR"] = 4.719;  res_sld_["VAL"] = 1.479;

  x_max_ = -10000; x_min_ = 10000;
  y_max_ = -10000; y_min_ = 10000;
  z_max_ = -10000; z_min_ = 10000;
}

void PDBModel::AddPDB(const string &pdbfile)
{
  pdbnames_.push_back(pdbfile);
}

void PDBModel::AddPDB(const char* pdbfile)
{
  string sname(pdbfile);
  pdbnames_.push_back(sname);
}

int PDBModel::GetPoints(Point3DVector &vp)
{
  if (vp.size() != 0){
    throw runtime_error("PDBModel::GetPoints(Point3DVector &VP):VP has to be empty"); 
  }
  vector<string>::iterator itr;
  for (itr = pdbnames_.begin(); itr!=pdbnames_.end(); ++itr){
    ifstream infile(itr->c_str());
    if (!infile){
      cerr << "error: unable to open input file: " 
	   << infile << endl;
    }
    string line;
    while (getline(infile,line)){
      size_t len = line.size();
      string header;
      
      //for a line with size >=4, retrieve the header
      //if the header == "ATOM""
      //make sure the length of the line >=54, then
      //retrieve the corresponding coordinates,convert str to double
      //then assign them to a point3d,which will be append to vp with a SLD
      if (len >= 4){
	for (size_t i=0; i !=4; ++i) header += line[i];
	if (header.compare("ATOM") == 0 && len >53){
	  string strx,stry,strz;
	  double x = 0, y = 0, z = 0;
	  for (size_t j = 30; j!=38; ++j){
	    strx += line[j];
	    stry += line[j+8];
	    strz += line[j+16];
	  }
	  x = atof(strx.c_str());
	  y = atof(stry.c_str());
	  z = atof(strz.c_str());
	  
	  //find residue type, and assign SLD
	  string resname;
	  for (size_t k = 17; k!=20; ++k) resname +=line[k];
	  mymapitr itr = res_sld_.find("ALA");
	  
	  //apoint(x,y,z,sld)
	  Point3D apoint(x,y,z,itr->second);
	  vp.push_back(apoint);
	  
	  //save x y z' max & min to calculate the size boundary
	  x_max_ = x > x_max_ ? x : x_max_;
	  x_min_ = x < x_min_ ? x : x_min_;
	  y_max_ = y > y_max_ ? y : y_max_;
	  y_min_ = y < y_min_ ? y : y_min_;
	  z_max_ = z > z_max_ ? z : z_max_;
	  z_min_ = z < z_min_ ? z : z_min_;
	}
      }
    }

    infile.close();
  }
  return vp.size();
}

double PDBModel::GetDimBound()
{
  if (pdbnames_.size() == 0 )
    return 0;

  //cout <<x_max_<<" "<<x_min_<<" "<<y_max_<<" "<<y_min_<<" "<<z_max_<<" "<<z_min_<<endl;
  double size = sqrt((x_max_-x_min_)*(x_max_-x_min_)+(y_max_-y_min_)*(y_max_-y_min_)+(z_max_-z_min_)*(z_max_-z_min_));
  return size;
}

vector<double> PDBModel::GetCenter()
{

  vector<double> cen(3);
  cen[0]= (x_max_+x_min_)/2;
  cen[1]= (y_max_+y_min_)/2;
  cen[2]= (z_max_+z_min_)/2;
  center_ = cen;

  return center_;
}

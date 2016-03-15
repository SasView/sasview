/** \file points_model.cc */

#include <vector>
#include <algorithm>
#include <fstream>
#include <stdio.h>
//#include <exception>
#include <stdexcept>
#include "points_model.h"
#include "Point3D.h"

PointsModel::PointsModel()
{
  r_grids_num_ = 2000;
  rmax_ = 0;
  cormax_ = 0;
  rstep_ = 0;
}

void PointsModel::CalculateIQ(IQ *iq)
{
  //fourier transform of the returned Array2D<double> from ddFunction()
  int nIpoints = iq->GetNumI();
  double qstep = (iq->GetQmax()) / (nIpoints-1);
  vector<double> fint(nIpoints, 0);

  //I(0) is calculated seperately
  int num_rstep = pr_.dim1();

  for (int k = 1; k<nIpoints; k++){

    double q = k * qstep;

    double r =0;
    double debeye = 0;
    double fadd =0;


    for (int i = 1; i < num_rstep; ++i){
      r = i*rstep_;  //r should start from 1* rstep
      double qr = q*r;
      debeye = sin(qr)/qr;
      fadd = pr_[i][1]*debeye;
      fint[k] = fint[k] + fadd;
    }
  }

  //I(0)
  double Izero = 0;
  for (int i = 0; i < num_rstep; ++i)
    Izero += pr_[i][1];
  fint[0] = Izero;

  //assign I(Q) with normalization
  for(int j = 0; j < nIpoints; ++j){
    (*iq).iq_data[j][0] = j * qstep;
    (*iq).iq_data[j][1] = fint[j];
    // remove normalization Izero;
  }
}

//return I with a single q value
double PointsModel::CalculateIQ(double q)
{
  //fourier transform of the returned Array2D<double> from ddFunction()
  int num_rstep = pr_.dim1();

  double r =0;
  double debeye = 0;
  double fadd = 0;
  double Irelative = 0;

  //I(0) is calculated seperately
  if (q == 0){
    //I(0)
    double Izero = 0;
    for (int i = 0; i < num_rstep; ++i)
      Izero += pr_[i][1];
    Irelative = Izero;
  }
  else {
    for (int i = 1; i < num_rstep; ++i){
      r = i*rstep_;  //r should start from 1* rstep
      double qr = q*r;
      debeye = sin(qr)/qr;
      fadd = pr_[i][1]*debeye;
      Irelative = Irelative + fadd;
    }
  }
  return Irelative;
}

double PointsModel::CalculateIQError(double q)
{
  //fourier transform of the returned Array2D<double> from ddFunction()
  int num_rstep = pr_.dim1();

  double r =0;
  double debeye = 0;
  double fadd = 0;
  double Irelative = 0;

  //I(0) is calculated seperately
  for (int i = 1; i < num_rstep; ++i){
	  r = i*rstep_;  //r should start from 1* rstep
	  double qr = q*r;
	  debeye = sin(qr)/qr;
	  fadd = fabs(pr_[i][2])*debeye*debeye 
	  	+ rstep_*rstep_/4.0/r/r*(cos(qr)*cos(qr) + debeye*debeye);
	  Irelative = Irelative + fadd;
  }
  return sqrt(Irelative);
}

//pass in a vector of points, and calculate the P(r)
double PointsModel::DistDistribution(const vector<Point3D> &vp)
{
  //get r axis:0,rstep,2rstep,3rstep......d_bound
  int sizeofpr = r_grids_num_ + 1; //+1 just for overflow prevention

  double d_bound = GetDimBound();
  rstep_ = CalculateRstep(r_grids_num_,d_bound);

  Array2D<double> pr(sizeofpr, 3); //third column is left for error for the future
  pr = 0;

  for (int i = 1; i != sizeofpr; ++i)
    pr[i][0] = pr[i-1][0] + rstep_ ;  //column 1:  distance

  int size = vp.size();

  for (int i1 = 0; i1 < size - 1; ++i1) {
    for (int i2 = i1 + 1; i2 < size; ++i2) {
      //dist_.push_back(vp[i1].distanceToPoint(vp[i2]));
      //product_sld_.push_back(vp[i1].getSLD() * vp[i2].getSLD());
      double a_dist = vp[i1].distanceToPoint(vp[i2]);
      double its_sld = vp[i1].getSLD() * vp[i2].getSLD();

      //save maximum distance
      if (a_dist>rmax_) {
        rmax_ = a_dist;
      }
      //insert into pr array
      int l = int(floor(a_dist/rstep_));

      //cout << "i1,i2,l,a_dist"<<vp[i1]<<" "<<vp[i2]<<" "<<l<<" "<<a_dist<<endl;     
      //overflow check
      if (l >= sizeofpr) {
        cerr << "one distance is out of range: " << l <<endl;
        //throw "Out of range";
      }
      else {
        pr[l][1] += its_sld;  //column 2 intermediate: sum of SLD of the points with specific distance     
        // Estimate uncertainty (squared)
        pr[l][2] += its_sld*its_sld; 
        //keep maxium Pr absolute number, in order to normalize
        //if (pr[l][1] > cormax_)	  cormax_ = pr[l][1];
      }
    }
  }
  
  //normalize Pr
  for (int j = 0; j != sizeofpr; ++j){           //final column2 for P(r)
    //pr[j][1] = pr[j][1]/cormax_;

    // 'Size' is the number of space points, without double counting (excluding 
    // overlapping regions between shapes). The volume of the combined shape
    // is given by  V = size * (sum of all sub-volumes) / (Total number of points) 
    //              V = size / (lores_density)
    
    // - To transform the integral to a sum, we need to give a weight
    // to each entry equal to the average space volume of a point (w = V/N = 1/lores_density).
    // The final output, I(q), should therefore be multiplied by V*V/N*N.
    // Since we will be interested in P(r)/V, we only need to multiply by 1/N*(V/N) = 1/N/lores_density.
    // We don't have access to lores_density from this class; we will therefore apply
    // this correction externally.
    //
    // - Since the loop goes through half the points, multiply by 2.
    // TODO: have access to lores_density from this class.
    // 
    pr[j][1] = 2.0*pr[j][1]/size;
    pr[j][2] = 4.0*pr[j][2]/size/size;
  }
  pr_ = pr;

  return rmax_;
}

Array2D<double> PointsModel::GetPr()
{
  return pr_;
}


double PointsModel::CalculateRstep(int num_grids, double rmax)
{
  assert(num_grids > 0);

  double rstep;
  rstep = rmax / num_grids;

  return rstep;
}

void PointsModel::OutputPR(const string &fpr){
  ofstream outfile(fpr.c_str());
  if (!outfile) {
    cerr << "error: unable to open output file: "
	 << outfile << endl;
    exit(1);
  }
  
  double sum = 0.0;
  double r_stepsize = 1.0;
  if (pr_.dim1()>2) r_stepsize = pr_[1][0] - pr_[0][0];
  
  for (int i = 0;  i < pr_.dim1(); ++i){
	  sum += pr_[i][1]*r_stepsize;
  }
  
  for (int i = 0;  i < pr_.dim1(); ++i){
	  if (pr_[i][1]==0) continue;
	  outfile << pr_[i][0] << "       " << (pr_[i][1]/sum) << endl;
  }
}

void PointsModel::OutputPDB(const vector<Point3D> &vp,const char *fpr){
  FILE *outfile=NULL;
  outfile = fopen(fpr,"w+");
  if (!outfile) {
    cerr << "error: unable to open output file: "
	 << outfile << endl;
    exit(1);
  }
  int size = vp.size();
  int index = 0;
  for (int i = 0;  i < size; ++i){
    ++index;
    fprintf(outfile,"ATOM%7d  C%24.3lf%8.3lf%8.3lf%6.3lf\n", \
           index,vp[i].getX(),vp[i].getY(),vp[i].getZ(),vp[i].getSLD());
  }
  fclose(outfile);
}

PointsModel::~PointsModel()
{
}

void PointsModel::DistDistributionXY(const vector<Point3D> &vp)
{
  //the max box get from 3D should be more than enough for 2D,but doesn't hurt
  double d_bound = GetDimBound();

  //using 1A for rstep, so the total bins is the max distance for the object
  int sizeofpr = ceil(d_bound) + 1; //+1 just for overflow prevention
  rstep_ = 1;

  Array2D<double> pr_xy(sizeofpr,sizeofpr); //2D histogram

  //the max frequency in the correlation histogram
  double cormax_xy_ = 0;

  //initialization
  pr_xy = 0;

  for (int i = 1; i != sizeofpr; ++i){
    pr_xy[i][0] = pr_xy[i-1][0] + rstep_ ;  //column 1:  distance
  }

  int size = vp.size();

  for (int i1 = 0; i1 < size - 1; ++i1) {
    for (int i2 = i1 + 1; i2 < size; ++i2) {
      int jx = int(floor(fabs(vp[i1].getX()-vp[i2].getX())/rstep_));
      int jy = int(floor(fabs(vp[i1].getY()-vp[i2].getY())/rstep_));
      //the sld for the pair of points
      double its_sld = vp[i1].getSLD()*vp[i2].getSLD();

      //overflow check
      if ((jx >= sizeofpr) || (jy >= sizeofpr))
      {
        cerr << "one distance is out of range: " <<endl;
        //throw "Out of range";
      }
      else{
	pr_xy[jx][jy] += its_sld;
        if (pr_xy[jx][jy] > cormax_xy_ ) cormax_xy_ = pr_xy[jx][jy];
      }
    }
  }

  //normalize Pr_xy
  for (int m = 0; m != sizeofpr; ++m){           //final column2 for P(r)
    for (int n = 0; n != sizeofpr; ++n){
      pr_xy[m][n] = pr_xy[m][n]/cormax_xy_;
      //cout << "m n:"<<m<<" "<<n<<" "<<pr_xy[m][n]<<endl;
    }
  }

  pr_xy_ = pr_xy;
}

void PointsModel::OutputPR_XY(const std::string &fpr)
{
  ofstream outfile(fpr.c_str());
  if (!outfile) {
    cerr << "error: unable to open output file: "
	 << outfile << endl;
    exit(1);
  }
  int size = pr_xy_.dim1();
  //pr_xy_ is a N x N array
  for (int i = 0;  i != size; ++i){
    for (int j = 0; j != size; ++j)
    {
      outfile << i << "    " << j <<"    "<< pr_xy_[i][j] << endl;
    }
  }
}

void PointsModel::CalculateIQ_2D(IQ *iq,double phi)
{
  int nIpoints = iq->GetNumI();
  double qstep = (iq->GetQmax()) / (nIpoints-1);
  vector<double> fint(nIpoints, 0);
  double Izero = 0;

  //number of bins on x and y axis
  int size_r = pr_xy_.dim1();
  //rstep is set to one, otherwise should be cos(phi)*rstep
  double cosphi = cos(phi);
  double sinphi = sin(phi);

  for(int k = 1; k != nIpoints; ++k){
    double q = k * qstep;
    double tmp = cos(q*(cosphi+sinphi));

    for(int i=0; i!=size_r; ++i){
      for(int j = 0; j!=size_r; ++j){
        fint[k] += pr_xy_[i][j]*tmp;
      }
    }
  }

  for(int i=0; i!=size_r; ++i){
    for(int j = 0; j!=size_r; ++j){
      Izero += pr_xy_[i][j];
    }
  }
  fint[0] = Izero;

  //assign I(Q) with normalization
  for(int j = 0; j < nIpoints; ++j){
    (*iq).iq_data[j][0] = j * qstep;
    (*iq).iq_data[j][1] = fint[j] / Izero;
  }
}

vector<double> PointsModel::GetCenter()
{
  vector<double> vp(3,0);
  return vp;
}

double PointsModel::CalculateIQ_2D(double qx, double qy)
{
  //for each (Qx,Qy) on 2D detector, calculate I
  double q = sqrt(qx*qx+qy*qy);
  double I = 0;

  double cosphi = qx/q;
  double sinphi = qy/q;
  double tmp = cos(q*(cosphi+sinphi));

  //loop through P(r) on xy plane
  int size_r = pr_xy_.dim1();
  for(int i=-size_r+1; i!=size_r; ++i){
    for(int j = -size_r+1; j!=size_r; ++j){
      //rstep is set to one, left out from calculation
      I += pr_xy_[abs(i)][abs(j)]*cos(q*(cosphi*i+sinphi*j));
    }
  }

  //return I, without normalization
  return I;
}

/*
 * 2D simulation for oriented systems
 * The beam direction is assumed to be in the z direction.
 * 
 * @param points: vector of space points
 * @param qx: qx [A-1]
 * @param qy: qy [A-1]
 * @return: I(qx, qy) for the system described by the space points [cm-1]
 * 
 */
double PointsModel::CalculateIQ_2D(const vector<Point3D>&points, double qx, double qy){
	/*
	 * TODO: the vector of points should really be part of the class
	 * 	     This is a design flaw inherited from the original programmer.
	 */
	
	int size = points.size();

	double cos_term = 0;
	double sin_term = 0;
	for (int i = 0; i < size; i++) {
	  	//the sld for the pair of points
	
		double phase = qx*points[i].getX() + qy*points[i].getY();
			  	
		cos_term += cos(phase) * points[i].getSLD();
		sin_term += sin(phase) * points[i].getSLD();
	
	}   			

	// P(q) = 1/V I(q) = (V/N)^2 (1/V) (cos_term^2 + sin_term^2) 
	// We divide by N here and we will multiply by the density later.

	return (cos_term*cos_term + sin_term*sin_term)/size;	
}

double PointsModel::CalculateIQ_2D_Error(const vector<Point3D>&points, double qx, double qy){
	
	int size = points.size();

	double delta_x, delta_y;
	double q_t2 = qx*qx + qy*qy;
	double cos_term = 0;
	double sin_term = 0;
	double cos_err = 0;
	double sin_err = 0;
	
	// Estimate the error on the position of each point
	// in x or y as V^(1/3)/N
	
	for (int i = 0; i < size; i++) {
		
		
		//the sld for the pair of points
	
		double phase = qx*points[i].getX() + qy*points[i].getY();
		double sld_fac = points[i].getSLD() * points[i].getSLD();
		
		cos_term += cos(phase) * points[i].getSLD();
		sin_term += sin(phase) * points[i].getSLD();

		sin_err += cos(phase) * cos(phase) * sld_fac;
		cos_err += sin(phase) * sin(phase) * sld_fac;
	
	}   			

	// P(q) = 1/V I(q) = (V/N)^2 (1/V) (cos_term^2 + sin_term^2) 
	// We divide by N here and we will multiply by the density later.

	// We will need to multiply this error by V^(1/3)/N.
	// We don't have access to V from within this class.
	return 2*sqrt(cos_term*cos_term*cos_err*cos_err + sin_term*sin_term*sin_err*sin_err)/size;	
}


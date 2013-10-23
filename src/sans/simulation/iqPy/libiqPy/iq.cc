/** \file iq.cc */

#include "iq.h"
#include <fstream>
#include <iostream>

using namespace std;

IQ::IQ(int numI){

  numI_ = numI;

  Array2D<double> iq1(numI, 2, 0.0);

  iq_data = iq1;
}

IQ::IQ(int numI,double qmin, double qmax){

  numI_ = numI;
  qmin_ = qmin;
  qmax_ = qmax;

  Array2D<double> iq1(numI, 2, 0.0);

  iq_data = iq1;
}

void IQ::SetQmin(double qmin){
  qmin_ = qmin;

}

void IQ::SetQmax(double qmax){
  qmax_ = qmax;
}

void IQ::SetContrast(double delrho){
  delrho_ = delrho;
}

void IQ::SetVolFrac(double vol_frac){
  vol_frac_ = vol_frac;
}

double IQ::GetQmin(){
  return qmin_;
}

double IQ::GetQmax(){
  return qmax_;
}

double IQ::GetContrast(){
  return delrho_;
}

double IQ::GetVolFrac(){
  return vol_frac_;
}

int IQ::GetNumI(){
  return numI_;
}

void IQ::OutputIQ(string fiq){
  ofstream outfile(fiq.c_str());
  if (!outfile) {
    cerr << "error: unable to open output file: "
	 << outfile << endl;
    exit(1);
  }
  for (int i = 0;  i < iq_data.dim1(); ++i){
    outfile << iq_data[i][0] << "       " << iq_data[i][1] << endl;
  }
    //    fprintf(fp,"%15lf%15lf%15lf\n", (j+1)*rstep, cor[j]/cormax, "0");



}

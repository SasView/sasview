#include "iq.h"
#include <iostream>

using namespace std;

int main(){

  cout << " Generating a empty iq 2D array with size of 10"  << endl;
	IQ iq1(10);

	for (int i = 0; i< iq1.iq_data.dim1(); i++)
		cout << iq1.iq_data[i][0]<< " " << iq1.iq_data[i][0] <<endl;

	int dim = iq1.iq_data.dim1();

	cout << "dimension of the iq array is : " << dim << endl;

	iq1.SetQmin(0.001);
	iq1.SetQmax(0.4);
	iq1.SetContrast(1.0);
	iq1.SetVolFrac(1.0);

	cout << iq1.GetQmin() << " " << iq1.GetQmax() << " " << iq1.GetContrast() << " " << iq1.GetVolFrac() << endl;

	cout << "generating another empty iq object through constructor IQ(numI,qmin,qmax)" <<endl;
	
	IQ iq2(15,0.001,0.4);

	iq2.OutputIQ("out.iq");

	cout << "pass." << endl;

	return 0;
}

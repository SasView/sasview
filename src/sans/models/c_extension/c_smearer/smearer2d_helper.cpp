/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2009, University of Tennessee
 */
#include "smearer2d_helper.hh"
#include <stdio.h>
#include <math.h>
using namespace std;

/**
 * Constructor for BaseSmearer
 *
 * binning
 * @param qx: array of Qx values
 * @param qy: array of Qy values
 * @param nrbins: number of r bins
 * @param nphibins: number of phi bins
 */
Smearer_helper :: Smearer_helper(int npoints, double* qx, double* qy,
		double* dqx, double* dqy, double rlimit, int nrbins, int nphibins) {
	// Number of bins
	this->npoints = npoints;
	this->rlimit = rlimit;
	this->nrbins = nrbins;
	this->nphibins = nphibins;
	this->qx_values = qx;
	this->qy_values = qy;
	this->dqx_values = dqx;
	this->dqy_values = dqy;
};

/**
 * Compute the point smearing matrix
 */
void Smearer_helper :: smear2d(double *weights, double *qx_out, double *qy_out){

	double rbin_size = rlimit / double(nrbins);
	double phibin_size = 0.0;
	double rbin = 0.0;
	double phibin = 0.0;
	double qr = 0.0;
	double qphi = 0.0;
	double Pi = 4.0*atan(1.0);
	
	// Loop over q-values and multiply apply matrix
	for(int i=0; i<nrbins; i++){
		rbin = rbin_size * (double(i) + 0.5);
		for(int j=0; j<nphibins; j++){
			phibin_size =  2.0 * Pi / double(nphibins);
			phibin = phibin_size * (double(j));
			for(int q_i=0; q_i<npoints; q_i++){
				qr = sqrt(qx_values[q_i]*qx_values[q_i] + qy_values[q_i]*qy_values[q_i]);
				qphi = atan(qy_values[q_i]/qx_values[q_i]);
				qx_out[q_i + npoints*(nrbins * j + i)] = (rbin*dqx_values[q_i]*cos(phibin) + qr)*cos(qphi)-
										rbin*dqy_values[q_i]*sin(phibin)*sin(qphi);
				qy_out[q_i + npoints*(nrbins * j + i)] = (rbin*dqx_values[q_i]*cos(phibin) + qr)*sin(qphi)+
										rbin*dqy_values[q_i]*sin(phibin)*cos(qphi);
				if (q_i==0){
					weights[nrbins * j + i] = exp(-0.5 * ((rbin - rbin_size / 2.0) *
							(rbin - rbin_size / 2.0)))- exp(-0.5 * ((rbin + rbin_size / 2.0 ) *
									(rbin + rbin_size / 2.0)));
			}
		}
	}
	}
}


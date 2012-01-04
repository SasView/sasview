/**
	This software was developed by the University of Tennessee as part of the
	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
	project funded by the US National Science Foundation.

	If you use DANSE applications to do scientific research that leads to
	publication, we ask that you acknowledge the use of the software with the
	following sentence:

	"This work benefited from DANSE software developed under NSF award DMR-0520547."

	copyright 2008, University of Tennessee
 */
#ifndef DISP_VISIT_H
#define DISP_VISIT_H

class DispersionVisitor {
public:
	void dispersion_to_dict(void *, void *);
	void gaussian_to_dict(void *, void *);
	void rectangle_to_dict(void *, void *);
	void lognormal_to_dict(void *, void *);
	void schulz_to_dict(void*, void *);
	void array_to_dict(void *, void *);

	void dispersion_from_dict(void*, void *);
	void gaussian_from_dict(void*, void *);
	void rectangle_from_dict(void*, void *);
	void lognormal_from_dict(void*, void *);
	void schulz_from_dict(void*, void *);
	void array_from_dict(void*, void *);

};


#endif

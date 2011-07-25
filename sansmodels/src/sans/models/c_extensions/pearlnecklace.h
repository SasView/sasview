#if !defined(o_h)
#define pearl_necklace_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = PearlNecklaceModel
 //[DISP_PARAMS] = radius, edge_separation
 //[DESCRIPTION] =<text>Calculate form factor for Pearl Necklace Model
//				[Macromol. Symp. 2004, 211, 25-42]
 //				Parameters:
 //				background:background
 //				scale: scale factor
 //				sld_pearl: the SLD of the pearl spheres
 //	            sld_string: the SLD of the strings
 //				sld_solv: the SLD of the solvent
 //				num_pearls: number of the pearls
 //				radius: the radius of a pearl
 //				edge_separation: the length of sring segment; surface to surface
 //				thick_string: thickness (ie, diameter) of the string
 //		</text>
 //[FIXED]=  <text>radius.width; edge_separation.width</text>
 //[NON_FITTABLE_PARAMS]= <text></text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
	double scale;
    ///	radius [A]
    //  [DEFAULT]=radius=80.0 [A]
	double radius;
	///	edge_separation
	//  [DEFAULT]=edge_separation= 350 [A]
	double edge_separation;
	///	thick_string [A]
	//  [DEFAULT]=thick_string= 2.5 [A]
	double thick_string;
	///	num_pearls
	//  [DEFAULT]=num_pearls= 3
	double num_pearls;
	///	sld_pearl
	//  [DEFAULT]=sld_pearl= 1.0e-06 [1/A^(2)]
	double sld_pearl;
	///	sld_string
	//  [DEFAULT]=sld_string= 1.0e-06 [1/A^(2)]
	double sld_string;
	///	sld_solv
	//  [DEFAULT]=sld_solv= 6.3e-06 [1/A^(2)]
	double sld_solv;
	/// Background
	//  [DEFAULT]=background=0
	double background;

}PeralNecklaceParameters;

double pearl_necklace_kernel(double dq[], double q);

/// 1D scattering function
double pearl_necklace_analytical_1D(PeralNecklaceParameters *pars, double q);

/// 2D scattering function
double pearl_necklace_analytical_2D(PeralNecklaceParameters *pars, double q, double phi);
double pearl_necklace_analytical_2DXY(PeralNecklaceParameters *pars, double qx, double qy);

#endif

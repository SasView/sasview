#if !defined(o_h)
#define rpa_h

/**
 * Structure definition for sphere parameters
 */
 //[PYTHONCLASS] = RPAModel
 //[DISP_PARAMS] = background
 //[DESCRIPTION] =<text>  THIS FORMALISM APPLIES TO MULTICOMPONENT POLYMER MIXTURES IN THE
 //							HOMOGENEOUS (MIXED) PHASE REGION ONLY.;
 //							CASE 0: C/D BINARY MIXTURE OF HOMOPOLYMERS
 //							CASE 1: C-D DIBLOCK COPOLYMER
 //							CASE 2: B/C/D TERNARY MIXTURE OF HOMOPOLYMERS
 //							CASE 3: B/C-D MIXTURE OF HOMOPOLYMER B AND
 //								DIBLOCK COPOLYMER C-D
 //							CASE 4: B-C-D TRIBLOCK COPOLYMER
 //							CASE 5: A/B/C/D QUATERNARY MIXTURE OF HOMOPOLYMERS
 //							CASE 6: A/B/C-D MIXTURE OF TWO HOMOPOLYMERS A/B
 //								AND A DIBLOCK C-D
 //							CASE 7: A/B-C-D MIXTURE OF A HOMOPOLYMER A AND A
 //								TRIBLOCK B-C-D
 //							CASE 8: A-B/C-D MIXTURE OF TWO DIBLOCK COPOLYMERS
 //								A-B AND C-D
 //							CASE 9: A-B-C-D FOUR-BLOCK COPOLYMER
 //							See details in the model function help
 //		</text>
 //[FIXED]=  <text></text>
 //[NON_FITTABLE_PARAMS]= <text> lcase_n; Na; Phia; va; La; Nb; Phib; vb; Lb;Nc; Phic; vc; Lc;Nd; Phid; vd; Ld; </text>
 //[ORIENTATION_PARAMS]= <text> </text>

typedef struct {
	/// The Case number
	//  [DEFAULT]=lcase_n=0
	int lcase_n;

    /// Segment Length ba
    //  [DEFAULT]=ba= 5.0
	double ba;
	/// Segment Length bb
    //  [DEFAULT]=bb=5.0
	double bb;
	/// Segment Length bc
	//  [DEFAULT]=bc= 5.0
	double bc;
	/// Segment Length bd
	//  [DEFAULT]=bd= 5.0
	double bd;

	/// Chi Param ab
	//  [DEFAULT]=Kab=-0.0004
	double Kab;
	/// Chi Param ac
	//  [DEFAULT]=Kac=-0.0004
    double Kac;
    /// Chi Param ad
    //  [DEFAULT]=Kad=-0.0004
    double Kad;
    /// Chi Param bc
    //  [DEFAULT]=Kbc=-0.0004
    double Kbc;
    /// Chi Param bd
    //  [DEFAULT]=Kbd=-0.0004
    double Kbd;
    /// Chi Param cd
    //  [DEFAULT]=Kcd=-0.0004
    double Kcd;

    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
    double background;

    /// Degree OF POLYMERIZATION of a
    //  [DEFAULT]=Na=1000.0
    double Na;
    /// Volume Fraction of a
    //  [DEFAULT]=Phia=0.25
    double Phia;
    /// Specific Volume of a
    //  [DEFAULT]=va=100.0
    double va;
    /// Scattering Length of a
    //  [DEFAULT]=La=1.0e-012
    double La;

    /// Degree OF POLYMERIZATION of b
    //  [DEFAULT]=Nb=1000.0
    double Nb;
    /// Volume Fraction of b
    //  [DEFAULT]=Phib=0.25
    double Phib;
    /// Specific Volume of b
    //  [DEFAULT]=vb=100.0
    double vb;
    /// Scattering Length of b
    //  [DEFAULT]=Lb=1.0e-012
    double Lb;

    /// Degree OF POLYMERIZATION of c
    //  [DEFAULT]=Nc=1000.0
    double Nc;
    /// Volume Fraction of c
    //  [DEFAULT]=Phic=0.25
    double Phic;
    /// Specific Volume of c
    //  [DEFAULT]=vc=100.0
    double vc;
    /// Scattering Length of c
    //  [DEFAULT]=Lc=1.0e-012
    double Lc;

    /// Degree OF POLYMERIZATION of d
    //  [DEFAULT]=Nd=1000.0
    double Nd;
    /// Volume Fraction of d
    //  [DEFAULT]=Phid=0.25
    double Phid;
    /// Specific Volume of d
    //  [DEFAULT]=vd=100.0
    double vd;
    /// Scattering Length of d
    //  [DEFAULT]=Ld=0.0e-012
    double Ld;

} RPAParameters;

double rpa_kernel(double dq[], double q);

/// 1D scattering function
double rpa_analytical_1D(RPAParameters *pars, double q);

/// 2D scattering function
double rpa_analytical_2D(RPAParameters *pars, double q, double phi);
double rpa_analytical_2DXY(RPAParameters *pars, double qx, double qy);

#endif

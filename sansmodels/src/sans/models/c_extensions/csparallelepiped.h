/*
	TODO: Add 2D model
*/

#if !defined(csparallelepiped_h)
#define csparallelepiped_h
/** Structure definition for CSParallelepiped parameters
 * [PYTHONCLASS] = CSParallelepipedModel
 * [DISP_PARAMS] = shortA, midB, longC,parallel_phi,parallel_psi, parallel_theta
   [DESCRIPTION] = <text> Form factor for a rectangular Shell. Below are the Parameters.
		scale: scale factor
		shortA: length of short edge  [A]
		midB: length of another short edge [A]
		longC: length of long edge  of the parallelepiped [A]
		rimA: length of short edge  [A]
		rimB: length of another short edge [A]
		rimC: length of long edge  of the parallelepiped [A]
		sld_rimA: sld of rimA [1/A^(2)]
		sld_rimB: sld of rimB [1/A^(2)]
		sld_rimC: sld of rimC [1/A^(2)]
		sld_core: Pipe_sld [1/A^(2)]
		sld_solv: solvent_sld [1/A^(2)]
		background: incoherent Background [1/cm]
		</text>
	[FIXED]= <text>shortA.width; midB.width; longC.width;parallel_phi.width;parallel_psi.width; parallel_theta.width</text>
	[ORIENTATION_PARAMS]= <text>parallel_phi;parallel_psi; parallel_theta; parallel_phi.width;parallel_psi.width; parallel_theta.width</text>


 **/
typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale=1.0
    double scale;
    ///  Length of short edge of the parallelepiped [A]
    //  [DEFAULT]=shortA=35 [A]
    double shortA;
	/// Length of mid edge of the parallelepiped [A]
    //  [DEFAULT]=midB=75 [A]
    double midB;
	/// Length of long edge of the parallelepiped [A]
    //  [DEFAULT]=longC=400 [A]
    double longC;
    ///  Thickness of rimA [A]
    //  [DEFAULT]=rimA=10 [A]
    double rimA;
	/// Thickness of rimB [A] [A]
    //  [DEFAULT]=rimB=10 [A]
    double rimB;
	/// Thickness of rimC [A] [A]
    //  [DEFAULT]=rimC=10 [A]
    double rimC;
    /// SLD_rimA [1/A^(2)]
    //  [DEFAULT]=sld_rimA=2e-6 [1/A^(2)]
    double sld_rimA;
    /// SLD_rimB [1/A^(2)]
    //  [DEFAULT]=sld_rimB=4e-6 [1/A^(2)]
    double sld_rimB;
    /// SLD_rimC [1/A^(2)]
    //  [DEFAULT]=sld_rimC=2e-6 [1/A^(2)]
    double sld_rimC;
    /// SLD_pcore [1/A^(2)]
    //  [DEFAULT]=sld_pcore=1e-6 [1/A^(2)]
    double sld_pcore;
    /// sld_solv [1/A^(2)]
    //  [DEFAULT]=sld_solv=6e-6 [1/A^(2)]
    double sld_solv;
	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.06 [1/cm]
	double background;
    /// Orientation of the parallelepiped axis w/respect incoming beam [rad]
    //  [DEFAULT]=parallel_theta=0.0 [rad]
    double parallel_theta;
    /// Orientation of the longitudinal axis of the parallelepiped in the plane of the detector [rad]
    //  [DEFAULT]=parallel_phi=0.0 [rad]
    double parallel_phi;
    /// Orientation of the cross-sectional minor axis of the parallelepiped in the plane of the detector [rad]
    //  [DEFAULT]=parallel_psi=0.0 [rad]
    double parallel_psi;


} CSParallelepipedParameters;



/// 1D scattering function
double csparallelepiped_analytical_1D(CSParallelepipedParameters *pars, double q);

/// 2D scattering function
double csparallelepiped_analytical_2D(CSParallelepipedParameters *pars, double q, double phi);
double csparallelepiped_analytical_2DXY(CSParallelepipedParameters *pars, double qx, double qy);
double csparallelepiped_analytical_2D_scaled(CSParallelepipedParameters *pars, double q, double q_x, double q_y);
#endif

#if !defined(sc_h)
#define sc_h

/**
 * Structure definition for SC_ParaCrystal parameters
 */
 //[PYTHONCLASS] = SCCrystalModel
 //[DISP_PARAMS] = radius,phi, psi, theta
 //[DESCRIPTION] =<text>P(q)=(scale/Vp)*V_lattice*P(q)*Z(q)+bkg where scale is the volume
 //					 fraction of sphere,
 //				Vp = volume of the primary particle,
 //				V_lattice = volume correction for
 //					for the crystal structure,
 //				P(q)= form factor of the sphere (normalized),
 //				Z(q)= paracrystalline structure factor
 //					for a simple cubic structure.
 //				Parameters;
 //				scale: volume fraction of spheres
 //				bkg:background, R: radius of sphere
 //				dnn: Nearest neighbor distance
 //				d_factor: Paracrystal distortion factor
 //				radius: radius of the spheres
 //				sldSph: SLD of the sphere
 //				sldSolv: SLD of the solvent
 //
 //		</text>
 //[FIXED]=  radius.width;phi.width;psi.width; theta.width
 //[ORIENTATION_PARAMS]= <text> phi;psi; theta; phi.width;psi.width; theta.width</text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	Nearest neighbor distance [A]
    //  [DEFAULT]=dnn=220.0 [A]
    double dnn;

    ///	Paracrystal distortion factor g
    //  [DEFAULT]=d_factor=0.06
    double d_factor;

    ///	Radius of sphere [A]
    //  [DEFAULT]=radius=40.0 [A]
    double radius;

    ///	sldSph [1/A^(2)]
    //  [DEFAULT]=sldSph= 3.0e-6 [1/A^(2)]
    double sldSph;

    ///	sldSolv [1/A^(2)]
    //  [DEFAULT]=sldSolv= 6.3e-6 [1/A^(2)]
    double sldSolv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0 [1/cm]
	double background;
    /// Orientation of the a1 axis w/respect incoming beam [rad]
    //  [DEFAULT]=theta=0.0 [rad]
    double theta;
    /// Orientation of the a2 in the plane of the detector [rad]
    //  [DEFAULT]=phi=0.0 [rad]
    double phi;
    /// Orientation of the a3 in the plane of the detector [rad]
    //  [DEFAULT]=psi=0.0 [rad]
    double psi;

} SCParameters;



/// 1D scattering function
double sc_analytical_1D(SCParameters *pars, double q);

/// 2D scattering function
double sc_analytical_2D(SCParameters *pars, double q, double phi);
double sc_analytical_2DXY(SCParameters *pars, double qx, double qy);
double sc_analytical_2D_scaled(SCParameters *pars, double q, double q_x, double q_y);

#endif

#if !defined(HayterMSA_h)
#define HayterMSA_h

/**
 * Structure definition for screened Coulomb interaction
 */
 //[PYTHONCLASS] = HayterMSAStructure
 //[DISP_PARAMS] = effect_radius
 //[DESCRIPTION] =<text>To calculate the structure factor (the Fourier transform of the
 //                     pair correlation function g(r)) for a system of
 //                     charged, spheroidal objects in a dielectric
 //						medium.
 //                     When combined with an appropriate form
 //                     factor, this allows for inclusion of
 //                     the interparticle interference effects
 //                     due to screened coulomb repulsion between
 //                     charged particles.
 //						(Note: charge > 0 required.)
 //
 //                     Ref: JP Hansen and JB Hayter, Molecular
 //                           Physics 46, 651-656 (1982).
 //
 //				</text>
 //[FIXED]= effect_radius.width

typedef struct {
    ///	effetitve radius of particle [A]
    //  [DEFAULT]=effect_radius=20.75 [A]
    double effect_radius;

    /// charge
    //  [DEFAULT]=charge= 19
    double charge;

    /// Volume fraction
    //  [DEFAULT]=volfraction= 0.0192
    double volfraction;

	///	Temperature [K]
    //  [DEFAULT]=temperature= 318.16 [K]
    double temperature;

	///	Monovalent salt concentration [M]
    //  [DEFAULT]=saltconc= 0 [M]
    double saltconc;

    ///	Dielectric constant of solvent
    //  [DEFAULT]=dielectconst= 71.08
    double dielectconst;
} HayterMSAParameters;



/// 1D scattering function
double HayterMSA_analytical_1D(HayterMSAParameters *pars, double q);

/// 2D scattering function
double HayterMSA_analytical_2D(HayterMSAParameters *pars, double q, double phi);
double HayterMSA_analytical_2DXY(HayterMSAParameters *pars, double qx, double qy);

#endif

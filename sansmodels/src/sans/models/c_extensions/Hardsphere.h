#if !defined(Hardsphere_h)
#define Hardsphere_h

/**
 * Structure definition for HardsphereStructure (factor) parameters
 */
 //[PYTHONCLASS] = HardsphereStructure
 //[DISP_PARAMS] = effect_radius
 //[DESCRIPTION] =<text>Structure factor for interacting particles:                   .
 //
 //  The interparticle potential is
 //
 //                     U(r)= inf   , r < 2R
 //                         = 0     , r >= 2R
 //
 //						R: effective radius of the Hardsphere particle
 //						V:The volume fraction
 //
 //    Ref: Percus., J. K.,etc., J. Phy.
 //     Rev. 1958, 110, 1.
 //	 </text>
 //[FIXED]= effect_radius.width


typedef struct {
    /// effect radius of hardsphere [A]
    //  [DEFAULT]=effect_radius=50.0 [A]
    double effect_radius;

    ///	Volume fraction
    //  [DEFAULT]=volfraction= 0.2
    double volfraction;
} HardsphereParameters;



/// 1D scattering function
double Hardsphere_analytical_1D(HardsphereParameters *pars, double q);

/// 2D scattering function
double Hardsphere_analytical_2D(HardsphereParameters *pars, double q, double phi);
double Hardsphere_analytical_2DXY(HardsphereParameters *pars, double qx, double qy);

#endif

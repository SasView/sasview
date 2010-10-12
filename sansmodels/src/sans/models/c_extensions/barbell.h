#if !defined(barbell_h)
#define barbell_h

/**
 * Structure definition for BarBell parameters
 */
 //[PYTHONCLASS] = BarBellModel
 //[DISP_PARAMS] = rad_bar,len_bar,rad_bell,phi,  theta
 //[DESCRIPTION] =<text>Calculates the scattering from a barbell-shaped cylinder. That is
 //				a sphereocylinder with spherical end caps
 //				that have a radius larger than that of
 //				the cylinder and the center of the end cap
 //				radius lies outside of the cylinder.
 //				Note: As the length of cylinder(bar) -->0,
 //				it becomes a dumbbell.
 //				And when rad_bar = rad_bell,
 //				it is a spherocylinder.
 //				It must be that rad_bar <(=) rad_bell.
 //				[Parameters];
 //				scale: volume fraction of spheres,
 //				background:incoherent background,
 //				rad_bar: radius of the cylindrical bar,
 //				len_bar: length of the cylindrical bar,
 //				rad_bell: radius of the spherical bell,
 //				sld_barbell: SLD of the barbell,
 //				sld_solv: SLD of the solvent.
 //		</text>
 //[FIXED]=  rad_bar.width;len_bar;rad_bell;phi.width; theta.width
 //[ORIENTATION_PARAMS]= <text> phi; theta; phi.width; theta.width</text>

typedef struct {
    /// Scale factor
    //  [DEFAULT]=scale= 1.0
    double scale;

    ///	rad_bar [A]
    //  [DEFAULT]=rad_bar=20.0 [A]
    double rad_bar;

    ///	length of the bar [A]
    //  [DEFAULT]=len_bar=400.0 [A]
    double len_bar;

    ///	Radius of sphere [A]
    //  [DEFAULT]=rad_bell=40.0 [A]
    double rad_bell;

    ///	sld_barbell [1/A^(2)]
    //  [DEFAULT]=sld_barbell= 1.0e-6 [1/A^(2)]
    double sld_barbell;

    ///	sld_solv [1/A^(2)]
    //  [DEFAULT]=sld_solv= 6.3e-6 [1/A^(2)]
    double sld_solv;

	/// Incoherent Background [1/cm]
	//  [DEFAULT]=background=0.0 [1/cm]
	double background;

    /// Angle of the main axis against z-axis in detector plane [rad]
    //  [DEFAULT]=theta=0.0 [rad]
    double theta;
    /// Azimuthal angle around z-axis in detector plane [rad]
    //  [DEFAULT]=phi=0.0 [rad]
    double phi;

} BarBellParameters;



/// 1D scattering function
double barbell_analytical_1D(BarBellParameters *pars, double q);

/// 2D scattering function
double barbell_analytical_2D(BarBellParameters *pars, double q, double phi);
double barbell_analytical_2DXY(BarBellParameters *pars, double qx, double qy);
double barbell_analytical_2D_scaled(BarBellParameters *pars, double q, double q_x, double q_y);

#endif

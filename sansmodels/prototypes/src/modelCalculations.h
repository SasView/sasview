#if !defined(modelcalcs_h)
#define modelcalcs_h

typedef struct {
	double x;
	double y;
	double z;
} SpacePoint;



typedef struct {
    /// Volume points
    SpacePoint * points;
    /// Pair correlation function
    double * rho;
    /// Is rho already generated?
    int isRhoAvailable;
    /// Memory allocation flag 
    int isPointMemAllocated;
    
    /// Volume points
    SpacePoint * points_2D;
    /// Pair correlation function
    float * rho_2D;
    /// Is rho already generated?
    int isRhoAvailable_2D;
    /// Memory allocation flag
    int isPointMemAllocated_2D;
    
    //TODO: add volume_points, r_points, step here...
    
    int volume_points;
    int r_points;
    
    float timePr_1D;
    float timePr_2D;
    float timeIq_1D;
    float timeIq_2D;
    
    int errorOccured;
    
    
} CalcParameters;

void modelcalculations_dealloc(CalcParameters *pars);
void modelcalculations_init(CalcParameters *pars);
void modelcalculations_reset(CalcParameters *pars);


double modelcalculations_calculateIq_1D(double * rho, int r_points, double step, double q);
int modelcalculations_calculatePairCorrelation_1D(SpacePoint * points, int volume_points, double * rho, int r_points, double size);

double modelcalculations_calculateIq_2D(float * rho, int r_points, double step, double q, double phi);
int modelcalculations_calculatePairCorrelation_2D(SpacePoint * points, int volume_points, float * rho, int r_points, double size);

double modelcalculations_calculateIq_2D_3Darray(float * rho, int r_points, double step, double q, double phi);
int modelcalculations_calculatePairCorrelation_2D_3Darray(SpacePoint * points, int volume_points, float * rho, int r_points, double size);
SpacePoint modelcalculations_rotate(SpacePoint p, double theta, double phi, double omega);

int modelcalculations_calculatePairCorrelation_2D_vector(SpacePoint * points, int volume_points, float * rho, 
			int r_points, double bin_width, double theta_beam, double phi_beam, double omega_beam);

#endif
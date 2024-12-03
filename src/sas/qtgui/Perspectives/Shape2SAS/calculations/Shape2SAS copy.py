
import time
import argparse
import warnings
import re

from sas.qtgui.Perspectives.Shape2SAS.calculations.helpfunctions import (
    GenerateAllPoints, WeightedPairDistribution, StructureFactor, ITheoretical, IExperimental, Qsampling,
    plot_2D, plot_results, generate_pdb
)
from sas.qtgui.Perspectives.Shape2SAS.DataHandler.Parameters import (ScatteringCalculation, SimulatedScattering, 
                                                TheoreticalScattering, ModelProfile, ModelPointDistribution)

################################ Shape2SAS functions ################################
def getPointDistribution(prof: ModelProfile, Npoints) -> ModelPointDistribution:
    """Generate points for a given model profile."""

    x_new, y_new, z_new, _, _ = GenerateAllPoints(Npoints, prof.com, prof.subunits, 
                                                  prof.dimensions, prof.rotation, 
                                                  prof.p_s, prof.exclude_overlap).onGeneratingAllPoints()
    
    return ModelPointDistribution(x=x_new, y=y_new, z=z_new)


def getTheoreticalScattering(scalc: ScatteringCalculation) -> TheoreticalScattering:
    """Calculate theoretical scattering for a given model profile."""
    sys = scalc.System #system
    calc = scalc.Calculation #calcualtion
    prof = sys.Profile #profile

    x_new, y_new, z_new, p_new, volume_total = GenerateAllPoints(calc.Npoints, prof.com, prof.subunits, 
                                                                 prof.dimensions, prof.rotation, prof.p_s, 
                                                                 prof.exclude_overlap).onGeneratingAllPoints()
    
    r, pr, _ = WeightedPairDistribution(x_new, y_new, z_new, p_new).calc_pr(calc.prpoints, sys.polydispersity)

    q = Qsampling(calc.qmin, calc.qmax, calc.Nq).onQsampling()
    I_theory = ITheoretical(q)
    _, Pq = I_theory.calc_Pq(r, pr, sys.conc, volume_total)

    S_class = StructureFactor(q, x_new, y_new, z_new, p_new, sys.Stype, sys.par)
    S_eff = S_class.getStructureFactor().structure_eff(Pq)

    I = I_theory.calc_Iq(Pq, S_eff, sys.sigma_r)

    return TheoreticalScattering(I_theory=I, q=q)


def getSimulatedScattering(scalc: ScatteringCalculation) -> SimulatedScattering:
    """Simulate scattering for a given theoretical scattering."""
    sys = scalc.System #system
    calc = scalc.Calculation #calculation
    prof = sys.Profile #profile

    x_new, y_new, z_new, p_new, volume_total = GenerateAllPoints(calc.Npoints, prof.com, prof.subunits, 
                                                                 prof.dimensions, prof.rotation, prof.p_s, 
                                                                 prof.exclude_overlap).onGeneratingAllPoints()
    r, pr, _ = WeightedPairDistribution(x_new, y_new, z_new, p_new).calc_pr(calc.prpoints, sys.polydispersity)
    
    q = Qsampling(calc.qmin, calc.qmax, calc.Nq).onQsampling()
    I_theory = ITheoretical(q)
    I0, Pq = I_theory.calc_Pq(r, pr, sys.conc, volume_total)

    S_class = StructureFactor(q, x_new, y_new, z_new, p_new, sys.Stype, sys.par)
    S_eff = S_class.getStructureFactor().structure_eff(Pq)

    I = I_theory.calc_Iq(Pq, S_eff, sys.sigma_r)

    Isim_class = IExperimental(q, I0, I, sys.exposure)
    I_sim, I_err = Isim_class.simulate_data()

    return SimulatedScattering(I_sim=I_sim, q=q, I_err=I_err)


################################ Shape2SAS batch version ################################
if __name__ == "__main__":
    ################################ Read argparse input ################################
    def float_list(arg):
        """
        Function to convert a string to a list of floats.
        Note that this function can interpret numbers with scientific notation 
        and negative numbers.

        input:
            arg: string, input string

        output:
            list of floats
        """

        arg = arg.replace(' ', '')
        arg = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", arg)

        return [float(i) for i in arg]

    def separate_string(arg):

        arg = re.split('[ ,]+', arg)
        return [str(i) for i in arg]


    def str2bool(v):
        """
        Function to circumvent the argparse default behaviour 
        of not taking False inputs, when default=True.
        """
        if v == "True":
            return True
        elif v == "False":
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    ################################ Check input values for batch version ################################
    def check_3Dinput(input: list, default: list, name: str, N_subunits: int, i: int):
        """
        Function to check if 3D vector input matches 
        in lenght with the number of subunits

        input:
            input: list of floats, input values
            default: list of floats, default values

        output:
            list of floats
        """
        try:
            inputted = input[i]
            if len(inputted) != N_subunits:
                warnings.warn(f"The number of subunits and {name} do not match. Using {default}")
                inputted = default * N_subunits
        except:
            inputted = default * N_subunits
            warnings.warn(f"Could not find {name}. Using default {default}.")

        return inputted


    def check_input(input: float, default: float, name: str, i: int):
        """
        Function to check if input is given, 
        if not, use default value.

        input:
            input: float, input value
            default: float, default value
            name: string, name of the input

        output:
            float
        """
        try:
            inputted = input[i]

        except:
            inputted = default
            warnings.warn(f"Could not find {name}. Using default {default}.")

        return inputted

    start_total = time.time()

    #input values
    parser = argparse.ArgumentParser(description='Shape2SaS - calculates small-angle scattering from a given shape defined by the user.')

    #general input options
    parser.add_argument('-qmin', '--qmin', type=float, default=0.001, 
                        help='Minimum q-value for the scattering curve.')
    parser.add_argument('-qmax', '--qmax', type=float, default=0.5, 
                        help='Maximum q-value for the scattering curve.')
    parser.add_argument('-qp', '--qpoints', type=int, default=400, 
                        help='Number of points in q.')
    parser.add_argument('-expo', '--exposure', type=float, default=500, 
                        help='Exposure time in arbitrary units.')
    parser.add_argument('-prp', '--prpoints', type=int, default=100, 
                        help='Number of points in the pair distance distribution function.')
    parser.add_argument('-Np', '--Npoints', type=int, default=3000, 
                        help='Number of simulated points.')
    
    #specific input options for each model
    parser.add_argument('-name', '--name', nargs='+', action='extend',
                        help='Name of model.')
    parser.add_argument('-excluolap', '--exclude_overlap', type=str2bool, default=True, 
                        help='bool to exclude overlap.')
    parser.add_argument('-subtype', '--subunit_type', type=separate_string, nargs='+', action='extend',
                        help='Type of subunits for each model.')
    
    #--a --b --c ---> dimension 'a b c'
    parser.add_argument('-dim', '--dimension', type=float_list, nargs='+', action='append',
                        help='dimensions of subunits for each model.')
    
    parser.add_argument('-p', '--p', type=float, nargs='+', action='append',
                        help='scattering length density.')
    
    #--x --y --z ---> com =  'x y z'
    parser.add_argument('-com', '--com', type=float_list, nargs='+', action='append', 
                        help='displacement for each subunits in each model.')
    parser.add_argument('-rotation', '--rotation', type=float_list, nargs='+', action='append', 
                        help='rotation for each subunits in each model.')
    
    parser.add_argument('-poly', '--polydispersity', type=float, nargs='+', action='extend',
                        help='Polydispersity of subunits for each model.')
    parser.add_argument('-S', '--S', type=str, nargs='+', action='extend',
                        help='structure factor: None/HS/aggregation in each model.')
    parser.add_argument('-rhs', '--r_hs', type=float, nargs='+', action='extend',
                        help='radius of hard sphere in each model.')
    parser.add_argument('-frac', '--frac', type=float, nargs='+', action='extend',
                        help='fraction of particles in aggregated form for each model.')
    parser.add_argument('-Naggr', '--N_aggr', type=int, nargs='+', action='extend',
                        help='Number of particles per aggregate for each model.')
    parser.add_argument('-Reff', '--R_eff', type=float, nargs='+', action='extend',
                        help='Effective radius of aggregates for each model.')
    parser.add_argument('-conc', '--conc', type=float, nargs='+', action='extend',
                        help='volume fraction concentration.')
    parser.add_argument('-sigmar', '--sigma_r', type=float, nargs='+', action='extend',
                        help='interface roughness for each model.')
    
    #plot options
    parser.add_argument('-xsclin', '--xscale_lin', type=str2bool, default=True, 
                        help='bool to include linear q scale.')
    parser.add_argument('-hres', '--high_res', type=bool, default=False, 
                        help='bool to include high resolution.')
    parser.add_argument('-scale', '--scale', type=int, nargs='+', action='extend',
                        help='In the plot, scale simulated intensity of each model.')       

    args = parser.parse_args()

    qmin = args.qmin
    qmax = args.qmax
 
    Nq = args.qpoints
    q = Qsampling(qmin, qmax, Nq).onQsampling()
    exposure = args.exposure
    Nbins = args.prpoints
    Npoints = args.Npoints
    exclude_overlap = args.exclude_overlap
    xscale_lin = args.xscale_lin
    high_res = args.high_res

    subunit_type = args.subunit_type

    if subunit_type is None:
        raise argparse.ArgumentError(subunit_type, "No subunit type was given as an input.")
    
    dimensions = args.dimension
    if dimensions is None:
        raise argparse.ArgumentError(dimensions, "No dimensions were given as an input.")
    
    for subunit, dimension in zip(subunit_type, dimensions):
         if len(subunit) != len(dimension):
            raise argparse.ArgumentTypeError("Mismatch between subunit types and dimensions.")
    
    r_list, pr_norm_list, I_list, Isim_list, sigma_list, S_eff_list, x_list, y_list, z_list, p_list, Model_list, scale_list, name_list = [], [], [], [], [], [], [], [], [], [], [], [], []
    num_models = len(subunit_type)
    
    print(f"Simulating {num_models} model(s)...")
    for i in range(num_models):
        print(" ")
        print(f"    Generating points for Model {i}")
        
        subunits = subunit_type[i]
        dims = dimensions[i]
        N_subunits = len(subunits)

        #check for SLD, COM, and rotation
        p_s = check_3Dinput(args.p, [1.0], "SLD", N_subunits, i)
        com = check_3Dinput(args.com, [[0, 0, 0]], "COM", N_subunits, i)
        rotation = check_3Dinput(args.rotation, [[0, 0, 0]], "rotation", N_subunits, i)

        #Generate points
        x_new, y_new, z_new, p_new, volume_total = GenerateAllPoints(Npoints, com, subunits, dims, rotation, p_s, exclude_overlap).onGeneratingAllPoints()

        ################### Calculate the pair distance for all points ###################
        #Check polydispersity input
        pd = check_input(args.polydispersity, 0.0, "polydispersity", i)
        Model = f'{i}'

        r, pr, pr_norm = WeightedPairDistribution(x_new, y_new, z_new, p_new).calc_pr(Nbins, pd)
        WeightedPairDistribution.save_pr(Nbins, r, pr, Model)


        ################### Calculate I(q) using histogram ###################
        print(" ")
        print("        Calculating intensity, I(q)...")

        #check structure factor and concentration
        Stype = check_input(args.S, 'None', "Structure type", i)
        par_dic = StructureFactor.getparname(Stype)
        par = []
        for name in par_dic.keys():
            attr = getattr(args, name, f"{name} could not be found. Uses default value {par_dic[name]}")[i]
            if attr == str:
                par.append(par_dic[name])
                print(f"        {name} could not be found. Uses default value {par_dic[name]}.")
            else:
                par.append(attr)

        conc = check_input(args.conc, 0.02, "concentration", i)

        S_class = StructureFactor(q, x_new, y_new, z_new, p_new, Stype, par)
        S_eff = S_class.getStructureFactor()
        S_class.save_S(S_eff, Model)

        #check interface roughness
        sigma_r = check_input(args.sigma_r, 0.0, "sigma_r", i)

        I_theory = ITheoretical(q)
        I0, Pq = I_theory.calc_Pq(r, pr, conc, volume_total)
        I = I_theory.calc_Iq(Pq, S_eff, sigma_r, Model)
        I_theory.save_I(I, Model)


        Isim_class = IExperimental(q, I0, I, exposure)
        Isim, sigma = Isim_class.simulate_data()
        Isim_class.save_Iexperimental(Isim, sigma, Model)

        #check model name and scaling
        name = check_input(args.name, f"Model {i}", "model name", i)
        scale = check_input(args.scale, 1, "scale", i)

        r_list.append(r)
        pr_norm_list.append(pr_norm)
        I_list.append(I)
        Isim_list.append(Isim)
        sigma_list.append(sigma)
        S_eff_list.append(S_eff)
        x_list.append(x_new)
        y_list.append(y_new)
        z_list.append(z_new)
        p_list.append(p_new)
        Model_list.append(Model)
        scale_list.append(scale)
        name_list.append(name)

        del x_new, y_new, z_new, p_new
    
    print(" ")
    print("Generating plots...")
    print(" ")
    #plot 2D projections

    plot_2D(x_list, y_list, z_list, p_list, Model_list, high_res)

    #3D vizualization: generate pdb file with points
    generate_pdb(x_list, y_list, z_list, p_list, Model_list)

    #plot p(r) and I(q)
    plot_results(q, r_list, pr_norm_list, I_list, Isim_list, 
                 sigma_list, S_eff_list, name_list, scale_list, xscale_lin, high_res)
    

    time_total = time.time() - start_total
    print(" ")
    print("Simulation successfully completed.")
    print("    Total run time:", round(time_total, 3), "seconds.")
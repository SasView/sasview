
from pathlib import Path
from sas.sascalc.fit import models
from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import ModelProfile
from numpy import inf

###TODO: add constraints as an input argument
def generatePlugin(prof: ModelProfile, dim_names: list[list[str]], file_name: str) -> tuple[str, Path]:
    """Generates a theoretical scattering plugin model"""

    plugin_location = Path(models.find_plugins_dir())
    if not file_name.endswith('.py'):
        file_name += '.py'
    full_path = plugin_location / file_name

    model_str = generateModel(prof, dim_names, file_name)

    return model_str, full_path

###TODO: add constraints as an input argument
def generateModel(prof: ModelProfile, dim_names: list[list[str]], model_name: str) -> str:
    """Generates a theoretical model"""

    pars = []
    par_names = []

    for i in range(len(prof.subunits)):
        num_col = i + 1
        delta_sld = prof.p_s[i]
        pars.append(["ΔSLD" + str(num_col), "", delta_sld, [-inf, inf], "ΔSLD", 
                     f"ΔSLD for {prof.subunits[i]} in column {num_col}"])

        for j in range(len(prof.dimensions[i])):
            par_name = f"{dim_names[i][j]}" + f"{num_col}"
            pars.append([par_name, "Å", prof.dimensions[i][j], 
                         [0, inf], "Length", f"{dim_names[i][j]} for {prof.subunits[i]} in column {num_col}"])
            par_names.append(par_name)

        alpha, beta, gamma = prof.rotation[i]
        pars.append(["α" + str(num_col), "Degree", alpha, [-inf, inf], "Angle", 
                     f"Angle α for {prof.subunits[i]} in column {num_col}"])
        pars.append(["β" + str(num_col), "Degree", beta, [-inf, inf], "Angle", 
                     f"Angle β for {prof.subunits[i]} in column {num_col}"])
        pars.append(["γ" + str(num_col), "Degree", gamma, [-inf, inf], "Angle", 
                     f"Angle γ for {prof.subunits[i]} in column {num_col}"])

    model_str = (f'''
r"""
This plugin model uses Shape2SAS to generate theoretical small-angle scattering data. Shape2SAS is a program build by Larsen and Brookes
(doi: https://doi.org/10.1107/S1600576723005848) to calculate small-angle scattering data and pair distance distributions
from a user built model. The user builds this model by combining pre-defined geometrical subunits. Each subunit may be rotated and translated to the
users desired position, resulting in a broad range of possible models to be created. 
Besides calculating theoretical scattering, Shape2SAS is also able to simulate small-angle scattering with noise.

###TODO: maybe add a method description on how Shape2SAS generates the scattering data??? bead model                 


Model {model_name.replace('.py', '')} was built from the following subunits:
{', '.join(prof.subunits)}
                 
"""



name = "{model_name.replace('.py', '')}"
title = "Shape2SAS Model"
description = """
Theoretical generation of P(q) using Shape2SAS
"""
category = "plugin"

#   ["name", "units", default, [lower, upper], "type","description"],
parameters = {pars}

def Iq(q, {', '.join(par_names)}):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    
    modelProfile = ModelProfile(subunits={prof.subunits}, p_s={prof.p_s}, dimensions={par_names}, com={prof.com}, 
                           rotation_points={prof.rotation_points}, rotation={prof.rotation}, exclude_overlap={prof.exclude_overlap})
    simPar = SimulationParameters(qmin={"MISSING"}, qmax={"MISSING"}, Nq={"MISSING"}, prpoints={"MISSING"}, Npoints={"MISSING"})
    dist = getPointDistribution(modelProfile, {"MISSING"})

    scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=dist, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=0.2, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=SimulationParameters())
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I

''').lstrip().rstrip()
    
    return model_str



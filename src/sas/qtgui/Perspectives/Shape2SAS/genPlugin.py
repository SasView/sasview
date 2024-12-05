
from pathlib import Path
from sas.sascalc.fit import models
from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import ModelProfile
from numpy import inf

###TODO: add constraints as an input argument
def generatePlugin(prof: ModelProfile, Npoints: int, pr_points: int, file_name: str, dim_names: list[list[str]]) -> tuple[str, Path]:
    """Generates a theoretical scattering plugin model"""

    plugin_location = Path(models.find_plugins_dir())
    if not file_name.endswith('.py'):
        file_name += '.py'
    full_path = plugin_location / file_name

    model_str = generateModel(prof, Npoints, pr_points, file_name, dim_names)

    return model_str, full_path

def onCheckConstant(name: str, val: float, checked: bool) -> str:
    """Checks if a parameter is constant or not"""

    if checked:
        #constant
        return name
    else:
        #parameter to be fitted
        return str(val)

def onAppendingList(pars: list[any], par: list[any]):
    """Convert list to string and append"""

    pars.append("[{}]".format(", ".join(par)))

def onAppending(pars: list[any], par: any):
    """Append to list"""

    pars.append(par[0])

def onAddParameterList(parameters: list[list[any]], vars: list[str], pars: list[any], checked: bool, checks: int, name: list[str], 
                       unit: list[str], vals: list[float], bounds: list[list], p_type: list[str], desc: list[str], appendMethod: any):
    """Adds a list of parameters to the list of parameters and pars"""

    par = []
    for i in range(len(name)):
        if checked[checks]:
            parameters.append([name[i], unit[i], vals[i], bounds[i], p_type[i], desc[i]])
            vars.append(name[i])
        val = onCheckConstant(name[i], vals[i], checked[checks])
        par.append(val)
        checks += 1
        
    appendMethod(pars, par)
    


###TODO: add constraints as an input argument
def generateModel(prof: ModelProfile, Npoints: int, pr_points: int, model_name: str, dim_names: list[list[str]]) -> str:
    """Generates a theoretical model"""

    ##list of check marks from the GUI on whether a parameter is constant or not
    checked = [True] * (len(prof.subunits) * 10 + sum([len(prof.dimensions[i]) for i in range(len(prof.dimensions))]))
    parameters = []
    dims = []
    vars = []
    ps = []
    coms = []
    rot_points = []
    rots = []

    checks = 0
    for i in range(len(prof.subunits)):
        num_col = i + 1

        sld_name = [f"ΔSLD{num_col}"]
        description = [f"ΔSLD{num_col} for column {num_col}"]
        onAddParameterList(parameters,
                            vars,
                            ps,
                            checked,
                            checks,
                            sld_name,
                            [""],
                            [prof.p_s[i]],
                            [[-inf, inf]],
                            ["ΔSLD"],
                            description,
                            onAppending)

        dim_name = [f"{dim_names[i][j]}" + f"{num_col}" for j in range(len(prof.dimensions[i]))]
        description_dim = [name + f" for {prof.subunits[i]} in column {num_col}" for name in dim_name]
        onAddParameterList(parameters, 
                           vars, 
                           dims, 
                           checked,
                           checks,
                           dim_name, 
                            ["Å"] * len(prof.dimensions[i]),
                            prof.dimensions[i],
                            [[0, inf]] * len(prof.dimensions[i]), 
                            ["Length"] * len(prof.dimensions[i]), 
                            description_dim,
                            onAppendingList)
        
        com_name = [f"COMX{num_col}", f"COMY{num_col}", f"COMZ{num_col}"]
        description = [com_name + f" for column {num_col}" for com_name in com_name]
        onAddParameterList(parameters,
                            vars,
                            coms,
                            checked,
                            checks,
                            com_name,
                            ["Å", "Å", "Å"],
                            prof.com[i],
                            [[-inf, inf], [-inf, inf], [-inf, inf]],
                            ["Length", "Length", "Length"],
                            com_name + [" for column {num_col}"] * 3,
                            onAppendingList)
        
        rot_points_name = [f"RPX{num_col}", f"RPY{num_col}", f"RPZ{num_col}"]
        description_rot_points = [rot_points_name + f" for column {num_col}" for rot_points_name in rot_points_name]
        onAddParameterList(parameters,
                            vars,
                            rot_points,
                            checked,
                            checks,
                            rot_points_name,
                            ["Å", "Å", "Å"],
                            prof.rotation_points[i],
                            [[-inf, inf], [-inf, inf], [-inf, inf]],
                            ["Length", "Length", "Length"],
                            description_rot_points,
                            onAppendingList)

        rot_name = [f"α{num_col}", f"β{num_col}", f"γ{num_col}"]
        description_rot = [rot_name + f" for column {num_col}" for rot_name in rot_name]
        onAddParameterList(parameters,
                            vars,
                            rots,
                            checked,
                            checks,
                            rot_name,
                            ["Degree", "Degree", "Degree"],
                            prof.rotation[i],
                            [[-inf, inf], [-inf, inf], [-inf, inf]],
                            ["Angle", "Angle", "Angle"],
                            description_rot,
                            onAppendingList)
        
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
from numpy import inf

name = "{model_name.replace('.py', '')}"
title = "Shape2SAS Model"
description = """
Theoretical generation of P(q) using Shape2SAS
"""
category = "plugin"

#   ["name", "units", default, [lower, upper], "type","description"],
parameters = {parameters}

def Iq(q, {', '.join(vars)}):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    
    modelProfile = ModelProfile(subunits={prof.subunits}, p_s=[{', '.join(ps)}], dimensions=[{', '.join(dims)}], com=[{','.join(coms)}], 
                                rotation_points=[{','.join(rot_points)}], rotation=[{', '.join(rots)}], exclude_overlap={prof.exclude_overlap})
    
    simPar = SimulationParameters(q, prpoints={pr_points}, Npoints={Npoints}, model_name={model_name.replace('.py', '')})
    dist = getPointDistribution(modelProfile, {Npoints})

    scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=dist, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=1, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=simPar)
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I

''').lstrip().rstrip()
    
    return model_str



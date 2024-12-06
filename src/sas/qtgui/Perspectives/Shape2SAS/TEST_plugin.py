r"""
###TODO: Rewrite this description
This plugin model uses Shape2SAS to generate theoretical small-angle scattering data. Shape2SAS is a program build by Larsen and Brookes
(doi: https://doi.org/10.1107/S1600576723005848) to calculate small-angle scattering data and pair distance distributions
from a user built model. The user builds this model by combining pre-defined geometrical subunits. Each subunit may be rotated and translated to the
users desired position, resulting in a broad range of possible models to be created. 
Besides calculating theoretical scattering, Shape2SAS is also able to simulate small-angle scattering with noise.

###TODO: maybe add a method description on how Shape2SAS generates the scattering data??? bead model                 

Model Model_1 was built from the following subunits:
Sphere

"""
from numpy import inf
from sas.qtgui.Perspectives.Shape2SAS.calculations.Shape2SAS import (ModelProfile, SimulationParameters, 
                                                        ModelSystem, getPointDistribution, 
                                                        TheoreticalScatteringCalculation, 
                                                        getTheoreticalScattering)

name = "Model_1"
title = "Shape2SAS Model"
description = """
Theoretical generation of P(q) using Shape2SAS
"""
category = "shape:Plugin Models"

#   ["name", "units", default, [lower, upper], "type","description"],
parameters = [['ΔSLD1', '', 1.0, [-inf, inf], 'ΔSLD', 'ΔSLD1 for column 1'], ['R1', 'Å', 50.0, [0, inf], 'Length', 'R1 for Sphere in column 1'], ['COMX1', 'Å', 0.0, [-inf, inf], 'Length', 'COMX1'], ['COMY1', 'Å', 0.0, [-inf, inf], 'Length', 'COMY1'], ['COMZ1', 'Å', 0.0, [-inf, inf], 'Length', 'COMZ1'], ['RPX1', 'Å', 0.0, [-inf, inf], 'Length', 'RPX1 for column 1'], ['RPY1', 'Å', 0.0, [-inf, inf], 'Length', 'RPY1 for column 1'], ['RPZ1', 'Å', 0.0, [-inf, inf], 'Length', 'RPZ1 for column 1'], ['α1', 'Degree', 0.0, [-inf, inf], 'Angle', 'α1 for column 1'], ['β1', 'Degree', 0.0, [-inf, inf], 'Angle', 'β1 for column 1'], ['γ1', 'Degree', 0.0, [-inf, inf], 'Angle', 'γ1 for column 1']]

def Iq(q, ΔSLD1, R1, COMX1, COMY1, COMZ1, RPX1, RPY1, RPZ1, α1, β1, γ1):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    
    modelProfile = ModelProfile(subunits=['Sphere'], p_s=[ΔSLD1], dimensions=[[R1]], com=[[COMX1, COMY1, COMZ1]], 
                                rotation_points=[[RPX1, RPY1, RPZ1]], rotation=[[α1, β1, γ1]], exclude_overlap=True)
    
    simPar = SimulationParameters(q, prpoints=100, Npoints=3000, model_name="Model_1")
    dist = getPointDistribution(modelProfile, 3000)

    scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=dist, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=1, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=simPar)
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I

Iq.vectorized = True
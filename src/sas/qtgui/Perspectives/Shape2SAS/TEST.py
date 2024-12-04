r"""
This plugin model uses Shape2SAS to generate theoretical small-angle scattering data. Shape2SAS is a program build by Larsen and Brookes
(doi: https://doi.org/10.1107/S1600576723005848) to calculate small-angle scattering data and pair distance distributions
from a user built model. The user builds this model by combining pre-defined geometrical subunits. Each subunit may be rotated and translated to the
users desired position, resulting in a broad range of possible models to be created. 
Besides calculating theoretical scattering, Shape2SAS is also able to simulate small-angle scattering with noise.

###TODO: maybe add a method description on how Shape2SAS generates the scattering data??? bead model                 


Model model_1 was built from the following subunits:
Sphere, Cuboid
                 
"""
from numpy import inf

name = "model_1"
title = "Shape2SAS Model"
description = """
Theoretical generation of P(q) using Shape2SAS
"""
category = "plugin"

#   ["name", "units", default, [lower, upper], "type","description"],
parameters = [['ΔSLD1', '', 1.0, [-inf, inf], 'ΔSLD', 'ΔSLD1 for column 1'], ['R1', 'Å', 50.0, [0, inf], 'Length', 'R1 for Sphere in column 1'], ['COMX1', 'Å', 0.0, [-inf, inf], 'Length', 'COMX1'], ['COMY1', 'Å', 0.0, [-inf, inf], 'Length', 'COMY1'], ['COMZ1', 'Å', 0.0, [-inf, inf], 'Length', 'COMZ1'], ['RPX1', 'Å', 0.0, [-inf, inf], 'Length', 'RPX1 for column 1'], ['RPY1', 'Å', 0.0, [-inf, inf], 'Length', 'RPY1 for column 1'], ['RPZ1', 'Å', 0.0, [-inf, inf], 'Length', 'RPZ1 for column 1'], ['α1', 'Degree', 0.0, [-inf, inf], 'Angle', 'α1 for column 1'], ['β1', 'Degree', 0.0, [-inf, inf], 'Angle', 'β1 for column 1'], ['γ1', 'Degree', 0.0, [-inf, inf], 'Angle', 'γ1 for column 1'], ['ΔSLD2', '', 1.0, [-inf, inf], 'ΔSLD', 'ΔSLD2 for column 2'], ['a2', 'Å', 50.0, [0, inf], 'Length', 'a2 for Cuboid in column 2'], ['b2', 'Å', 50.0, [0, inf], 'Length', 'b2 for Cuboid in column 2'], ['c2', 'Å', 200.0, [0, inf], 'Length', 'c2 for Cuboid in column 2'], ['COMX2', 'Å', 0.0, [-inf, inf], 'Length', 'COMX2'], ['COMY2', 'Å', 0.0, [-inf, inf], 'Length', 'COMY2'], ['COMZ2', 'Å', 0.0, [-inf, inf], 'Length', 'COMZ2'], ['RPX2', 'Å', 0.0, [-inf, inf], 'Length', 'RPX2 for column 2'], ['RPY2', 'Å', 0.0, [-inf, inf], 'Length', 'RPY2 for column 2'], ['RPZ2', 'Å', 0.0, [-inf, inf], 'Length', 'RPZ2 for column 2'], ['α2', 'Degree', 0.0, [-inf, inf], 'Angle', 'α2 for column 2'], ['β2', 'Degree', 0.0, [-inf, inf], 'Angle', 'β2 for column 2'], ['γ2', 'Degree', 0.0, [-inf, inf], 'Angle', 'γ2 for column 2']]

def Iq(q, ΔSLD1, R1, COMX1, COMY1, COMZ1, RPX1, RPY1, RPZ1, α1, β1, γ1, ΔSLD2, a2, b2, c2, COMX2, COMY2, COMZ2, RPX2, RPY2, RPZ2, α2, β2, γ2):
    """Fit function using Shape2SAS to calculate the scattering intensity."""
    
    modelProfile = ModelProfile(subunits=['Sphere', 'Cuboid'], p_s=[ΔSLD1, ΔSLD2], dimensions=[[R1], [a2, b2, c2]], com=[[COMX1, COMY1, COMZ1],[COMX2, COMY2, COMZ2]], 
                                rotation_points=[[RPX1, RPY1, RPZ1],[RPX2, RPY2, RPZ2]], rotation=[[α1, β1, γ1], [α2, β2, γ2]], exclude_overlap=True)
    
    simPar = SimulationParameters(qmin=MISSING, qmax=MISSING, Nq=MISSING, prpoints=MISSING, Npoints=MISSING)
    dist = getPointDistribution(modelProfile, MISSING)

    scattering = TheoreticalScatteringCalculation(System=ModelSystem(PointDistribution=dist, 
                                                                        Stype="None", par=[], 
                                                                        polydispersity=0.0, conc=1, 
                                                                        sigma_r=0.0), 
                                                                        Calculation=simPar)
    theoreticalScattering = getTheoreticalScattering(scattering)

    return theoreticalScattering.I
import time

import matplotlib.pyplot as plt
import numpy as np

from sas.qtgui.Perspectives.ParticleEditor.calculations.debye import debye
from sas.qtgui.Perspectives.ParticleEditor.datamodel.calculation import CalculationParameters, QSample, SLDDefinition
from sas.qtgui.Perspectives.ParticleEditor.sampling.points import Grid


def sld(x, y, z):
    """ Cube sld """
    out = np.ones_like(x)
    inds = np.logical_and(
        np.logical_and(
            np.abs(x) > 50,
            np.abs(y) > 50),
        np.abs(z) > 50)
    out[inds] = 0
    return out

def transform(x,y,z):
    return x,y,z

sld_def = SLDDefinition(sld_function=sld, to_cartesian_conversion=transform)

calc_params = CalculationParameters(
                solvent_sld=0.0,
                background=0.0,
                scale=1.0,
                sld_parameters={},
                magnetism_parameters={})

point_generator = Grid(100, 10_000)

q = QSample(1e-3, 1, 101, True)

for chunk_size in [1000]:
    for preallocate in [False, True]:

        print("Chunk size %i%s"%(chunk_size, ", preallocate" if preallocate else ""))

        start_time = time.time()

        output = debye(
            sld_definition=sld_def,
            magnetism_definition=None,
            parameters=calc_params,
            point_generator=point_generator,
            q_sample=q,
            minor_chunk_size=chunk_size,
            preallocate=preallocate)

        print(time.time() - start_time)

        plt.loglog(q(), output)

plt.show()

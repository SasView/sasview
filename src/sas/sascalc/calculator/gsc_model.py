"""
create plugin model from the Generic Scattering Calculator
"""
import math
from pathlib import Path

import numpy as np

from sas.sascalc.fit import models


def generate_plugin(f_name: str, data_to_plot: np.ndarray, x_values: np.ndarray, f_q: list,
                    mass: float) -> tuple[str, Path]:
    """Generate an empirical plugin model using calculated data.

    :param f_name: The desired file name for the resulting model
    :param data_to_plot: The plottable data
    :param x_values: The x values, as a numpy array
    :param f_q: The calculated F(Q)
    :param mass: The mass associated with the Rg calculation
    """
    # check if file exists & assign filename
    plugin_location = Path(models.find_plugins_dir())
    if not f_name.endswith('.py'):
        f_name += '.py'
    full_path = plugin_location / f_name

    # generate the model representation as a string
    model_str = generate_model(f_name, data_to_plot, x_values, f_q, mass)

    return model_str, full_path


def generate_model(f_name: str, data_to_plot: np.ndarray, x_values: np.ndarray, f_q: list, mass: float) -> str:
    """Generate an empirical model from the current plugin state
    """

    # TODO:
    #  This should be the correct normalization, but P(Q) has already been rescaled in a different part of the code
    #  pix_symbol = self.nuc_sld_data.pix_symbol
    #  sld = 0
    #  for i, sym in enumerate(pix_symbol):
    #      atom = periodictable.elements.symbol(sym)
    #      sld += atom.neutron.b_c
    #  normPQ = self.data_to_plot / (sld**2)
    norm_pq = data_to_plot/data_to_plot[0]   # temporary fix

    nq = len(x_values)
    log_q = "{" + ','.join(f'{math.log(v):.15e}' for v in x_values.tolist()) + "}"
    f_q = "{" + ','.join(f'{v:.15e}' for v in f_q) + "}"
    log_fq_sq_avg = "{" + ','.join(f'{math.log(v):.15e}' for v in norm_pq) + "}"
    prefactor = 1e-2

    model_str = (f'''
r"""
Example empirical model using interp.
"""
# Note: requires the pr-python-fq branch which may or may not have been merged.

import numpy as np
from numpy import inf
from types import SimpleNamespace as dotted


name = "{f_name.replace('.py', '')}"
title = "Model precalculated from PDB file."
description = """
Interpolate F(q) values from an interpolation table generated for the PDB
file {{pdbfile}}.pdb.
"""
#category = "shape:pdb"

#   ["name", "units", default, [lower, upper], "type","description"],
parameters = [
    ["sld", "1e-6/Ang^2", 1, [0, inf], "sld", "Protein scattering length density"],
    ["sld_solvent", "1e-6/Ang^2", 0, [-inf, inf], "sld", "Solvent scattering length density"],
    ["swelling", "", 1, [0, inf], "volume", "swelling parameter changing effective radius"],
    ["protein_volume", "Ang^3", 1, [0, inf], "volume", ""],
]

c_code =  r"""
#define NQ {nq}
constant double LOGQ[NQ] = {log_q};
constant double FQ[NQ] = {f_q};
constant double LOGFQSQ[NQ] = {log_fq_sq_avg};
constant double prefactor = {prefactor};

static double
form_volume(double swelling, double protein_volume)
{{
    return protein_volume;
}}

static double
radius_effective(int mode, double swelling,double protein_volume)
{{
    switch (mode) {{
    default:
    case 1: // equivalent sphere
    return (cbrt(protein_volume*3.0/4.0/M_PI))*swelling;
    case 2: // radius of gyration
    return {mass}*swelling;
    }}
}}

static void
Fq(double q, double *f1, double *f2, double sld, double sld_solvent, double swelling, double protein_volume)
{{
    const double logq = log(q*swelling);
    if (logq < LOGQ[0] || logq > LOGQ[NQ-1]) {{
        *f1 = *f2 = NAN;
        return;
    }}

    const double contrast = (sld - sld_solvent);
    const double scale = prefactor * contrast * form_volume(swelling, protein_volume);

    // binary search
    int steps = 0;
    const int max_steps = (int)(ceil(log((double)(NQ))/log(2.0)));

    int high = NQ-1;
    int low = 0;
    while (low < high-1) {{
        int mid = (high + low) / 2;
        if (logq < LOGQ[mid]) {{
            high = mid;
        }} else {{
            low = mid;
        }}
//printf("q: %g in [%d, %d]  (%g <= %g <= %g)\\n",q,low,high,LOGQ[low],logq,LOGQ[high]);
        if (steps++ > max_steps) {{
            printf("Binary search failed for q=%g\\n", q);
            *f1 = *f2 = NAN;
            return;
        }}
    }}
    //high = low+1;
    // linear interpolation
    const double x1 = LOGQ[low];
    const double x2 = LOGQ[high];
    const double frac = (logq - x1)/(x2-x1);
    *f1 = scale*(FQ[low]*(1-frac) + FQ[high]*frac);
    *f2 = scale*scale*exp(LOGFQSQ[low]*(1-frac) + LOGFQSQ[high]*frac);
//printf("scale: %g\\n", scale);
//printf("Done with q: %g in [%d, %d]  (%g <= %g <= %g)\\n",q,low,high,x1,logq, x2);
//printf("Frac: %g of interval [%g, %g] gives %g\\n", frac, LOGFQSQ[low],LOGFQSQ[high],LOGFQSQ[low]*(1-frac) + LOGFQSQ[high]*frac);
}}
"""
#print(c_code)

have_Fq = True
radius_effective_modes = ["equivalent sphere", "radius of gyration"]
''').lstrip().rstrip()

    return model_str

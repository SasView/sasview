import logging

import numpy as np


def sasview_sans_debye(q, coords, weight, worksize=100000):
    """
    Compute I(q) for a set of points using the full Debye formula.
    *q* is the q values for the calculation.
    *coords* are the sample points.
    *weight* is the weight associated with each point.
    *worksize* is the number of q values to compute at once.
    """
    Iq = np.zeros_like(q)
    q_pi = q/np.pi  # Precompute q/pi since np.sinc = sin(pi x)/(pi x).
    batch_size = worksize // coords.shape[0]
    for batch in range(0, len(q), batch_size):
        _calc_Iq_batch(Iq[batch:batch+batch_size], q_pi[batch:batch+batch_size],
                        coords, weight)
    return Iq

def _calc_Iq_batch(Iq, q_pi, coords, weight):
    """
    Helper function for _calc_Iq which operates on a batch of q values.
    *Iq* is accumulated within each batch, and should be initialized to zero.
    *q_pi* is q/pi, needed because np.sinc computes sin(pi x)/(pi x).
    *coords* are the sample points.
    *weight* is the weight associated with each point.
    """
    for j in range(len(weight)):
        if j % 100 == 0:
            logging.info(f"\tprogress: {j/len(weight)*100:.0f}%")
        # Compute dx for one row of the upper triangle matrix.
        dx = coords[:, j:] - coords[:, j:j+1]
        # Find the length of each dx vector.
        r = np.sqrt(np.sum(dx**2, axis=0))
        # Compute I_jk = rho_j rho_k j0(q ||x_j - x_k||) over all q in batch.
        bes = np.sinc(q_pi[:, None]*r[None, :])
        I_jk = (weight[j:] * weight[j])[None, :] * bes
        # Accumulate terms I(j,j), I(j, k+1..n) and by symmetry I(k+1..n, j).
        # Don't double-count the diagonal.
        Iq += 2*np.sum(I_jk, axis=1) - I_jk[:, 0]

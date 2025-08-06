import csv
import os

import numpy as np
import pytest

from sasdata.dataloader.data_info import Data1D
from sasdata.dataloader.loader import Loader

from src.sas.sascalc.size_distribution.SizeDistribution import sizeDistribution


def find(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


@pytest.fixture(autouse=True)
def data1():
    data = Loader().load(find("Alumina_usaxs_irena_input.csv"))[0]

    size_distribution = sizeDistribution(data)
    size_distribution.aspectRatio = 1.0
    size_distribution.diamMin = 25
    size_distribution.diamMax = 10000
    size_distribution.nbins = 100
    size_distribution.logbin = True
    size_distribution.skyBackground = 1.94434e-5
    size_distribution.weightType = 'dI'
    size_distribution.weightFactor = 1.9033
    size_distribution.iterMax = 100
    size_distribution.ndx_qmin = 13
    size_distribution.ndx_qmax = 94

    return size_distribution

def fetch_answer():
    bins = np.array([])
    mags = np.array([])

    with open(find("AluminaUSAXS_IrenaTenShotsResults.csv")) as fp:
        spamreader = csv.reader(fp, delimiter=",")

        for row in spamreader:
            try:
                bins = np.append(bins, float(row[0]))
                mags = np.append(mags, float(row[4]))
            except:
                pass
    return bins, mags

def test_noRes(data1):
    # Subtract a (low Q) power law background. Power = 4 and scale =2.5508e-7
    y_power_back = 2.5508e-7 * data1.data.x ** -4
    # Subtract falt background (high Q - e.g. incoherent scattering) background = 0.121176
    y_flat = np.ones(len(data1.data.x))*.121176
    # Now compute full background to subtract from the data
    y_back = y_power_back + y_flat
    data_to_subtract = Data1D(data1.data.x, y_back, dy=0)
    trim_data, intensities, init_binsBack, sigma = data1.prep_maxEnt(data_to_subtract, full_fit=True, rngseed=0)
    # Now run the fit.
    # The return is a list over the number of runs (only one for quick fit and 10 for a full fit
    # each element of the list is a list containing the convergence truth and the number of
    # iterations it took to converge.
    convergence = data1.run_maxEnt(trim_data, intensities, init_binsBack, sigma)
    # Now retrieve the "ground truth" to compare to.
    answerBins, answerMags = fetch_answer()
    # TODO: Need to understand how IRENA is reporting bins. It seems to be using bin 1 and last as the
    #       values input from the user while we are starting from the midpoint of what should be the
    #       the first bin if the min diameter is the bottom edge of the bin.
    assert convergence[0][0] is True
    assert data1.MaxEnt_statistics['volume'] == pytest.approx(4.84, abs=0.02)
    assert data1.BinMagnitude_maxEnt == pytest.approx(answerMags, abs=1e-3)


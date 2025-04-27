import os
import pytest
import csv
import numpy as np
from sasdata.dataloader.loader import Loader
from sasdata.dataloader.data_info import Data1D
from src.sas.sascalc.poresize.SizeDistribution import sizeDistribution


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
    size_distribution.skyBackground = 1e-3
    size_distribution.weightType = 'dI'
    size_distribution.weightFactor = 2.0
    size_distribution.iterMax = 100
#    size_distribution.ndx_qmin = 25
#    size_distribution.ndx_qmax = 94

    return size_distribution

def fetch_answer():
    bins = np.array([])
    mags = np.array([])

    with open(find("Alumina_usaxs_irena_diameter_fit.csv")) as fp:
        spamreader = csv.reader(fp, delimiter=",")

        for row in spamreader:
            try:
                bins = np.append(bins, float(row[0]))
                mags = np.append(mags, float(row[4]))
            except:
                pass
    return bins, mags

def test_noRes(data1):
    data_background = np.ones(len(data1.data.y)) * 0.120605
    subtracted_data = Data1D(data1.data.x, data_background, dy = data_background * 0.001, lam=None, dlam=None, isSesans=False)
    trim_data, intensities, init_binsBack, sigma = data1.prep_maxEnt(subtracted_data, full_fit=False, rngseed=0)
    convergence = data1.run_maxEnt(trim_data, intensities, init_binsBack, sigma)
    answerBins, answerMags = fetch_answer()
    # TODO: Need to understand how IRENA is reporting bins. It seems to be using bin 1 and last as the
    #       values input from the user while we are starting from the midpoint of what should be the
    #       the first bin if the min diameter is the bottom edge of the bin.
    assert data1.bins * 2 == pytest.approx(answerBins, rel=1e-1)
    # TODO: need to get a results file from IRENA from a KNOWN set of parameters, preferably that converge quickly
    #assert convergence == True
    #assert data1.BinMagnitude_maxEnt == pytest.approx(answerMags, rel=1e3)

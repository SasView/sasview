import os
import pytest
import csv
import numpy as np
from sasdata.dataloader.data_info import Data1D
from src.sas.sascalc.poresize.SizeDistribution import sizeDistribution


def find(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


@pytest.fixture(autouse=True)
def data1():
    load_data = np.loadtxt(find("Alumina_usaxs_irena_input.csv"), dtype=np.float64, delimiter=",")
    x = load_data[:,0]
    y = load_data[:,1]
    dy = load_data[:,2]
    data = Data1D(x,y,dy=dy, dx = None, lam=None, dlam=None, isSesans=False)

    size_distribution = sizeDistribution(data)
    size_distribution.aspectRatio = 1.0
    size_distribution.diamMin = 25
    size_distribution.diamMax = 10000
    size_distribution.nbins = 100
    size_distribution.logbin = True
    size_distribution.skyBackground = 1e-3
    size_distribution.weightType = 'dI'
    size_distribution.weightFactor = 2.0
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
                mags = np.append(mags, float(row[2]))
            except:
                pass
    return bins, mags

def test_noRes(data1):
    data_background = np.ones(len(data1.data.y)) * 0.120605
    subtracted_data = Data1D(data1.data.x, data_background, dy = data_background * 0.001, lam=None, dlam=None, isSesans=False)
    trim_data, intensities, init_binsBack, sigma = data1.prep_maxEnt(subtracted_data, full_fit=True, rngseed=0)
    _, Bins, _, BinMag, _, _ = data1.run_maxEnt(trim_data, intensities, init_binsBack, sigma)
    answerBins, answerMags = fetch_answer()
    assert Bins == pytest.approx(answerBins, rel=100)
    assert BinMag == pytest.approx(answerMags, rel=100)

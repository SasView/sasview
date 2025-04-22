import os
import pytest
import csv
import numpy as np
from sasmodels import resolution as rst
from sasdata.dataloader.data_info import Data1D
from sasdata.dataloader.loader import Loader
from src.sas.sascalc.poresize.SizeDistribution import sizeDistribution


def find(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


#class SizeDistributionTest:
@pytest.fixture(autouse=True)
def data1():
#        class StartTest:
#        def __init__(self, filename, answerFile):
#            self.fileName = filename
#            self.answer = answerFile
    data_from_loader = Loader().load(find("Alumina_usaxs_irena_Iq_fit.csv"))
    data = data_from_loader[0]
    size_distribution = sizeDistribution(data)
    size_distribution.aspectRatio = 1.0
    size_distribution.diamMin = 25
    size_distribution.diamMax = 10000
    size_distribution.nbins = 100
    size_distribution.logbin = True
    size_distribution.skyBackground = 1e-3
    size_distribution.weightType = 'dI'
    size_distribution.weightFactor = 1.0

    return size_distribution
#            def file_to_input(self):
"""
                Q = np.array([])
                I = np.array([])
                dI = np.array([])

                with open(self.fileName) as fp:
                    spamreader = csv.reader(fp, delimiter=",")

                    for row in spamreader:
                        try:
                            Q = np.append(Q, float(row[0]))
                            I = np.append(I, float(row[1]))
                            dI = np.append(dI, float(row[2]))
                        except:
                            pass

                data_from_loader = data_info.Data1D(
                    x=Q, y=I, dx=None, dy=dI, lam=None, dlam=None, isSesans=False
                )
                data_from_loader.filename = "mock data"

                # Contrust the input dictionary
                input_dict = {}
                input_dict["Filename"] = data_from_loader.filename
                input_dict["Data"] = [data_from_loader.x, data_from_loader.y]
                Qmin = min(data_from_loader.x)
                Qmax = max(data_from_loader.x)
                input_dict["Limits"] = [Qmin, Qmax]
                input_dict["Scale"] = 1
                input_dict["Logbin"] = True
                input_dict["DiamRange"] = diamRange
                input_dict["WeightFactors"] = np.ones(len(data_from_loader.y))
                input_dict["Contrast"] = contrast
                input_dict["Sky"] = sky
                if weightsOpt == "dI":
                    input_dict["Weights"] = 1 / (dI * dI)
                elif weightsOpt == "I":
                    input_dict["Weights"] = 1 / (I * I)
                input_dict["Background"] = np.ones(len(data_from_loader.y)) * 0.120605
                input_dict["Model"] = "Sphere"
                perfect1D = rst.Perfect1D(data_from_loader.x)
                qlength, qwidth = 0.117, None
                Ibeg = np.searchsorted(Q, Qmin)
                Ifin = np.searchsorted(Q, Qmax) + 1
                slit = None
                if resOpt != None:
                    if resOpt == "slit1D":
                        slit = rst.Slit1D(
                            Q[Ibeg:Ifin],
                            q_length=qlength,
                            q_width=qwidth,
                            q_calc=Q[Ibeg:Ifin],
                        )
                input_dict["Resolution"] = perfect1D
                return input_dict, slit
                """
def fetch_answer(self):
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

#        filename1 = find("Alumina_usaxs_irena_Iq_fit.csv")
#        answer1 = find("Alumina_usaxs_irena_diameter_fit.csv")
#        return StartTest(filename1, answer1)

def test_noRes(data1):
#        input_dict, slit = data1.file_to_input(diamRange=[25, 10000, 100])
#    _, Bins, _, BinMag, _, _ = sizeDistribution(input_dict)
#   Do we need to subtract background here?
    print (type(data1))
    subtracted_data = data1.data
    trim_data, intensities, init_binsBack, sigma = data1.prep_maxEnt(subtracted_data, full_fit=True)
    _, Bins, _, BinMag, _, _ = data1.run_maxEnt(trim_data, intensities,init_binsBack, sigma)
    answerBins, answerMags = fetch_answer()
    assert Bins == pytest.approx(answerBins, rel=100)
    assert BinMag == pytest.approx(answerMags, rel=100)

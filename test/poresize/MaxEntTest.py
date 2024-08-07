import pytest
from maxEnt_method import sizeDistribution
import unittest
import csv
import numpy as np
from sasmodels import resolution as rst
from sasdata.dataloader import data_info

class SizeDistributionTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    class StartTest:
        def __init__(self,filename,answerFile):
            self.fileName = filename
            self.answer = answerFile
            
        def file_to_input(self,diamRange,logBin=True,contrast=1,sky=1e-3,weightsOpt="dI",resOpt=None):
            Q = np.array([])
            I = np.array([])
            dI = np.array([])

            with open(self.fileName) as fp:
                spamreader = csv.reader(fp, delimiter=',')

                for row in spamreader:
                    try:
                        Q = np.append(Q, float(row[0]))
                        I = np.append(I, float(row[1]))
                        dI = np.append(dI, float(row[2]))
                    except:
                        pass
                    
            data_from_loader = data_info.Data1D(x=Q, y=I, dx=None, dy=dI,lam=None, dlam=None, isSesans=False)
            data_from_loader.filename = "mock data"

            # Contrust the input dictionary
            input = {}
            input["Filename"] = data_from_loader.filename
            input["Data"] = [data_from_loader.x,data_from_loader.y]
            Qmin = min(data_from_loader.x)
            Qmax = max(data_from_loader.x)
            input["Limits"] = [Qmin, Qmax]
            input["Scale"] = 1
            input["Logbin"] = True
            input["DiamRange"] = diamRange
            input["WeightFactors"] = np.ones(len(data_from_loader.y))
            input["Contrast"] = contrast
            input["Sky"] = sky
            if weightsOpt == "dI":
                input["Weights"] = 1/(dI*dI)
            elif weightsOpt == "I":
                input["Weights"] = 1/(I*I)
            input["Background"] = np.ones(len(data_from_loader.y))*0.120605
            input["Model"] = 'Sphere'
            perfect1D = rst.Perfect1D(data_from_loader.x) 
            qlength, qwidth = 0.117, None 
            Ibeg = np.searchsorted(Q,Qmin)
            Ifin = np.searchsorted(Q,Qmax)+1
            slit = None
            if resOpt != None:
                if resOpt == "slit1D":
                    slit = rst.Slit1D(Q[Ibeg:Ifin],q_length=qlength,q_width=qwidth,q_calc=Q[Ibeg:Ifin])
            input["Resolution"] = perfect1D
            return input,slit
        
        def fetch_answer(self):
            bins = np.array([])
            mags = np.array([])
            
            with open(self.answer) as fp:
                spamreader = csv.reader(fp, delimiter=',')

                for row in spamreader:
                    try:
                        bins = np.append(bins, float(row[0]))
                        mags = np.append(mags, float(row[1]))
                    except:
                        pass
            return bins,mags
    
    filename1 = 'test_data/Alumina_usaxs_irena_Iq_fit.csv'
    answer1 = 'test_data/Alumina_usaxs_irena_diameter_fit.csv'
    data1 = StartTest(filename1,answer1)

    def test_noRes(self,data1):
        data1.file_to_input(diamRange=[25,10000,100])
        _,Bins,_,BinMag,_,_ = sizeDistribution(input)
        answerBins,answerMags = data1.fetch_answer()
        assert pytest.approx(Bins,answerBins,rel=100)
        assert pytest.approx(BinMag,answerMags,rel=100)
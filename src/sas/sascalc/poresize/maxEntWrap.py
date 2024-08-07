from maxEnt_method import SizeDistribution
import csv
import numpy as np
import matplotlib.pyplot as plt

fileName = "I_for_dist1.txt"
#if fileName[:-3] == "ses" or fileName[:-5] == "sesans":

Q = np.array([])
I = np.array([])
dI = np.array([])

# read data
with open(fileName) as fp:
    spamreader = csv.reader(fp, delimiter=' ')
    for row in spamreader:
        try:
            Q = np.append(Q, float(row[0]))
            I = np.append(I, float(row[1]))
            dI = np.append(dI, float(row[2]))
        except:
            pass

#print(I)
#print(Q)
# consisting Q, I, wt (weight of point in fitting), Ic (IDK and not used), Ib (IDK and not used)
Profile = [Q, I, dI, I, I]
Limits = [None, [5.237261180003165e-04, 5.000000000000000e-01]]
ProfDict = {'wtFactor':1.}
Sample = {'Contrast':[None, 1],
        'Scale':[1.]
        }

Data = {
    "Size":{
        "Shape":["Sphere"],
        "logBins":False,        #Flag for logBin
        "MinDiam":1,            #Max diameter
        "MaxDiam":24000,        #Min diameter
        "Nbins":200,            #number of bins
        "MaxEnt":{"Sky":0.,     #Entropy background
            "Niter":5000},      #number of iterations
        "Method": "MaxEnt"      #flag for opt method,
    },
    "Back":np.array([0] * len(I)),  # background to subtract from I(Q)
    }

# Call the function
SizeDistribution(Profile,ProfDict,Limits,Sample,Data)

print(Data["Size"]["Distribution"])

rst = Data["Size"]["Distribution"]
plt.figure(figsize=(8, 6))  # Width=8 inches, height=6 inches

plt.scatter(rst[0], rst[2])
plt.title("Max Ent")

# read and compare to the answers
bin = np.array([])
per = np.array([])

with open("dist1.txt") as fp:
    spamreader = csv.reader(fp, delimiter=' ')
    for row in spamreader:
        try:
            bin = np.append(bin, float(row[0]))
            per = np.append(per, float(row[1]))
        except:
            pass
plt.figure(figsize=(8, 6))  # Width=8 inches, height=6 inches

plt.scatter(bin, per)

plt.title("Fake")


#plt.show()

plt.figure(figsize=(8,6))
plt.scatter(rst[0], rst[2], label="Max Ent")
plt.scatter(bin * 100., per / 10, label="Fake")
plt.xlabel("Ang")
plt.ylabel("Percentage")

plt.legend()  # Display the legend

plt.show()

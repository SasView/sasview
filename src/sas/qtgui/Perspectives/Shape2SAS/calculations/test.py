
from helpfunctions import GenerateAllPoints
from Shape2SAS import getPointDistribution, ModelProfile
import matplotlib.pyplot as plt
import numpy as np


subunits = ["Sphere", "cylinder"]
com = [[0, 0, 0], [50, 0, 0]]
dimensions = [[30], [20, 100]]
rotation_points = [[0, 0, 0], [0, 0, 0]]
rotation = [[0, 0, 0], [0, 90, 0]]
p = [1, 1]
exclude_overlap = True

points = GenerateAllPoints(3000, com, subunits, dimensions, rotation, p, exclude_overlap).onGeneratingAllPointsSeparately()

x = points[0]
y = points[1]
z = points[2]

x = np.concatenate(x)
y = np.concatenate(y)
z = np.concatenate(z)

fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
ax.scatter(x, y, z, s=1)
plt.show()
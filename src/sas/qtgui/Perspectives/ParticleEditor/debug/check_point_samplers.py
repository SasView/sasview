import matplotlib.pyplot as plt

from sas.qtgui.Perspectives.ParticleEditor.sampling.points import Grid

fig = plt.figure("Grid plot")
ax = fig.add_subplot(projection='3d')

gen = Grid(100, 250)

n_total = gen.n_points

x,y,z = gen.generate(0, n_total//3)
ax.scatter(x,y,z,color='b')

x,y,z = gen.generate(n_total//3, n_total)
ax.scatter(x,y,z,color='r')

plt.show()

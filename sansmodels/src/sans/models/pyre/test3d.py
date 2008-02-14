import matplotlib.pylab as pylab
import matplotlib.axes3d as axes3d
from matplotlib.axes3d import Axes3D

# Read this: http://www.scipy.org/Cookbook/Matplotlib/mplot3D

import random
import numpy as npy



def test_scatter():

    fig=pylab.figure()
    ax = Axes3D(fig)
    #
    #
    n = 100
    for c,zl,zh in [('r',-50,-25),('b',-30,-5)]:
        xs,ys,zs = zip(*
                       [(random.randrange(23,32),
                         random.randrange(100),
                         random.randrange(zl,zh)
                         ) for i in range(n)])
        ax.scatter3D(xs,ys,zs, c=c)
    #
    ax.set_xlabel('------------ X Label --------------------')
    ax.set_ylabel('------------ Y Label --------------------')
    ax.set_zlabel('------------ Z Label --------------------')

def get_test_data(delta=0.05):
    from matplotlib.mlab import meshgrid, bivariate_normal
    x = y = npy.arange(-3.0, 3.0, delta)
    X, Y = meshgrid(x,y)

    Z1 = bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
    Z2 = bivariate_normal(X, Y, 1.5, 0.5, 1, 1)
    Z = Z2-Z1

    X = X * 10
    Y = Y * 10
    Z = Z * 500
    return X,Y,Z

def test_wire():
    fig=pylab.figure()
    ax = Axes3D(fig)

    X,Y,Z = get_test_data(0.05)
    ax.plot_wireframe(X,Y,Z, rstride=10,cstride=10)
    #
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

def test_surface():
    fig=pylab.figure()
    ax = Axes3D(fig)

    X,Y,Z = get_test_data(0.05)
    ax.plot_surface(X,Y,Z, rstride=10,cstride=10)
    #
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')


def test_contour():
    fig=pylab.figure()
    ax = Axes3D(fig)

    X,Y,Z = get_test_data(0.05)
    cset = ax.contour3D(X,Y,Z)
    ax.clabel(cset, fontsize=9, inline=1)
    #
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

def test_plot():
    fig=pylab.figure()
    ax = Axes3D(fig)
    xs = npy.arange(0,4*npy.pi+0.1,0.1)
    ys = npy.sin(xs)
    ax.plot(xs,ys, label='zl')
    ax.plot(xs,ys+max(xs),label='zh')
    ax.plot(xs,ys,dir='x', label='xl')
    ax.plot(xs,ys,dir='x', z=max(xs),label='xh')
    ax.plot(xs,ys,dir='y', label='yl')
    ax.plot(xs,ys,dir='y', z=max(xs), label='yh')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()


def test_polys():
    from matplotlib.collections import LineCollection, PolyCollection
    from matplotlib.colors import colorConverter

    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)

    fig=pylab.figure()
    ax = Axes3D(fig)
    xs = npy.arange(0,10,0.4)
    verts = []
    zs = [0.0,1.0,2.0,3.0]
    for z in zs:
        ys = [random.random() for x in xs]
        ys[0],ys[-1] = 0,0
        verts.append(zip(xs,ys))

    poly = PolyCollection(verts, facecolors = [cc('r'),cc('g'),cc('b'),
                                               cc('y')])
    #patches = art3d.Poly3DCollectionW(poly, zs=zs, dir='y')
    #poly = PolyCollection(verts)
    ax.add_collection(poly,zs=zs,dir='y')
    #ax.wrapped.add_collection(poly)
    #
    ax.plot(xs,ys, z=z, dir='y', c='r')
    ax.set_xlim(0,10)
    ax.set_ylim(-1,4)
    ax.set_zlim(0,1)

def test_scatter2D():
    xs = [random.random() for i in range(20)]
    ys = [random.random() for x in xs]
    fig=pylab.figure()
    ax = Axes3D(fig)
    ax.scatter(xs,ys)
    ax.scatter(xs,ys, dir='y', c='r')
    ax.scatter(xs,ys, dir='x', c='g')

def test_bar2D():
    fig=pylab.figure()
    ax = Axes3D(fig)

    for c,z in zip(['r','g','b','y'],[30,20,10,0]):
        xs = npy.arange(20)
        ys = [random.random() for x in xs]
        ax.bar(xs,ys,z=z,dir='y',color=c)
    #ax.plot(xs,ys)

if __name__ == "__main__":
    
    #test_scatter()
    test_wire()
    #test_surface()
    #test_contour()
    #test_plot()
    #test_polys()
    #test_scatter2D()
    #test_bar2D()
    pylab.show()
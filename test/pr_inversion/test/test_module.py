from sans.pr.core.pr_inversion import Cinvertor
import numpy

c = Cinvertor()
print c.__class__.__name__


x = numpy.ones(3)
print x.__class__.__name__
print c.set_x(x)
print c.set_y(x)
print c.set_err(x)
print c.is_valid()
print c.set_dmax(60.0)
p = numpy.ones(1)
print c.residuals(p)



v = numpy.zeros(0)
v = numpy.append(v, 1.0)
v = numpy.append(v, 2.0)
print v[0], v[1]
print len(v)


print numpy.ndarray.
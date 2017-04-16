import math

# log(x) 
def from_log10(x, y=0):
    return math.pow(10.0, x)
def err_log10(x, y, dx, dy):
    return math.pow(10.0, x)*dx

# ln(x) 
def from_lnx(x, y=0):
    return math.exp(x)
def err_lnx(x, y, dx, dy):
    return math.exp(x)*dx

# x^2
def from_x2(x, y=0):
    return math.sqrt(x)
def err_x2(x, y, dx, dy):
    return 0.5*dx/math.sqrt(x)

# 1/x
def from_inv_x(x, y=0):
    return 1.0/x
def err_inv_x(x, y, dx, dy):
    return 1.0/(x**2)*dx

# 1/sqrt(y)
def from_inv_sqrtx(x, y=0):
    return 1.0/x**2
def err_inv_sqrtx(x, y, dx, dy):
    return 2.0*math.pow(x,-3.0)*dx

# ln(xy)
def from_lnxy(x, y):
    return math.exp(x)/y
def err_lnxy(x, y, dx, dy):
    return math.exp(x)/y*dx

# ln(xy2)
def from_lnx2y(x, y):
    return math.exp(x)/y**2
def err_lnx2y(x, y, dx, dy):
    return math.exp(x)/y**2*dx

# ln(xy4)
def from_lnx4y(x, y):
    return math.exp(x)/y**4
def err_lnx4y(x, y, dx, dy):
    return math.exp(x)/y**4*dx


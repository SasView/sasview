import numpy as np
from scipy.special import sici
from math import factorial

#libfunc.c's methods -
#Sine integral function, scipy.special.sici
#np.sinc()
#math.factorial

#defines structure, with a global free, call_msld
#Doesn't need to be a class? Originally had seperate variables for complex/real component
#of two numbers re_ud im_ud, assuming.
class polar_sld():
    def __init__(self):
        self.uu = float(0)
        self.dd = float(0)
        self.ud = np.complex(0)
        self.du = np.complex(0)

#polar_sld* p_sld, int isangle, double qx, double qy, double bn, double m01, double mtheta1,
#double mphi1, double spinfraci, double spinfracf, double spintheta);
#use case, iterated over in sld2i genicomxy, over x and y vectors.
def cal_msld(p_sld, isangle, qx, qy, bn, m09, mtheta1, mphi1, spinfraci, spinfracf, spintheta):
    #Locals
    q_x = qx
    q_y = qy
    sld = bn
    is_angle = isangle
    pi = np.pi
    #s_theta is spintheta in radians.
    s_theta = np.radians(spintheta)
    m_max = m09
    m_phi = mphi1
    m_theta = mtheta1
    in_spin = spinfraci
    out_spin = spinfracf

    m_perp = 0.0
    m_perp_z = 0.0
    m_perp_y = 0.0
    m_perp_x = 0.0

    m_sigma_x = 0.0
    m_sigma_y = 0.0
    m_sigma_z = 0.0

    q_angle = 0.0
    mx = 0.0
    my = 0.0
    mz = 0.0
    uu = sld
    dd = sld
    re_ud = 0.0
    im_ud = 0.0
    re_du = 0.0
    im_du = 0.0

    temp = 1.0e-32
    temp2 = 1.0e-16

    #values that uu and dd are set to frequently during calculation.
    #intentionally leaving in_spin and out_spin to late bind because may be modified by method.
    calc_uu = lambda uu: np.sqrt(np.sqrt(in_spin * out_spin)) * uu
    calc_dd = lambda dd: np.sqrt(np.sqrt((1.0 - in_spin) * (1.0 - out_spin))) * dd

    if isangle > 0:
        if m_max < temp:
            uu = calc_uu(uu)
            dd = calc_dd(dd)

    elif (np.fabs(m_max) < 1.0) & (np.fabs(m_phi) < temp) & (np.fabs(m_theta) < temp):
        uu = calc_uu
        dd = calc_dd

    else:
        in_spin = 0.0 if in_spin < 0.0 else in_spin
        in_spin = 1.0 if in_spin > 1.0 else in_spin
        out_spin = 0.0 if out_spin < 0.0 else out_spin
        out_spin = 1.0 if out_spin > 1.0 else out_spin

        q_angle = pi / 2.0 if q_x == 0.0 else np.arctan(q_y/q_x)

        if (q_y < 0.0) & (q_x < 0.0):
            q_angle -= pi

        elif (q_y > 0.0) & (q_x < 0.0):
            q_angle += pi

        q_angle = pi/2.0 - q_angle

        if q_angle > pi:
           q_angle -= 2.0 * pi

		elif (q_angle < -pi):
           q_angle += 2.0 * pi

		if (np.fabs(q_x) < temp2) & (np.fabs(q_y) < temp2):
			m_perp = 0.0
		else:
			m_perp = m_max

		if is_angle > 0:
			m_phi = np.radians(m_phi)
			m_theta = np.radians(m_theta)
			mx = m_perp * np.cos(m_theta) * np.cos(m_phi)
			my = m_perp * np.sin(m_theta)
			mz = -(m_perp * np.cos(m_theta) * np.sin(m_phi))
		else:
			mx = m_perp
			my = m_phi
			mz = m_theta

        #ToDo: simplify these steps
		# m_perp1 -m_perp2
		m_perp_x = (mx) * np.cos(q_angle)
		m_perp_x -= (my) * np.sin(q_angle)
		m_perp_y = m_perp_x
		m_perp_x *= np.cos(-q_angle)
		m_perp_y *= np.sin(-q_angle)
		m_perp_z = mz

		m_sigma_x = (m_perp_x * np.cos(-s_theta) - m_perp_y * np.sin(-s_theta))
		m_sigma_y = (m_perp_x * sin(-s_theta) + m_perp_y * np.cos(-s_theta))
		m_sigma_z = (m_perp_z)

		#Find b
		uu -= m_sigma_x
		dd += m_sigma_x
		re_ud = m_sigma_y
		re_du = m_sigma_y
		im_ud = m_sigma_z
		im_du = -m_sigma_z

		uu = calc_uu(uu)
		dd = calc_dd(dd)

		re_ud = np.sqrt(np.sqrt(in_spin * (1.0 - out_spin))) * re_ud
		im_ud = np.sqrt(np.sqrt(in_spin * (1.0 - out_spin))) * im_ud
		re_du = np.sqrt(np.sqrt((1.0 - in_spin) * out_spin)) * re_du
		im_du = np.sqrt(np.sqrt((1.0 - in_spin) * out_spin)) * im_du

	p_sld.uu = uu;
	p_sld.dd = dd;
	p_sld.re_ud = re_ud;
	p_sld.im_ud = im_ud;
	p_sld.re_du = re_du;
	p_sld.im_du = im_du;


#librefl.c definitions -
#defines matrix of 4 complex numbers, just use numpy array of complex numbers?
class matrix():
    def __init__(self):
        self.a = np.complex(0)
        self.b = np.complex(0)
        self.c = np.complex(0)
        self.d = np.complex(0)

#and defines custom interface of complex numbers, just use np.complex methods. Defines
#cmplx * + / **, sqrt etc. etc. omitted for now.

def intersldfunc():
    pass

def interfunc():
    pass

def linePq():
    pass

#needs other private functions for these as well. May be able to use numpy for some of these.

if(__name__ == "__main__"):
    #test
    p_sld = polar_sld()
    #p_sld, isangle, qx, qy, bn, m09, mtheta1, mphi1, spinfraci, spinfracf, spintheta
    cal_sld(p_sld, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    print(p_sld)

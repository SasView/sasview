import logging

import numpy as np
from scipy.special import sici
from math import factorial

logger = logging.getLogger(__name__)

#libfunc.c's methods -
#Sine integral function, scipy.special.sici
#np.sinc()
#math.factorial
#libfunc.c, converted.

#defines structure, with a global free, call_msld
#Doesn't need to be a class? Originally had seperate variables for complex/real component
#of two numbers re_ud im_ud, assuming.
class polar_sld():
    def __init__(self):
        self.uu = float(0)
        self.dd = float(0)
        self.ud = np.complex(0)
        self.du = np.complex(0)

    def __str__(self):
        desc = ""
        desc += "uu: " + str(self.uu) + "\n"
        desc += "dd: " + str(self.dd) + "\n"
        desc += "ud: " + str(self.ud) + "\n"
        desc += "du: " + str(self.du)
        return desc

    #polar_sld* p_sld, int isangle, double qx, double qy, double bn, double m01, double mtheta1,
    #double mphi1, double spinfraci, double spinfracf, double spintheta);
    #use case, iterated over in sld2i genicomxy, over x and y vectors.
    #Operates on p_sld, global free, only, so in polar_sld class?
    def cal_msld(self, isangle, qx, qy, bn, m01, mtheta1, mphi1, spinfraci, spinfracf, spintheta):
        """
        calculate magnetic sld and return total sld.
        Note: all angles are in degrees.

        :param bn: Contrast (not just sld of the layer)
        :param m01: Max mag of M.
        :param mtheta1: angle from x-z plane.
        :param mph1i: Angle (anti-clock-wise)of x-z projection(M) from x axis.
        :param spinfraci1: The fraction of UP among UP+Down (before sample).
        :param spinfracf: The fraction of UP among UP+Down (after sample and before detector).
        :param spintheta: Angle (anti-clock-wise) between neutron spin(up) and x axis.
        """

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

            elif q_angle < -pi:
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
            m_sigma_y = (m_perp_x * np.sin(-s_theta) + m_perp_y * np.cos(-s_theta))
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

        self.uu = uu
        self.dd = dd
        self.re_ud = re_ud
        self.im_ud = im_ud
        self.re_du = re_du
        self.im_du = im_du




#librefl.c definitions -
#defines matrix of 4 complex numbers, just use numpy array of complex numbers?
class matrix():
    def __init__(self):
        self.a = np.complex(0)
        self.b = np.complex(0)
        self.c = np.complex(0)
        self.d = np.complex(0)

#Private methods implementation -

def p_gamma(a, x, loggamma_a):
    """
    Incomplete gamma function.
    1/ Gamma(a) * Int_0^x exp(-t) t^(a-1) dt
    """
    k = 0
    result, term, previous = 0.0, 0.0, 0.0

    if x >= 1 + a:
        return 1 - q_gamma(a, x, loggamma_a)
    if x == 0:
        return 0

    term = np.exp(a * np.log(x) - x - loggamma_a) / a
    result = term
    k_r = np.arange(1, 1000)

    terms = x / (a + k_r)


    for k in terms:
        term *= k
        result += term
        previous = result

        if(result == previous):
            return result

    logger.error("p_gamma() could not converge.")
    return result

def q_gamma(a, x, loggamma_a)
    k = 0
    result, w, temp, previous = 0.0, 0.0, 0.0, 0.0

    if x >= (1 + a):
        return 1 - p_gamma(a, x, loggamma_a)
    w = np.exp(a * np.log(x) - x - loggamma_a)
    result = w / lb

    k_r = np.arange(2, 1000)

    for k in k_r:
        temp = ((k - 1 - a) * (lb - la) + (k + x) * lb) / k
        lb = temp
        la = lb
        w *= (k - 1 - a) / k
        temp = w / (la * lb)
        result += temp
        previous = result
        if result == previous:
            return result

    logger.error("q_gamma() could not converge.")
    return result

def erf(x):
    _log_pi_over_2 = np.log(np.pi) / 2

    if !np.isfinite(x):
        if np.isnan(x):
            return x
    if x >= 0:
        return p_gamma(0.5, x ** 2, _log_pi_over_2)
    else:
        return -p_gamma(0.5, x ** 2, _log_pi_over_2)

def erfc(x):
    _log_pi_over_2 = np.log(np.pi) / 2




#and defines custom interface of complex numbers, just use np.complex methods. Defines
#cmplx * + / **, sqrt etc. etc. omitted for now.
#int fun_type, double n_sub, double i, double nu, double sld_l, double sld_r
def intersldfunc(fun_type, n_sub, i, nu, sld_l, sld_r):
    pass

#int fun_type, double n_sub, double i, double sld_l, double sld_r
def interfunc(fun_type, n_sub, i, sld_l, sld_r):
    pass

#int fun_type, double thick, double sld_in, double sld_out,double r, double q
def linePq(fun_type, thick, sld_in, sld_out, r, q):
    pass

if(__name__ == "__main__"):
    #test
    p_sld = polar_sld()
    #p_sld, isangle, qx, qy, bn, m09, mtheta1, mphi1, spinfraci, spinfracf, spintheta
    cal_msld(p_sld, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1)

    print(p_sld)

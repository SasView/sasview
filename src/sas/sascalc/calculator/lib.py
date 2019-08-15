import logging

import numpy as np

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
        self.uu = float()
        self.dd = float()
        self.ud = np.complex()
        self.du = np.complex()

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
        m_max = m01
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

def q_gamma(a, x, loggamma_a):
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

    if not np.isfinite(x):
        if np.isnan(x):
            #erf(Nan) = Nan
            return x
        #erf(+-inf) = +-1.0
        return 1.0 if x > 0 else -1.0
    if x >= 0:
        return p_gamma(0.5, np.square(x), _log_pi_over_2)
    else:
        return -p_gamma(0.5, np.square(x), _log_pi_over_2)

def erfc(x):
    _log_pi_over_2 = np.log(np.pi) / 2
    if not np.isfinite(x):
        if np.isnan(x):
            #erfc(NaN) = Nan
            return x
        #erfc(+-inf) = 0.0, 2.0
        return 0.0 if x > 0 else 2.0
    if x >= 0:
        return q_gamma(0.5, np.square(x), _log_pi_over_2)

def err_mod_func(n_sub, ind, nu):
    """
    Normalized and modified erf
     |
   1 +                __  - - - -
     |             _
  	 |            _
     |        __
   0 + - - -
     |-------------+------------+--
     0           center       n_sub    --->
                                       ind
    :param n_sub: Total no. of bins(or sublayers).
    :param ind: x position- 0 to max.
    :param nu: Max x to integration.
    """
    center, func = 0.0, 0.0
    if nu == 0.0:
        nu = 1e-14
    if n_sub == 0.0:
        n_sub = 1.0

    #ind = (n_sub - 1.0)/2.0-1.0 + ind
    center = n_sub/2.0
    #transform it so that min(ind) = 0
    ind -= center
    #normalize by max limit
    ind /= center
    #divide by sqrt(2) to get Gaussian func
    nu /= np.sqrt(2.0)
    ind *= nu
    #re-scale and normalize it so that max(erf)=1, min(erf) = 0
    func = (erf(ind)/erf(nu)) / 2.0 #to show the ordering of operations clearer
    #shift it by +0.5 in y-direction so that min(erf) = 0
    func += 0.5

    return func

#Seems to be just ind * 1.0/n_sub where if n_sub = 0, +=1
#not sure why nu is being passed as a parameter.
def linearfunc(n_sub, ind, nu):
    bin_size, func = 0.0, 0.0

    if n_sub == 0.0:
        n_sub = 1.0

    #Size of each sub-layer.
    bin_size = 1.0 / n_sub
    #Rescale.
    ind *= bin_size
    func = ind

    return func

#Use the right hand side from the center of power func
#(ind * 1.0 / n_sub) ^ nu where if nu = 0 nu = 1e-14, n_sub+1 if 0.
def power_r(n_sub, ind, nu):
    bin_size, func = 0.0, 0.0

    if nu == 0.0:
        nu = 1e-14

    if n_sub == 0.0:
        n_sub = 1.0

    #Size of each sub-layer.
    bin_size = 1.0 / n_sub

    #Rescale.
    ind *= bin_size
    func = np.power(ind, nu)

    return func

#Use the left hand side from the center of power func.
#1.0 - (1.0 - (ind * 1.0 / n_sub)) ^ nu
def power_l(n_sub, ind, nu):
    bin_size, func = 0.0, 0.0

    if nu == 0.0:
        nu = 1e-14

    if n_sub == 0.0:
        n_sub = 1.0

    #Size of each sub-layer.
    bin_size = 1.0 / n_sub
    #Rescale.
    ind *= bin_size
    func = 1.0 - np.power((1.0 - ind), nu)

    return func

#Use 1-exp func from x=0 to x=1
#(1.0 - e^(-nu * (ind * 1.0/n_sub))) / (1.0 - e^(-nu))
def exp_r(n_sub, ind, nu):
    bin_size, func = 0.0, 0.0

    if nu == 0.0:
        nu = 1e-14
    if n_sub == 0.0:
        n_sub = 1.0

    #Size of each sub-layer.
    bin_size = 1.0 / n_sub
    #Rescale.
    ind *= bin_size
    #Modify func so that func(0) = 0 and func(max) = 1.
    func = 1.0 - np.exp(-nu * ind)
    #Normalize by its max.
    func /= 1.0 - np.exp(-nu)

    return func

#Use the left hand side mirror image of expr func
def exp_l(n_sub, ind, nu):
    bin_size, func = 0.0, 0.0

    if nu == 0.0:
        nu = 1e-14
    if n_sub == 0.0:
        n_sub = 1.0

    #Size of each sub-layer.
    bin_size = 1.0 / n_sub
    #Rescale.
    ind *= bin_size
    #Modify func.
    func = np.exp(-nu * (1.0 - ind)) - np.exp(-nu)
    #Normalize by its max.
    func /= (1.0 - exp(-nu))

    return func

#and defines custom interface of complex numbers, just use np.complex methods. Defines
#cmplx * + / **, sqrt etc. etc. omitted for now.
#int fun_type, double n_sub, double i, double nu, double sld_l, double sld_r
#To select function called, at nu = 0 (singular point), call line function.
def intersldfunc(fun_type, n_sub, i, nu, sld_l, sld_r):
    sld_i, func = 0.0, 0.0

    if nu == 0.0:
        nu = 1e-13

    if fun_type not in np.arange(1, 6):
        func = err_mod_func(n_sub, i, nu)
    else:
        func_select = {
            1: power_r(n_sub, i, nu),
            2: power_l(n_sub, i, nu),
            3: exp_r(n_sub, i, nu),
            4: exp_l(n_sub, i, nu),
            5: linearfunc(n_sub, i, nu),
        }
        func = func_select[fun_type]

    #compute sld
    if sld_r > sld_l:
        sld_i = (sld_r-sld_l) * func + sld_l

    elif sld_r < sld_l:
        func = 1.0 - func
        sld_i = (sld_l-sld_r) * func + sld_r

    else:
        sld_i = sld_r

    return sld_i

#int fun_type, double n_sub, double i, double sld_l, double sld_r
def interfunc(fun_type, n_sub, i, sld_l, sld_r):
    sld_i, func = 0.0, 0.0

    if fun_type == 0:
        func = err_mod_func(n_sub, i, 2.5)
    else:
        func = linearfunc(n_sub, i, 1.0)

    if sld_r > sld_l:
        sld_i = (sld_r-sld_l) * func + sld_l
    elif sld_r < sld_l:
        func = 1.0 - func
        sld_i = (sld_l-sld_r) * func + sld_r
    else:
        sld_i = sld_r

    return sld_i

#int fun_type, double thick, double sld_in, double sld_out,double r, double q
#Cannot find implementation in librefl.c or call in sld2i.c
#def linePq(fun_type, thick, sld_in, sld_out, r, q):
#    pass

if __name__ == "__main__":
    #test
    p_sld = polar_sld()
    #p_sld, isangle, qx, qy, bn, m01, mtheta1, mphi1, spinfraci, spinfracf, spintheta
    p_sld.cal_msld(0, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    print(p_sld)

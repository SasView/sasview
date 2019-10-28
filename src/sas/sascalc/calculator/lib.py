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
#Refractoring polar_sld as structured array, then pass in

#returns dtype of polar_sld_type.
def get_polar_sld_type():
    dtype = [('uu', 'f8'), ('dd', 'f8'), ('ud', 'complex_'), ('du', 'complex_')]
    return dtype

#cal_msld taking in vector of bn, m09, mtheta1, mphi1.
#also takes in structured array of polar_sld_type, polar_slds, assumes is of right type.
def cal_msld_vec(polar_slds, is_angle, q_x, q_y, sld, m_max, m_theta, m_phi, in_spin, out_spin, spintheta):
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
    #qx and qy loop invariant can be passed in full and calculated using 3d vector calculations.
    pi = np.pi
    #s_theta is spintheta in radians.
    s_theta = np.radians(spintheta)

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
    dd = np.copy(sld)
    re_ud = np.zeros(len(sld), dtype=np.complex_)
    im_ud = np.zeros(len(sld), dtype=np.complex_)
    re_du = np.zeros(len(sld), dtype=np.complex_)
    im_du = np.zeros(len(sld), dtype=np.complex_)

    temp = 1.0e-32
    temp2 = 1.0e-16

    #values that uu and dd are set to frequently during calculation.
    #intentionally leaving in_spin and out_spin to late bind because may be modified by method.
    calc_uu = lambda uu: np.sqrt(np.sqrt(in_spin * out_spin)) * uu
    calc_dd = lambda dd: np.sqrt(np.sqrt((1.0 - in_spin) * (1.0 - out_spin))) * dd

    #Accepting values, which is values where absolute values of m_max < 1.0, abs(m_phi) < tempand abs(m_theta) < temp

    index_m_max = np.fabs(m_max) < 1.0
    index_m_phi = np.fabs(m_phi) < temp
    index_m_theta = np.fabs(m_theta) < temp

    index_accept = np.array([x & y & z for (x, y, z) in zip(index_m_max, index_m_phi, index_m_theta)], dtype=np.bool)

    #only do the computation in elif if there if something in accept matrix otherwise will do regardless of other conditions.

    if is_angle > 0:
        index = m_max < temp
        #if m_max < temp:
        uu[index] = calc_uu(uu[index])
        dd[index] = calc_dd(dd[index])


    else:
        #if there is any in index_accept, then do this, just so won't do computation if isangle > 0.
        uu[index_accept] = calc_uu(uu[index_accept])
        dd[index_accept] = calc_dd(dd[index_accept])

        if ~index_accept.all():
            #Make a temporary index, of all that failed the condition to use for the remaining calculations.
            index_use = ~index_accept

            #vectors are - bn m01 mtheta1 mphi1 -> sld, m_max, m_phi, m_theta.
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
                m_perp = np.zeros(len(m_max[index_use]), dtype=float)
            else:
                m_perp = m_max[index_use]

            if is_angle > 0:
                m_phi[index_use] = np.radians(m_phi[index_use])
                m_theta[index_use] = np.radians(m_theta[index_use])
                mx = m_perp * np.cos(m_theta[index_use]) * np.cos(m_phi[index_use])
                my = m_perp * np.sin(m_theta[index_use])
                mz = -(m_perp * np.cos(m_theta[index_use]) * np.sin(m_phi[index_use]))
            else:
                mx = m_perp
                my = m_phi[index_use]
                mz = m_theta[index_use]

            #ToDo: simplify these steps
            # m_perp1 -m_perp2
            m_perp_x = mx * np.cos(q_angle)
            m_perp_x -= my * np.sin(q_angle)
            m_perp_y = m_perp_x
            m_perp_x *= np.cos(-q_angle)
            m_perp_y *= np.sin(-q_angle)
            m_perp_z = mz

            m_sigma_x = m_perp_x * np.cos(-s_theta) - m_perp_y * np.sin(-s_theta)
            m_sigma_y = m_perp_x * np.sin(-s_theta) + m_perp_y * np.cos(-s_theta)
            m_sigma_z = m_perp_z

            #Find b
            uu[index_use] -= m_sigma_x
            dd[index_use] += m_sigma_x
            re_ud[index_use] = m_sigma_y
            re_du[index_use] = m_sigma_y
            im_ud[index_use] = m_sigma_z
            im_du[index_use] = -m_sigma_z

            uu[index_use] = calc_uu(uu[index_use])
            dd[index_use] = calc_dd(dd[index_use])

            re_ud[index_use] = np.sqrt(np.sqrt(in_spin * (1.0 - out_spin))) * re_ud[index_use]
            im_ud[index_use] = np.sqrt(np.sqrt(in_spin * (1.0 - out_spin))) * im_ud[index_use]
            re_du[index_use] = np.sqrt(np.sqrt((1.0 - in_spin) * out_spin)) * re_du[index_use]
            im_du[index_use] = np.sqrt(np.sqrt((1.0 - in_spin) * out_spin)) * im_du[index_use]

    polar_slds['uu'] = uu
    polar_slds['dd'] = dd

    #generate all complex numbers into new array, combining real and imaginary components calculated.
    #only way can find so far of doing this.
    _ud = np.zeros(len(re_ud), dtype=np.complex_)
    _du = np.zeros(len(re_du), dtype=np.complex_)

    for i in range(len(_ud)):
        _udt = np.complex(re_ud[i], im_ud[i])
        _dut = np.complex(re_du[i], im_du[i])
        _ud[i] = _udt
        _du[i] = _dut

    #new ud.
    polar_slds['ud'] = _ud
    #new du.
    polar_slds['du'] = _du

    #return uu, re_ud + 1j*im_ud, re_du + 1j*im_du, dd

#cal_msld taking in vector of bn, m09, mtheta1, mphi1.
#also takes in structured array of polar_sld_type, polar_slds, assumes is of right type.
#scalar version, which uses polar_sld as an array.
def cal_msld(polar_slds, is_angle, q_x, q_y, sld, m_max, m_theta, m_phi, in_spin, out_spin, spintheta):
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
    pi = np.pi
    #s_theta is spintheta in radians.
    s_theta = np.radians(spintheta)

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

    if is_angle > 0:
        if m_max < temp:
            uu = calc_uu(uu)
            dd = calc_dd(dd)

    elif (np.fabs(m_max) < 1.0) & (np.fabs(m_phi) < temp) & (np.fabs(m_theta) < temp):
        uu = calc_uu(uu)
        dd = calc_dd(dd)

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
        m_perp_x = mx * np.cos(q_angle)
        m_perp_x -= my * np.sin(q_angle)
        m_perp_y = m_perp_x
        m_perp_x *= np.cos(-q_angle)
        m_perp_y *= np.sin(-q_angle)
        m_perp_z = mz

        m_sigma_x = m_perp_x * np.cos(-s_theta) - m_perp_y * np.sin(-s_theta)
        m_sigma_y = m_perp_x * np.sin(-s_theta) + m_perp_y * np.cos(-s_theta)
        m_sigma_z = m_perp_z

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

    polar_slds[0]['uu'] = uu
    polar_slds[0]['dd'] = dd

    #new ud.
    _ud = np.complex(re_ud, im_ud)
    polar_slds[0]['ud'] = _ud

    #new du.
    _du = np.complex(re_du, im_du)
    polar_slds[0]['du'] = _du

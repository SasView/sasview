"""
Taken from sld2i_module and sld2i, definition of GenI
class, defined through structs and global free functions in C.

Depends on lib.py, implementation of libfunc.c and librefl.c
"""
from math import factorial

import numpy as np
from scipy.special import sici
import timeit

#from . import lib
import lib

class GenI():
    def __init__(self, is_avg, npix, x, y, z, sldn, mx, my, mz,
                 voli, in_spin, out_spin, s_theta):
        """
        Constructor for GenI
        :param qx: array of Qx values.
        :param qy: array of Qy values.
        :param qz: array of Qz values.
        :param x: array of x values.
        :param y: array of y values.
        :param z: array of z values.
        :param sldn: array of sld n.
        :param mx: array of sld mx.
        :param my: array of sld my.
        :param mz: array of sld mz.
        :param in_spin: ratio of up spin in Iin.
        :param out_spin: ratio of up spin in Iout.
        :param s_theta: angle (from x-axis) of the up spin in degrees.
        """
        self.is_avg = is_avg
        self.n_pix = npix
        self.x_val = x
        self.y_val = y
        self.z_val = z
        self.sldn_val = sldn
        self.mx_val = mx
        self.my_val = my
        self.mz_val = mz
        self.vol_pix = voli
        self.inspin = in_spin
        self.outspin = out_spin
        self.stheta = s_theta

    def genicomXY(self, qx, qy):
        """
        Compute 2d ansotropic.

        Returns I_out[] 1d array.
        """

        npoints = len(qx)

        #npoints is given negative for angular averaging
        #Assumes that q doesn't have qz component and sld_n is all real
        b_sld = lib.polar_sld()
        qr = float()
        iqr = np.complex()
        ephase = np.complex()
        comp_sld = np.complex()

        sumj_uu = np.complex()
        sumj_ud = np.complex()
        sumj_du = np.complex()
        sumj_dd = np.complex()
        temp_fi = np.complex()

        count = float()

        iqr = np.complex()
        ephase = np.complex()
        comp_sld = np.complex()

        I_out = np.zeros(npoints, dtype=np.float)

	    #Assume that pixel volumes are given in vol_pix in A^3 unit
        #Loop over q-values and multiply apply matrix
        for i in range(npoints):
            sumj_uu = np.complex()
            sumj_ud = np.complex()
            sumj_du = np.complex()
            sumj_dd = np.complex()

            for j in range(self.n_pix):
                if self.sldn_val[j] != 0.0 or self.mx_val[j] != 0.0 or self.my_val[j] != 0.0 or self.mz_val[j] != 0.0:

				    #anisotropic
                    temp_fi = np.complex()

                    b_sld.cal_msld(0, qx[i], qy[i], self.sldn_val[j],
                                   self.mx_val[j], self.my_val[j], self.mz_val[j],
                                   self.inspin, self.outspin, self.stheta);
                    qr = (qx[i]*self.x_val[j] + qy[i]*self.y_val[j]);
                    iqr = np.complex(0.0, qr)

                    #As in the original code, sets ephase reference to two methods that should
                    #both reset it, both set the real and imaginary parts.
                    ephase = np.exp(iqr)
                    #Let's multiply pixel(atomic) volume here
                    ephase = self.vol_pix[j] * ephase

				    #up_up
                    if (self.inspin > 0.0) & (self.outspin > 0.0):
                        comp_sld = np.complex(b_sld.uu, 0.0)
                        temp_fi = comp_sld * ephase
                        sumj_uu = sumj_uu + temp_fi

				    #down_down
                    if (self.inspin < 1.0) & (self.outspin < 1.0):
                        comp_sld = np.complex(b_sld.dd, 0.0)
                        temp_fi = comp_sld * ephase
                        sumj_dd = sumj_dd + temp_fi

                    #up_down
                    if (self.inspin > 0.0) & (self.outspin < 1.0):
                        comp_sld = np.complex(b_sld.re_ud, b_sld.im_ud)
                        temp_fi = comp_sld * ephase
                        sumj_ud = sumj_ud + temp_fi

                    #down_up
                    if (self.inspin < 1.0) & (self.outspin > 0.0):
                        comp_sld = np.complex(b_sld.re_du, b_sld.im_du)
                        temp_fi = comp_sld * ephase
                        sumj_du = sumj_du + temp_fi

                    if i == 0:
                        count += self.vol_pix[j];

            calc = lambda x: np.square(x.real) + np.square(x.imag)
            I_out[i] = calc(sumj_uu)
            I_out[i] += calc(sumj_ud)
            I_out[i] += calc(sumj_du)
            I_out[i] += calc(sumj_dd)
            I_out[i] *= (1.0E+8 / count) #in cm (unit) / number; to be multiplied by vol_pix

        return I_out

    def genicom(self, q):
        """
        Computes 1D isotropic.
        Isotropic: Assumes all slds are real (no magnetic)
        Also assumes there is no polarization: No dependency on spin.

        :param npoints: npoints.
        :param q: q vector.

        :return: I_out.
        """
        npoints = len(q)

        count = 0.0
        I_out = np.zeros(npoints)

        coords = np.vstack((self.x_val, self.y_val, self.z_val))

        norm_vals = np.linalg.norm(coords, axis=0)

        for i in range(npoints):
            sumj = 0.0

            if self.is_avg == 1:
                qr = norm_vals * q[i]
                bool_index = qr > 0.0

                qr_pos = qr[bool_index]

                qr_pos_calc = np.sin(qr_pos) / qr_pos

                sumj += np.sum(self.sldn_val[bool_index] * self.vol_pix[bool_index] * qr_pos_calc)
                sumj += np.sum(self.sldn_val[~bool_index] * self.vol_pix[~bool_index])

            else:
                #full calculation
                #pragma omp parallel for

                sld_j = np.dot(np.square(self.sldn_val).reshape(len(self.sldn_val), 1), np.square(self.vol_pix).reshape(1, len(self.vol_pix)))

                #calc calculates (x[j] - x[:]) * (x[j] - x[:]) where x is a 1d array.
                calc = lambda x: np.square(x.reshape(len(x), 1) - x.reshape(1, len(x)))

                #qr should be result of vector addition of [self.n_pix] + [self.n_pix] + [self.n_pix]
                qr = calc(self.x_val) + calc(self.y_val) + calc(self.z_val)

                #qr * scalar q.
                qr = np.sqrt(qr) * q[i]

                bool_index = qr > 0.0

                qr_pos = qr[bool_index]
                qr_pos_calc = np.sin(qr_pos) / qr_pos

                sumj += np.sum(np.dot(sld_j[bool_index], qr_pos_calc))
                sumj += np.sum(sld_j[~bool_index])

            if i == 0:
                count += np.sum(self.vol_pix)

            I_out[i] = sumj

            if self.is_avg == 1:
                I_out[i] *= sumj

            I_out[i] *= 1.0E+8 / count

        return I_out

if(__name__ == "__main__"):
    is_avg = 0
    npix = 301
    x = np.linspace(0.1, 0.5, npix)
    y = np.linspace(0.1, 0.5, npix)
    z = np.linspace(0.1, 0.5, npix)
    sldn = np.linspace(0.1, 0.5, npix)
    mx = np.linspace(0.1, 0.5, npix)
    my = np.linspace(0.1, 0.5, npix)
    mz = np.linspace(0.1, 0.5, npix)
    voli = np.linspace(0.1, 0.5, npix)
    q = np.linspace(0.1, 0.5, npix)

    in_spin = 0.5
    out_spin = 0.2
    s_theta = 0.1
    gen_i = GenI(is_avg, npix, x, y, z, sldn, mx, my, mz, voli, in_spin, out_spin, s_theta)

    setup = '''
from __main__ import GenI
import numpy as np
is_avg = 1
npix = 301
x = np.linspace(0.1, 0.5, npix)
y = np.linspace(0.1, 0.5, npix)
z = np.linspace(0.1, 0.5, npix)
sldn = np.linspace(0.1, 0.5, npix)
mx = np.linspace(0.1, 0.5, npix)
my = np.linspace(0.1, 0.5, npix)
mz = np.linspace(0.1, 0.5, npix)
voli = np.linspace(0.1, 0.5, npix)
q = np.linspace(0.1, 0.5, npix)

in_spin = 0.5
out_spin = 0.2
s_theta = 0.1
gen_i = GenI(is_avg, npix, x, y, z, sldn, mx, my, mz, voli, in_spin, out_spin, s_theta)'''
    run = '''
I_out = gen_i.genicomXY(npix, x, y)'''

    #times = timeit.repeat(stmt = run, setup = setup, repeat = 10, number = 1)

    #print(times)

    I_out = gen_i.genicomXY(x, y)

    print(I_out)
    print(I_out.shape)

    #test_sld = lib.polar_sld()
    #test_sld.uu = 1.0
    #test_sld.dd = 2.5
    #test_sld.ud = np.complex(1.5, 2.5)
    #test_sld.du = np.complex(4.5, 5.5)
    #param = 0.3

    #test_sld.cal_msld(0, 0.5, 0.5, 0.4986666666666667, 0.4986666666666667, 0.4986666666666667, 0.4986666666666667, 0.5, 0.2, 0.1)

    #print(test_sld)

"""
Taken from sld2i_module and sld2i, definition of GenI
class, defined through structs and global free functions in C.

Depends on lib.py, implementation of libfunc.c and librefl.c
"""
from math import factorial

import numpy as np
from scipy.special import sici
import timeit

import lib
#from . import lib
from numba import njit

class GenI():
    def __init__(self, is_avg, x, y, z, sldn, mx, my, mz,
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
        self.n_pix = len(x)
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
        b_sld = np.array([(np.float(), np.float(), np.complex(), np.complex())], dtype=lib.get_polar_sld_type())
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

                    lib.cal_msld(b_sld, 0, qx[i], qy[i], self.sldn_val[j],
                                 self.mx_val[j], self.my_val[j], self.mz_val[j],
                                 self.inspin, self.outspin, self.stheta)

                    qr = (qx[i]*self.x_val[j] + qy[i]*self.y_val[j])
                    iqr = np.complex(0.0, qr)

                    #As in the original code, sets ephase reference to two methods that should
                    #both reset it, both set the real and imaginary parts.
                    ephase = np.exp(iqr)
                    #Let's multiply pixel(atomic) volume here
                    ephase = self.vol_pix[j] * ephase

				    #up_up
                    if (self.inspin > 0.0) & (self.outspin > 0.0):
                        comp_sld = np.complex(b_sld[0]['uu'], 0.0)
                        temp_fi = comp_sld * ephase
                        sumj_uu = sumj_uu + temp_fi

				    #down_down
                    if (self.inspin < 1.0) & (self.outspin < 1.0):
                        comp_sld = np.complex(b_sld[0]['dd'], 0.0)
                        temp_fi = comp_sld * ephase
                        sumj_dd = sumj_dd + temp_fi

                    #up_down
                    if (self.inspin > 0.0) & (self.outspin < 1.0):
                        comp_sld = np.complex(b_sld[0]['ud'].real, b_sld[0]['ud'].imag)
                        temp_fi = comp_sld * ephase
                        sumj_ud = sumj_ud + temp_fi

                    #down_up
                    if (self.inspin < 1.0) & (self.outspin > 0.0):
                        comp_sld = np.complex(b_sld[0]['du'].real, b_sld[0]['du'].imag)
                        temp_fi = comp_sld * ephase
                        sumj_du = sumj_du + temp_fi

                    if i == 0:
                        count += self.vol_pix[j]

            calc = lambda x: np.square(x.real) + np.square(x.imag)
            I_out[i] = calc(sumj_uu)
            I_out[i] += calc(sumj_ud)
            I_out[i] += calc(sumj_du)
            I_out[i] += calc(sumj_dd)
            I_out[i] *= (1.0E+8 / count) #in cm (unit) / number; to be multiplied by vol_pix

        return I_out

    def genicomXY_vec(self, qx, qy):
        """
        Compute 2d ansotropic.

        Returns I_out[] 1d array.
        """

        npoints = len(qx)

        #npoints is given negative for angular averaging
        #Assumes that q doesn't have qz component and sld_n is all real
        b_sld = np.zeros(self.n_pix, dtype=lib.get_polar_sld_type())
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

            #for j in range(self.n_pix):
            zero_sldn = self.sldn_val == 0
            zero_mx = self.mx_val == 0
            zero_my = self.my_val == 0
            zero_mz = self.mz_val == 0
            #find index where all are equal to 0
            index_zero = [s & x & y & z for (s, x, y, z) in zip(zero_sldn, zero_mx, zero_my, zero_mz)]

            #then exclude those from the calculation
            index_zero = np.array(index_zero, dtype=bool)
            sldn_val_use = self.sldn_val[~index_zero]
            mx_val_use = self.mx_val[~index_zero]
            my_val_use = self.my_val[~index_zero]
            mz_val_use = self.mz_val[~index_zero]

			#anisotropic
            temp_fi = np.complex()

            #all passed to cal_msld, not full values but should all be same length.
            lib.cal_msld_vec(b_sld, 0, qx[i], qy[i], sldn_val_use,
                             mx_val_use, my_val_use, mz_val_use,
                             self.inspin, self.outspin, self.stheta)

            qr = (qx[i]*self.x_val + qy[i]*self.y_val)
            iqr = np.zeros(len(self.x_val), dtype=np.complex_)

            for j in range(len(self.x_val)):
                _temp = np.complex(0.0, qr[j])
                iqr[j] = _temp

            #iqr = np.complex(0.0, qr)

            #As in the original code, sets ephase reference to two methods that should
            #both reset it, both set the real and imaginary parts.
            ephase = np.exp(iqr)
            #Let's multiply pixel(atomic) volume here
            ephase = self.vol_pix * ephase

			#up_up
            if (self.inspin > 0.0) & (self.outspin > 0.0):
                comp_sld = b_sld['uu']
                temp_fi = comp_sld * ephase
                sumj_uu = np.sum(sumj_uu + temp_fi)

			#down_down
            if (self.inspin < 1.0) & (self.outspin < 1.0):
                comp_sld = b_sld['dd']
                temp_fi = comp_sld * ephase
                sumj_dd = np.sum(sumj_dd + temp_fi)

            #up_down
            if (self.inspin > 0.0) & (self.outspin < 1.0):
                comp_sld = b_sld['ud']
                temp_fi = comp_sld * ephase
                sumj_ud = np.sum(sumj_ud + temp_fi)

            #down_up
            if (self.inspin < 1.0) & (self.outspin > 0.0):
                comp_sld = b_sld['du']
                temp_fi = comp_sld * ephase
                sumj_du = np.sum(sumj_du + temp_fi)

            if i == 0:
                count = np.sum(self.vol_pix)


            calc = lambda x: np.square(x.real) + np.square(x.imag)
            I_out[i] = calc(sumj_uu)
            I_out[i] += calc(sumj_ud)
            I_out[i] += calc(sumj_du)
            I_out[i] += calc(sumj_dd)
            I_out[i] *= 1.0E+8 / count #in cm (unit) / number; to be multiplied by vol_pix

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
        nq = len(q)
        npoints = len(self.sldn_val)
        coords = np.vstack((self.x_val, self.y_val, self.z_val))
        sld = self.sldn_val * self.vol_pix
        count = np.sum(self.vol_pix)
        I_out = np.zeros(npoints)

        if self.is_avg == 1:
            r = np.linalg.norm(coords, axis=0)
            for i in range(nq):
                bes = np.sinc((q[i]/np.pi) * r)
                sumj = np.sum(sld * bes)
                I_out[i] = sumj ** 2

        else:
            for i in range(nq):
                sumj = genicom_full(q[i], npoints, coords, sld)
                I_out[i] = sumj

        return I_out * 1.0E+8/count

@njit('f8(f8, f8, f8[:, :], f8[:])')
def genicom_full(q, npoints, coords, sld):
    sumj = 0.0

    for j in range(npoints):
        dx = coords[:, j:] - coords[:, j:j+1]
        r = np.sqrt(np.sum(dx**2, axis=0))
        bes = np.sinc((q/np.pi)*r)
        Ijk = sld[j:] * sld[j] * bes
        sumj += 2*np.sum(Ijk) - Ijk[0] # don't double-count the diagonal

    return sumj

def demo():
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
    gen_i = GenI(is_avg, x, y, z, sldn, mx, my, mz, voli, in_spin, out_spin, s_theta)

    setup = '''
from __main__ import GenI
import numpy as np
is_avg = 0
npix = 1000
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
gen_i = GenI(is_avg, x, y, z, sldn, mx, my, mz, voli, in_spin, out_spin, s_theta)'''
    run = '''
I_out = gen_i.genicom(q)'''

    times = timeit.repeat(stmt = run, setup = setup, repeat = 1, number = 1)
    print(times)
    qx = np.linspace(0.1, 0.5, 301)
    qy = np.copy(qx)

    I_out = gen_i.genicom(q)

    np.set_printoptions(precision = 15)
    print("result:", I_out)
    print("size I_out: ", I_out.shape)
    print("type I_out: ", I_out.dtype)

    #print(I_out)
    #print(I_out.shape)

    #test_sld = lib.polar_sld()
    #test_sld.uu = 1.0
    #test_sld.dd = 2.5
    #test_sld.ud = np.complex(1.5, 2.5)
    #test_sld.du = np.complex(4.5, 5.5)
    #param = 0.3

    #test_sld.cal_msld(0, 0.5, 0.5, 0.4986666666666667, 0.4986666666666667, 0.4986666666666667, 0.4986666666666667, 0.5, 0.2, 0.1)

    #print(test_sld)

if __name__ == "__main__":
    demo()

"""
Taken from sld2i_module and sld2i, definition of GenI
class, defined through structs and global free functions in C.

Depends on lib.py, implementation of libfunc.c and librefl.c
"""
from math import factorial

import numpy as np
from scipy.special import sici

from . import lib

class GenI():
    def __init__(self, is_avg, npix, x, y, sldn, z, mx, my, mz,
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

    def genicomXY(self, npoints, qx, qy, I_out):
        """
        Compute 2d ansotropic.

        Stores result by reference in vector I_out[]
        """
        #npoints is given negative for angular averaging
        #Assumes that q doesn't have qz component and sld_n is all real
        b_sld = polar_sld()
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
	    #Assume that pixel volumes are given in vol_pix in A^3 unit
        #Loop over q-values and multiply apply matrix
        for i in range(npoints):
            sumj_uu = np.complex()
            sumj_ud = np.complex()
            sumj_du = np.complex()
            sumj_dd = np.complex()

            for j in range(self.n_pix):
                if self.sldn_val[j] != 0.0 | self.mx_val[j] != 0.0 | self.my_val[j] != 0.0 | self.mz_val[j] != 0.0:

				    #anisotropic
                    temp_fi = np.complex()
                    b_sld.cal_msld(b_sld, 0, qx[i], qy[i], self.sldn_val[j],
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

            calc = lambda x: np.square(x.real) + np.square(y.imag)

            I_out[i] = calc(sumj_uu)
            I_out[i] += calc(sumj_ud)
            I_out[i] += calc(sumj_du)
            I_out[i] += calc(sumj_dd)

            I_out[i] *= (1.0E+8 / count) #in cm (unit) / number; to be multiplied by vol_pix

    def genicom(self, npoints, q, I_out):
        """
        Computes 1D isotropic.
        Isotropic: Assumes all slds are real (no magnetic)
        Also assumes there is no polarization: No dependency on spin.
        """
        #current method returns by reference using I_out, will change to return by value.
        #qr = vector norm in 3d.
	    #make 3d matrix of points for other purposes as well?
	    #x y and z, all length j, must be same,
        coords = np.zeros([self.n_pix, self.n_pix, self.n_pix])

        coords[0, :] = self.x_val
        coords[1, :] = self.y_val
        coords[2, :] = self.z_val

        norm_vals = np.linalg.norm(coords, axis=1)

        for i in range(npoints):
            sumj = 0.0

		    #for j in range(self.n_pix):
		    #dependant on the lengths of sldn_val and vol_pix.
		    #then the length of the q vector.

            if self.is_avg == 1:
			    #np.dot(norm_vals, q)?
                qr = norm_vals * q[i]

                if qr > 0.0:
                    qr = np.sin(qr) / qr
                    sumj += self.sldn_val * self.vol_pix * qr

                else:
                    sumj += self.sldn_val * self.vol_pix
            else:
			    #for k in range(self.n_pix):
			    #j = k, up to n_pix, if x y and z is len(n_pix) then just all
			    #Assume it is
			    #as long as vol_pix and sldn_val shape is also [n_pix] should work.

                sld_j = self.sldn_val * self.sldn_val * self.vol_pix * self.vol_pix
                qr = np.square(self.x_val - self.x_val) + np.square(self.y_val - self.y_val) + np.square(self.z_val - self.z_val)

                qr = np.sqrt(qr) * q[i]

                if qr > 0.0:
                    sumj += np.sum(sld_j * np.sin(qr) / qr)
                else:
                    sumj += np.sum(sld_j)

            if i == 0:
                count += self.vol_pix

            I_out[i] = sumj

            if self.is_avg == 1:
                I_out[i] *= sumj

            I_out[i] *= 1.0E+8 / count

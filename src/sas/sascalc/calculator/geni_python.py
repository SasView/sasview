"""
Taken from sld2i_module and sld2i, definition of GenI
class, defined through structs and global free functions in C.

Depends on lib.py, implementation of libfunc.c and librefl.c
"""
import numpy as np

from . import lib

class GenI():
    #Instance variables, no setters/getters in C so public.

    is_avg = int(0)
    n_pix = int(0)
    x_val = np.zeros(0, dtype=float)
    y_val = np.zeros(0, dtype=float)
    z_val = np.zeros(0, dtype=float)
    sldn_val = np.zeros(0, dtype=float)
    mx_val = np.zeros(0, dtype=float)
    my_val = np.zeros(0, dtype=float)
    mz_val = np.zeros(0, dtype=float)
    vol_pix = np.zeros(0, dtype=float)

    #Spin Ratios.
    inspin = float(0)
    outspin = float(0)
    stheta = float(0)

    def __init__(self):
        pass

    def genicom(self, npoints, q, I_out):
        #current method returns by reference using I_out, will change to return by value.

        #qr = vector norm in 3d.
	    #make 3d matrix of points for other purposes as well?
	    #x y and z, all length j, must be same,
        coords = np.zeros([self.n_pix, self.n_pix, self.n_pix])

        coords[0, :] = self.x_val
        coords[1, :] = self.y_val
        coords[2, :] = self.z_val

        norm_vals = np.linalg.norm(coords, axis = 1)

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
                    sumj += self.sldn_val * this.vol_pix * qr

                else:
                    sumj += this.sldn_val * this.vol_pix
            else:
			    #for k in range(self.n_pix):
			    #j = k, up to n_pix, if x y and z is len(n_pix) then just all
			    #Assume it is
			    #as long as vol_pix and sldn_val shape is also [n_pix] should work.

                sld_j = self.sldn_val * self.sldn_val * self.vol_pix * self.vol_pix
                qr = (self.x_val - self.x_val)**2 + (self.y_val - self.y_val)**2 + (self.z_val - self.z_val)**2

                qr = np.sqrt(qr) * q[i]

                if qr > 0.0:
                    sumj += np.sum(sld_j * np.sin(qr) / qr)
                else:
                    sumj += np.sum(sld_j)

            if(i == 0):
                count += self.vol_pix

            I_out[i] = sumj

            if(self.is_avg == 1):
                I_out[i] *= sumj

            I_out[i] *= 1.0E+8 / count

    def genicomXY(self):
        pass
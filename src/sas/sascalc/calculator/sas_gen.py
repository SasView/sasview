# pylint: disable=invalid-name
"""
SAS generic computation and sld file readers.

Calculation checked by sampling from an ellipsoid and comparing Iq with the
1D, 2D oriented and 2D oriented magnetic analytical model from sasmodels.
"""
from __future__ import print_function

import os
import sys
import logging

import numpy as np
from periodictable import formula, nsf

from .geni import Iq, Iqxy

logger = logging.getLogger(__name__)

if sys.version_info[0] < 3:
    def decode(s):
        return s
else:
    def decode(s):
        return s.decode() if isinstance(s, bytes) else s

MFACTOR_AM = 2.90636E-12
MFACTOR_MT = 2.3128E-9
METER2ANG = 1.0E+10
#Avogadro constant [1/mol]
NA = 6.02214129e+23

def mag2sld(mag, v_unit=None):
    """
    Convert magnetization to magnatic SLD
    sldm = Dm * mag where Dm = gamma * classical elec. radius/(2*Bohr magneton)
    Dm ~ 2.90636E8 [(A m)^(-1)]= 2.90636E-12 [to Ang^(-2)]
    """
    if v_unit == "A/m":
        factor = MFACTOR_AM
    elif v_unit == "mT":
        factor = MFACTOR_MT
    else:
        raise ValueError("Invalid magnetism unit %r" % v_unit)
    return factor * mag

def transform_center(pos_x, pos_y, pos_z):
    """
    re-center
    :return: posx, posy, posz   [arrays]
    """
    posx = pos_x - (min(pos_x) + max(pos_x)) / 2.0
    posy = pos_y - (min(pos_y) + max(pos_y)) / 2.0
    posz = pos_z - (min(pos_z) + max(pos_z)) / 2.0
    return posx, posy, posz

class GenSAS(object):
    """
    Generic SAS computation Model based on sld (n & m) arrays
    """
    def __init__(self):
        """
        Init
        :Params sld_data: MagSLD object
        """
        # Initialize BaseComponent
        self.sld_data = None
        self.data_pos_unit = None
        self.data_x = None
        self.data_y = None
        self.data_z = None
        self.data_sldn = None
        self.data_mx = None
        self.data_my = None
        self.data_mz = None
        self.data_vol = None #[A^3]
        self.is_avg = False
        ## Name of the model
        self.name = "GenSAS"
        ## Define parameters
        self.params = {}
        self.params['scale'] = 1.0
        self.params['background'] = 0.0
        self.params['solvent_SLD'] = 0.0
        self.params['total_volume'] = 1.0
        self.params['Up_frac_in'] = 1.0
        self.params['Up_frac_out'] = 1.0
        self.params['Up_theta'] = 0.0
        self.params['Up_phi'] = 0.0
        self.description = 'GenSAS'
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale'] = ['', 0.0, np.inf]
        self.details['background'] = ['[1/cm]', 0.0, np.inf]
        self.details['solvent_SLD'] = ['1/A^(2)', -np.inf, np.inf]
        self.details['total_volume'] = ['A^(3)', 0.0, np.inf]
        self.details['Up_frac_in'] = ['[u/(u+d)]', 0.0, 1.0]
        self.details['Up_frac_out'] = ['[u/(u+d)]', 0.0, 1.0]
        self.details['Up_theta'] = ['[deg]', -90, 90]
        self.details['Up_phi'] = ['[deg]', -180, 180]
        # fixed parameters
        self.fixed = []

    def set_pixel_volumes(self, volume):
        """
        Set the volume of a pixel in (A^3) unit
        :Param volume: pixel volume [float]
        """
        if self.data_vol is None:
            raise TypeError("data_vol is missing")
        self.data_vol = volume

    def set_is_avg(self, is_avg=False):
        """
        Sets is_avg: [bool]
        """
        self.is_avg = bool(is_avg)

    def calculate_Iq(self, qx, qy=None):
        """
        Evaluate the function
        :Param x: array of x-values
        :Param y: array of y-values
        :return: function value
        """
        x, y, z = self.data_x, self.data_y, self.data_z
        sld = self.data_sldn - self.params['solvent_SLD']
        vol = self.data_vol
        if qy is not None and len(qy) > 0:
            # 2-D calculation
            qx, qy = _vec(qx), _vec(qy)
            mx, my, mz = self.data_mx, self.data_my, self.data_mz
            in_spin = self.params['Up_frac_in']
            out_spin = self.params['Up_frac_out']
            s_theta = self.params['Up_theta']
            s_phi = self.params['Up_phi']
            I_out = Iqxy(
                qx, qy, x, y, z, sld, vol, mx, my, mz,
                in_spin, out_spin, s_theta, s_phi,
                )
        else:
            # 1-D calculation
            q = _vec(qx)
            if self.is_avg:
                x, y, z = transform_center(x, y, z)
            I_out = Iq(q, x, y, z, sld, vol, is_avg=self.is_avg)

        vol_correction = self.data_total_volume / self.params['total_volume']
        result = ((self.params['scale'] * vol_correction) * I_out
                  + self.params['background'])
        return result

    # TODO: rename set_sld_data() since it does more than set sld
    def set_sld_data(self, sld_data=None):
        """
        Sets sld_data
        """
        self.sld_data = sld_data
        self.data_pos_unit = sld_data.pos_unit
        self.data_x = _vec(sld_data.pos_x)
        self.data_y = _vec(sld_data.pos_y)
        self.data_z = _vec(sld_data.pos_z)
        self.data_sldn = _vec(sld_data.sld_n)
        self.data_mx = _vec(sld_data.sld_mx)
        self.data_my = _vec(sld_data.sld_my)
        self.data_mz = _vec(sld_data.sld_mz)
        self.data_vol = _vec(sld_data.vol_pix)
        self.data_total_volume = np.sum(sld_data.vol_pix)
        self.params['total_volume'] = self.data_total_volume

    def getProfile(self):
        """
        Get SLD profile
        : return: sld_data
        """
        return self.sld_data

    def run(self, x=0.0):
        """
        Evaluate the model
        :param x: simple value
        :return: (I value)
        """
        if isinstance(x, list):
            if len(x[1]) > 0:
                raise ValueError("Not a 1D vector.")
            # 1D I is found at y=0 in the 2D pattern
            out = self.calculate_Iq(x[0])
            return out
        else:
            msg = "Q must be given as list of qx's and qy's"
            raise ValueError(msg)

    def runXY(self, x=0.0):
        """
        Evaluate the model
        :param x: simple value
        :return: I value
        :Use this runXY() for the computation
        """
        if isinstance(x, list):
            return self.calculate_Iq(x[0], x[1])
        else:
            msg = "Q must be given as list of qx's and qy's"
            raise ValueError(msg)

    def evalDistribution(self, qdist):
        """
        Evaluate a distribution of q-values.

        :param qdist: ndarray of scalar q-values (for 1D) or list [qx,qy]
                      where qx,qy are 1D ndarrays (for 2D).
        """
        if isinstance(qdist, list):
            return self.run(qdist) if len(qdist[1]) < 1 else self.runXY(qdist)
        else:
            mesg = "evalDistribution is expecting an ndarray of "
            mesg += "a list [qx,qy] where qx,qy are arrays."
            raise RuntimeError(mesg)

def _vec(v):
    return np.ascontiguousarray(v, 'd') if v is not None else None

class OMF2SLD(object):
    """
    Convert OMFData to MAgData
    """
    def __init__(self):
        """
        Init
        """
        self.pos_x = None
        self.pos_y = None
        self.pos_z = None
        self.mx = None
        self.my = None
        self.mz = None
        self.sld_n = None
        self.vol_pix = None
        self.output = None
        self.omfdata = None

    def set_data(self, omfdata, shape='rectangular'):
        """
        Set all data
        """
        self.omfdata = omfdata
        length = int(omfdata.xnodes * omfdata.ynodes * omfdata.znodes)
        pos_x = np.arange(omfdata.xmin,
                          omfdata.xnodes*omfdata.xstepsize + omfdata.xmin,
                          omfdata.xstepsize)
        pos_y = np.arange(omfdata.ymin,
                          omfdata.ynodes*omfdata.ystepsize + omfdata.ymin,
                          omfdata.ystepsize)
        pos_z = np.arange(omfdata.zmin,
                          omfdata.znodes*omfdata.zstepsize + omfdata.zmin,
                          omfdata.zstepsize)
        self.pos_x = np.tile(pos_x, int(omfdata.ynodes * omfdata.znodes))
        self.pos_y = pos_y.repeat(int(omfdata.xnodes))
        self.pos_y = np.tile(self.pos_y, int(omfdata.znodes))
        self.pos_z = pos_z.repeat(int(omfdata.xnodes * omfdata.ynodes))
        self.mx = omfdata.mx
        self.my = omfdata.my
        self.mz = omfdata.mz
        self.sld_n = np.zeros(length)

        if omfdata.mx is None:
            self.mx = np.zeros(length)
        if omfdata.my is None:
            self.my = np.zeros(length)
        if omfdata.mz is None:
            self.mz = np.zeros(length)

        self._check_data_length(length)
        #self.remove_null_points(True, False)
        mask = np.ones(len(self.sld_n), dtype=bool)
        if shape.lower() == 'ellipsoid':
            try:
                # Pixel (step) size included
                x_c = max(self.pos_x) + min(self.pos_x)
                y_c = max(self.pos_y) + min(self.pos_y)
                z_c = max(self.pos_z) + min(self.pos_z)
                x_d = max(self.pos_x) - min(self.pos_x)
                y_d = max(self.pos_y) - min(self.pos_y)
                z_d = max(self.pos_z) - min(self.pos_z)
                x_r = (x_d + omfdata.xstepsize) / 2.0
                y_r = (y_d + omfdata.ystepsize) / 2.0
                z_r = (z_d + omfdata.zstepsize) / 2.0
                x_dir2 = ((self.pos_x - x_c / 2.0) / x_r)
                x_dir2 *= x_dir2
                y_dir2 = ((self.pos_y - y_c / 2.0) / y_r)
                y_dir2 *= y_dir2
                z_dir2 = ((self.pos_z - z_c / 2.0) / z_r)
                z_dir2 *= z_dir2
                mask = (x_dir2 + y_dir2 + z_dir2) <= 1.0
            except Exception as exc:
                logger.error(exc)
        self.output = MagSLD(self.pos_x[mask], self.pos_y[mask],
                             self.pos_z[mask], self.sld_n[mask],
                             self.mx[mask], self.my[mask], self.mz[mask])
        self.output.set_pix_type('pixel')
        self.output.set_pixel_symbols('pixel')

    def get_omfdata(self):
        """
        Return all data
        """
        return self.omfdata

    def get_output(self):
        """
        Return output
        """
        return self.output

    def _check_data_length(self, length):
        """
        Check if the data lengths are consistent
        :Params length: data length
        """
        parts = (self.pos_x, self.pos_y, self.pos_z, self.mx, self.my, self.mz)

        if any(len(v) != length for v in parts):
            raise ValueError("Error: Inconsistent data length.")

    def remove_null_points(self, remove=False, recenter=False):
        """
        Removes any mx, my, and mz = 0 points
        """
        if remove:
            is_nonzero = (np.fabs(self.mx) + np.fabs(self.my) +
                          np.fabs(self.mz)).nonzero()
            if len(is_nonzero[0]) > 0:
                self.pos_x = self.pos_x[is_nonzero]
                self.pos_y = self.pos_y[is_nonzero]
                self.pos_z = self.pos_z[is_nonzero]
                self.sld_n = self.sld_n[is_nonzero]
                self.mx = self.mx[is_nonzero]
                self.my = self.my[is_nonzero]
                self.mz = self.mz[is_nonzero]
        if recenter:
            self.pos_x -= (min(self.pos_x) + max(self.pos_x)) / 2.0
            self.pos_y -= (min(self.pos_y) + max(self.pos_y)) / 2.0
            self.pos_z -= (min(self.pos_z) + max(self.pos_z)) / 2.0

    def get_magsld(self):
        """
        return MagSLD
        """
        return self.output


class OMFReader(object):
    """
    Class to load omf/ascii files (3 columns w/header).
    """
    ## File type
    type_name = "OMF ASCII"

    ## Wildcards
    type = ["OMF files (*.OMF, *.omf)|*.omf"]
    ## List of allowed extensions
    ext = ['.omf', '.OMF']

    def read(self, path):
        """
        Load data file
        :param path: file path
        :return: x, y, z, sld_n, sld_mx, sld_my, sld_mz
        """
        desc = ""
        mx = np.zeros(0)
        my = np.zeros(0)
        mz = np.zeros(0)
        try:
            input_f = open(path, 'rb')
            buff = decode(input_f.read())
            lines = buff.split('\n')
            input_f.close()
            output = OMFData()
            valueunit = None
            for line in lines:
                line = line.strip()
                # Read data
                if line and not line.startswith('#'):
                    try:
                        toks = line.split()
                        _mx = float(toks[0])
                        _my = float(toks[1])
                        _mz = float(toks[2])
                        _mx = mag2sld(_mx, valueunit)
                        _my = mag2sld(_my, valueunit)
                        _mz = mag2sld(_mz, valueunit)
                        mx = np.append(mx, _mx)
                        my = np.append(my, _my)
                        mz = np.append(mz, _mz)
                    except Exception as exc:
                        # Skip non-data lines
                        logger.error(str(exc)+" when processing %r"%line)
                elif line:
                #Reading Header; Segment count ignored
                    s_line = line.split(":", 1)
                    if s_line[0].lower().count("oommf") > 0:
                        oommf = s_line[1].lstrip()
                    if s_line[0].lower().count("title") > 0:
                        title = s_line[1].lstrip()
                    if s_line[0].lower().count("desc") > 0:
                        desc += s_line[1].lstrip()
                        desc += '\n'
                    if s_line[0].lower().count("meshtype") > 0:
                        meshtype = s_line[1].lstrip()
                    if s_line[0].lower().count("meshunit") > 0:
                        meshunit = s_line[1].lstrip()
                        if meshunit.count("m") < 1:
                            msg = "Error: \n"
                            msg += "We accept only m as meshunit"
                            raise ValueError(msg)
                    if s_line[0].lower().count("xbase") > 0:
                        xbase = s_line[1].lstrip()
                    if s_line[0].lower().count("ybase") > 0:
                        ybase = s_line[1].lstrip()
                    if s_line[0].lower().count("zbase") > 0:
                        zbase = s_line[1].lstrip()
                    if s_line[0].lower().count("xstepsize") > 0:
                        xstepsize = s_line[1].lstrip() 
                    if s_line[0].lower().count("ystepsize") > 0:
                        ystepsize = s_line[1].lstrip()   
                    if s_line[0].lower().count("zstepsize") > 0:
                        zstepsize = s_line[1].lstrip()
                    if s_line[0].lower().count("xnodes") > 0:
                        xnodes = s_line[1].lstrip()   
                    #print(s_line[0].lower().count("ynodes"))
                    if s_line[0].lower().count("ynodes") > 0:
                        ynodes = s_line[1].lstrip()
                        #print(ynodes)
                    if s_line[0].lower().count("znodes") > 0:
                        znodes = s_line[1].lstrip()  
                    if s_line[0].lower().count("xmin") > 0:
                        xmin = s_line[1].lstrip()
                    if s_line[0].lower().count("ymin") > 0:
                        ymin = s_line[1].lstrip()
                    if s_line[0].lower().count("zmin") > 0:
                        zmin = s_line[1].lstrip()
                    if s_line[0].lower().count("xmax") > 0:
                        xmax = s_line[1].lstrip()
                    if s_line[0].lower().count("ymax") > 0:
                        ymax = s_line[1].lstrip()
                    if s_line[0].lower().count("zmax") > 0:
                        zmax = s_line[1].lstrip()
                    if s_line[0].lower().count("valueunit") > 0:
                        valueunit = s_line[1].lstrip()
                        if valueunit.count("mT") < 1 and valueunit.count("A/m") < 1: 
                            msg = "Error: \n"
                            msg += "We accept only mT or A/m as valueunit"
                            raise ValueError(msg)    
                    if s_line[0].lower().count("valuemultiplier") > 0:
                        valuemultiplier = s_line[1].lstrip()
                    if s_line[0].lower().count("valuerangeminmag") > 0:
                        valuerangeminmag = s_line[1].lstrip()
                    if s_line[0].lower().count("valuerangemaxmag") > 0:
                        valuerangemaxmag = s_line[1].lstrip()
                    if s_line[0].lower().count("end") > 0:
                        output.filename = os.path.basename(path)
                        output.oommf = oommf
                        output.title = title
                        output.desc = desc
                        output.meshtype = meshtype
                        output.xbase = float(xbase) * METER2ANG
                        output.ybase = float(ybase) * METER2ANG
                        output.zbase = float(zbase) * METER2ANG
                        output.xstepsize = float(xstepsize) * METER2ANG
                        output.ystepsize = float(ystepsize) * METER2ANG
                        output.zstepsize = float(zstepsize) * METER2ANG
                        output.xnodes = float(xnodes)
                        output.ynodes = float(ynodes)
                        output.znodes = float(znodes)
                        output.xmin = float(xmin) * METER2ANG
                        output.ymin = float(ymin) * METER2ANG
                        output.zmin = float(zmin) * METER2ANG
                        output.xmax = float(xmax) * METER2ANG
                        output.ymax = float(ymax) * METER2ANG
                        output.zmax = float(zmax) * METER2ANG
                        output.valuemultiplier = valuemultiplier
                        output.valuerangeminmag \
                            = mag2sld(float(valuerangeminmag), valueunit)
                        output.valuerangemaxmag \
                            = mag2sld(float(valuerangemaxmag), valueunit)
            output.set_m(mx, my, mz)
            return output
        except Exception:
            msg = "%s is not supported: \n" % path
            msg += "We accept only Text format OMF file."
            raise RuntimeError(msg)

class PDBReader(object):
    """
    PDB reader class: limited for reading the lines starting with 'ATOM'
    """
    type_name = "PDB"
    ## Wildcards
    type = ["pdb files (*.PDB, *.pdb)|*.pdb"]
    ## List of allowed extensions
    ext = ['.pdb', '.PDB']

    def read(self, path):
        """
        Load data file

        :param path: file path
        :return: MagSLD
        :raise RuntimeError: when the file can't be opened
        """
        pos_x = []
        pos_y = []
        pos_z = []
        sld_n = []
        sld_mx = []
        sld_my = []
        sld_mz = []
        vol_pix = []
        pix_symbol = []
        x_line = []
        y_line = []
        z_line = []
        x_lines = []
        y_lines = []
        z_lines = []
        try:
            input_f = open(path, 'rb')
            buff = decode(input_f.read())
            lines = buff.split('\n')
            input_f.close()
            num = 0
            for line in lines:
                try:
                    # check if line starts with "ATOM"
                    if line[0:6] in ('ATM   ', 'ATOM  '):
                        # define fields of interest
                        atom_name = line[12:16].strip()
                        try:
                            float(line[12])
                            atom_name = atom_name[1].upper()
                        except Exception:
                            if len(atom_name) == 4:
                                atom_name = atom_name[0].upper()
                            elif line[12] != ' ':
                                atom_name = atom_name[0].upper() + \
                                        atom_name[1].lower()
                            else:
                                atom_name = atom_name[0].upper()
                        _pos_x = float(line[30:38].strip())
                        _pos_y = float(line[38:46].strip())
                        _pos_z = float(line[46:54].strip())
                        pos_x = np.append(pos_x, _pos_x)
                        pos_y = np.append(pos_y, _pos_y)
                        pos_z = np.append(pos_z, _pos_z)
                        try:
                            val = nsf.neutron_sld(atom_name)[0]
                            # sld in Ang^-2 unit
                            val *= 1.0e-6
                            sld_n = np.append(sld_n, val)
                            atom = formula(atom_name)
                            # cm to A units
                            vol = 1.0e+24 * atom.mass / atom.density / NA
                            vol_pix = np.append(vol_pix, vol)
                        except Exception:
                            logger.error("Error: set the sld of %s to zero"% atom_name)
                            sld_n = np.append(sld_n, 0.0)
                        sld_mx = np.append(sld_mx, 0)
                        sld_my = np.append(sld_my, 0)
                        sld_mz = np.append(sld_mz, 0)
                        pix_symbol = np.append(pix_symbol, atom_name)
                    elif line[0:6] == 'CONECT':
                        toks = line.split()
                        num = int(toks[1]) - 1
                        val_list = []
                        for val in toks[2:]:
                            try:
                                int_val = int(val)
                            except Exception:
                                break
                            if int_val == 0:
                                break
                            val_list.append(int_val)
                        #need val_list ordered
                        for val in val_list:
                            index = val - 1
                            if (pos_x[index], pos_x[num]) in x_line and \
                               (pos_y[index], pos_y[num]) in y_line and \
                               (pos_z[index], pos_z[num]) in z_line:
                                continue
                            x_line.append((pos_x[num], pos_x[index]))
                            y_line.append((pos_y[num], pos_y[index]))
                            z_line.append((pos_z[num], pos_z[index]))
                    if len(x_line) > 0:
                        x_lines.append(x_line)
                        y_lines.append(y_line)
                        z_lines.append(z_line)
                except Exception as exc:
                    logger.error(exc)

            output = MagSLD(pos_x, pos_y, pos_z, sld_n, sld_mx, sld_my, sld_mz)
            output.set_conect_lines(x_line, y_line, z_line)
            output.filename = os.path.basename(path)
            output.set_pix_type('atom')
            output.set_pixel_symbols(pix_symbol)
            output.set_nodes()
            output.set_pixel_volumes(vol_pix)
            output.sld_unit = '1/A^(2)'
            return output
        except Exception:
            raise RuntimeError("%s is not a sld file" % path)

    def write(self, path, data):
        """
        Write
        """
        print("Not implemented... ")

class SLDReader(object):
    """
    SLD reader for text files.

    7 columns: x, y, z, sld, mx, my, mz
    8 columns: x, y, z, sld, mx, my, mz, volume
    """
    ## File type
    type_name = "SLD ASCII"
    ## Wildcards
    type = ["sld files (*.SLD, *.sld)|*.sld",
            "txt files (*.TXT, *.txt)|*.txt",
            "all files (*.*)|*.*"]
    ## List of allowed extensions
    ext = ['.sld', '.SLD', '.txt', '.TXT', '.*']

    def read(self, path):
        """
        Load data file
        :param path: file path
        :return MagSLD: x, y, z, sld_n, sld_mx, sld_my, sld_mz
        :raise RuntimeError: when the file can't be loaded
        """
        try:
            data = np.loadtxt(path, dtype='float', skiprows=1,
                              ndmin=1, unpack=True)
        except Exception:
            data = None
        if data is None or data.shape[0] not in (7, 8):
            raise RuntimeError("%r is not a sld file" % path)
        x, y, z, sld, mx, my, mz = data[:7]
        vol = data[7] if data.shape[0] > 7 else None
        output = MagSLD(x, y, z, sld, mx, my, mz, vol)
        output.filename = os.path.basename(path)
        output.set_pix_type('pixel')
        output.set_pixel_symbols('pixel')
        return output

    def write(self, path, data):
        """
        Write sld file
        :Param path: file path
        :Param data: MagSLD data object
        """
        if path is None:
            raise ValueError("Missing the file path.")
        if data is None:
            raise ValueError("Missing the data to save.")
        x, y, z = data.pos_x, data.pos_y, data.pos_z
        sld_n = data.sld_n if data.sld_n is not None else np.zeros_like(x)
        if data.sld_mx is None:
            mx = my = mz = np.zeros_like(x)
        else:
            mx, my, mz = data.sld_mx, data.sld_my, data.sld_mz
        vol = data.vol_pix if data.vol_pix is not None else np.ones_like(x)
        columns = np.column_stack((x, y, z, sld_n, mx, my, mz, vol))
        with open(path, 'w') as out:
            # First Line: Column names
            out.write("X  Y  Z  SLDN SLDMx  SLDMy  SLDMz VOLUMEpix\n")
            np.savetxt(out, columns)


class OMFData(object):
    """
    OMF Data.
    """
    _meshunit = "A"
    _valueunit = "A^(-2)"
    def __init__(self):
        """
        Init for mag SLD
        """
        self.filename = 'default'
        self.oommf = ''
        self.title = ''
        self.desc = ''
        self.meshtype = ''
        self.meshunit = self._meshunit
        self.valueunit = self._valueunit
        self.xbase = 0.0
        self.ybase = 0.0
        self.zbase = 0.0
        self.xstepsize = 6.0
        self.ystepsize = 6.0
        self.zstepsize = 6.0
        self.xnodes = 10.0
        self.ynodes = 10.0
        self.znodes = 10.0
        self.xmin = 0.0
        self.ymin = 0.0
        self.zmin = 0.0
        self.xmax = 60.0
        self.ymax = 60.0
        self.zmax = 60.0
        self.mx = None
        self.my = None
        self.mz = None
        self.valuemultiplier = 1.
        self.valuerangeminmag = 0
        self.valuerangemaxmag = 0

    def __str__(self):
        """
        doc strings
        """
        _str = "Type:            %s\n" % self.__class__.__name__
        _str += "File:            %s\n" % self.filename
        _str += "OOMMF:           %s\n" % self.oommf
        _str += "Title:           %s\n" % self.title
        _str += "Desc:            %s\n" % self.desc
        _str += "meshtype:        %s\n" % self.meshtype
        _str += "meshunit:        %s\n" % str(self.meshunit)
        _str += "xbase:           %s [%s]\n" % (str(self.xbase), self.meshunit)
        _str += "ybase:           %s [%s]\n" % (str(self.ybase), self.meshunit)
        _str += "zbase:           %s [%s]\n" % (str(self.zbase), self.meshunit)
        _str += "xstepsize:       %s [%s]\n" % (str(self.xstepsize),
                                                self.meshunit)
        _str += "ystepsize:       %s [%s]\n" % (str(self.ystepsize),
                                                self.meshunit)
        _str += "zstepsize:       %s [%s]\n" % (str(self.zstepsize),
                                                self.meshunit)
        _str += "xnodes:          %s\n" % str(self.xnodes)
        _str += "ynodes:          %s\n" % str(self.ynodes)
        _str += "znodes:          %s\n" % str(self.znodes)
        _str += "xmin:            %s [%s]\n" % (str(self.xmin), self.meshunit)
        _str += "ymin:            %s [%s]\n" % (str(self.ymin), self.meshunit)
        _str += "zmin:            %s [%s]\n" % (str(self.zmin), self.meshunit)
        _str += "xmax:            %s [%s]\n" % (str(self.xmax), self.meshunit)
        _str += "ymax:            %s [%s]\n" % (str(self.ymax), self.meshunit)
        _str += "zmax:            %s [%s]\n" % (str(self.zmax), self.meshunit)
        _str += "valueunit:       %s\n" % self.valueunit
        _str += "valuemultiplier: %s\n" % str(self.valuemultiplier)
        _str += "ValueRangeMinMag:%s [%s]\n" % (str(self.valuerangeminmag),
                                                self.valueunit)
        _str += "ValueRangeMaxMag:%s [%s]\n" % (str(self.valuerangemaxmag),
                                                self.valueunit)
        return _str

    def set_m(self, mx, my, mz):
        """
        Set the Mx, My, Mz values
        """
        self.mx = mx
        self.my = my
        self.mz = mz

class MagSLD(object):
    """
    Magnetic SLD.
    """
    pos_x = None
    pos_y = None
    pos_z = None
    sld_n = None
    sld_mx = None
    sld_my = None
    sld_mz = None
    # Units
    _pos_unit = 'A'
    _sld_unit = '1/A^(2)'
    _pix_type = 'pixel'

    def __init__(self, pos_x, pos_y, pos_z, sld_n=None,
                 sld_mx=None, sld_my=None, sld_mz=None, vol_pix=None):
        """
        Init for mag SLD
        :params : All should be numpy 1D array
        """
        self.is_data = True
        self.filename = ''
        self.xstepsize = 6.0
        self.ystepsize = 6.0
        self.zstepsize = 6.0
        self.xnodes = 10.0
        self.ynodes = 10.0
        self.znodes = 10.0
        self.has_stepsize = False
        self.has_conect = False
        self.pos_unit = self._pos_unit
        self.sld_unit = self._sld_unit
        self.pix_type = 'pixel' if vol_pix is None else 'atom'
        self.pos_x = np.asarray(pos_x, 'd')
        self.pos_y = np.asarray(pos_y, 'd')
        self.pos_z = np.asarray(pos_z, 'd')
        self.sld_n = np.asarray(sld_n, 'd')
        self.line_x = None
        self.line_y = None
        self.line_z = None
        self.sld_mx = sld_mx
        self.sld_my = sld_my
        self.sld_mz = sld_mz
        self.vol_pix = vol_pix
        #self.sld_m = None
        #self.sld_phi = None
        #self.sld_theta = None
        #self.sld_phi = None
        self.pix_symbol = None
        if sld_mx is not None and sld_my is not None and sld_mz is not None:
            self.set_sldms(sld_mx, sld_my, sld_mz)
        if vol_pix is None:
            self.set_nodes()
        else:
            self.set_pixel_volumes(vol_pix)

    def __str__(self):
        """
        doc strings
        """
        _str = "Type:       %s\n" % self.__class__.__name__
        _str += "File:       %s\n" % self.filename
        _str += "Axis_unit:  %s\n" % self.pos_unit
        _str += "SLD_unit:   %s\n" % self.sld_unit
        return _str

    def set_pix_type(self, pix_type):
        """
        Set pixel type
        :Param pix_type: string, 'pixel' or 'atom'
        """
        self.pix_type = pix_type

    def set_sldn(self, sld_n):
        """
        Sets neutron SLD.

        Warning: if *sld_n* is a scalar and attribute *is_data* is True, then
        only pixels with non-zero magnetism will be set.
        """
        if isinstance(sld_n, float):
            if self.is_data:
                # For data, put the value to only the pixels w non-zero M
                is_nonzero = (np.fabs(self.sld_mx) +
                              np.fabs(self.sld_my) +
                              np.fabs(self.sld_mz)).nonzero()
                if len(is_nonzero[0]) > 0:
                    self.sld_n = np.zeros_like(self.pos_x)
                    self.sld_n[is_nonzero] = sld_n
                else:
                    self.sld_n = np.full_like(self.pos_x, sld_n)
            else:
                # For non-data, put the value to all the pixels
                self.sld_n = np.full_like(self.pos_x, sld_n)
        else:
            self.sld_n = sld_n

    def set_sldms(self, sld_mx, sld_my, sld_mz):
        r"""
        Sets mx, my, mz and abs(m).
        """ # Note: escaping
        if isinstance(sld_mx, float):
            self.sld_mx = np.full_like(self.pos_x, sld_mx)
        else:
            self.sld_mx = sld_mx
        if isinstance(sld_my, float):
            self.sld_my = np.full_like(self.pos_x, sld_my)
        else:
            self.sld_my = sld_my
        if isinstance(sld_mz, float):
            self.sld_mz = np.full_like(self.pos_x, sld_mz)
        else:
            self.sld_mz = sld_mz

        #sld_m = np.sqrt(sld_mx**2 + sld_my**2 + sld_mz**2)
        #if isinstance(sld_m, float):
        #    self.sld_m = np.full_like(self.pos_x, sld_m)
        #else:
        #    self.sld_m = sld_m

    def set_pixel_symbols(self, symbol='pixel'):
        """
        Set pixel
        :Params pixel: str; pixel or atomic symbol, or array of strings
        """
        if self.sld_n is None:
            return
        if symbol.__class__.__name__ == 'str':
            self.pix_symbol = np.repeat(symbol, len(self.sld_n))
        else:
            self.pix_symbol = symbol

    def set_pixel_volumes(self, vol):
        """
        Set pixel volumes
        :Params pixel: str; pixel or atomic symbol, or array of strings
        """
        if self.sld_n is None:
            return
        if isinstance(vol, np.ndarray):
            self.vol_pix = vol
        elif vol.__class__.__name__.count('float') > 0:
            self.vol_pix = np.repeat(vol, len(self.sld_n))
        else:
            # TODO: raise error rather than silently ignore
            self.vol_pix = None

    def get_sldn(self):
        """
        Returns nuclear sld
        """
        return self.sld_n

    def set_nodes(self):
        """
        Set xnodes, ynodes, and znodes
        """
        self.set_stepsize()
        if self.pix_type == 'pixel':
            try:
                xdist = (max(self.pos_x) - min(self.pos_x)) / self.xstepsize
                ydist = (max(self.pos_y) - min(self.pos_y)) / self.ystepsize
                zdist = (max(self.pos_z) - min(self.pos_z)) / self.zstepsize
                self.xnodes = int(xdist) + 1
                self.ynodes = int(ydist) + 1
                self.znodes = int(zdist) + 1
            except Exception:
                # TODO: don't silently ignore errors
                self.xnodes = None
                self.ynodes = None
                self.znodes = None
        else:
            self.xnodes = None
            self.ynodes = None
            self.znodes = None

    def set_stepsize(self):
        """
        Set xtepsize, ystepsize, and zstepsize
        """
        if self.pix_type == 'pixel':
            try:
                xpos_pre = self.pos_x[0]
                ypos_pre = self.pos_y[0]
                zpos_pre = self.pos_z[0]
                for x_pos in self.pos_x:
                    if xpos_pre != x_pos:
                        self.xstepsize = np.fabs(x_pos - xpos_pre)
                        break
                for y_pos in self.pos_y:
                    if ypos_pre != y_pos:
                        self.ystepsize = np.fabs(y_pos - ypos_pre)
                        break
                for z_pos in self.pos_z:
                    if zpos_pre != z_pos:
                        self.zstepsize = np.fabs(z_pos - zpos_pre)
                        break
                #default pix volume
                self.vol_pix = np.ones(len(self.pos_x))
                vol = self.xstepsize * self.ystepsize * self.zstepsize
                self.set_pixel_volumes(vol)
                self.has_stepsize = True
            except Exception:
                # TODO: don't silently ignore errors
                self.xstepsize = None
                self.ystepsize = None
                self.zstepsize = None
                self.vol_pix = None
                self.has_stepsize = False
        else:
            self.xstepsize = None
            self.ystepsize = None
            self.zstepsize = None
            self.has_stepsize = True
        return self.xstepsize, self.ystepsize, self.zstepsize

    def set_conect_lines(self, line_x, line_y, line_z):
        """
        Set bonding line data if taken from pdb
        """
        if line_x.__class__.__name__ != 'list' or len(line_x) < 1:
            return
        if line_y.__class__.__name__ != 'list' or len(line_y) < 1:
            return
        if line_z.__class__.__name__ != 'list' or len(line_z) < 1:
            return
        self.has_conect = True
        self.line_x = line_x
        self.line_y = line_y
        self.line_z = line_z

def test():
    """
    Check that the GenSAS can load coordinates and compute I(q).
    """
    ofpath = _get_data_path("coordinate_data", "A_Raw_Example-1.omf")
    if not os.path.isfile(ofpath):
        raise ValueError("file(s) not found: %r"%(ofpath,))
    oreader = OMFReader()
    omfdata = oreader.read(ofpath)
    omf2sld = OMF2SLD()
    omf2sld.set_data(omfdata)
    model = GenSAS()
    model.set_sld_data(omf2sld.output)
    q = np.linspace(0, 0.1, 11)[1:]
    return model.runXY([q, q])

# =======================================================================
#
# Code to check the speed and correctness of the generic sas calculation.
#
# =======================================================================

def _get_data_path(*path_parts):
    from os.path import realpath, join as joinpath, dirname
    # in sas/sascalc/calculator;  want sas/sasview/test
    return joinpath(dirname(realpath(__file__)),
                    '..', '..', 'sasview', 'test', *path_parts)

def demo_load():
    """
    Check loading of coordinate data.
    """
    tfpath = _get_data_path("1d_data", "CoreXY_ShellZ.txt")
    ofpath = _get_data_path("coordinate_data", "A_Raw_Example-1.omf")
    if not os.path.isfile(tfpath) or not os.path.isfile(ofpath):
        raise ValueError("file(s) not found: %r, %r"%(tfpath, ofpath))
    reader = SLDReader()
    oreader = OMFReader()
    output = reader.read(tfpath)
    ooutput = oreader.read(ofpath)
    foutput = OMF2SLD()
    foutput.set_data(ooutput)

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = Axes3D(fig)
    ax.plot(output.pos_x, output.pos_y, output.pos_z, '.', c="g",
            alpha=0.7, markeredgecolor='gray', rasterized=True)
    #gap = 7
    #max_mx = max(output.sld_mx)
    #max_my = max(output.sld_my)
    #max_mz = max(output.sld_mz)
    #max_m = max(max_mx, max_my, max_mz)
    #x2 = output.pos_x+output.sld_mx/max_m * gap
    #y2 = output.pos_y+output.sld_my/max_m * gap
    #z2 = output.pos_z+output.sld_mz/max_m * gap
    #x_arrow = np.column_stack((output.pos_x, x2))
    #y_arrow = np.column_stack((output.pos_y, y2))
    #z_arrow = np.column_stack((output.pos_z, z2))
    #unit_x2 = output.sld_mx / max_m
    #unit_y2 = output.sld_my / max_m
    #unit_z2 = output.sld_mz / max_m
    #color_x = np.fabs(unit_x2 * 0.8)
    #color_y = np.fabs(unit_y2 * 0.8)
    #color_z = np.fabs(unit_z2 * 0.8)
    #colors = np.column_stack((color_x, color_y, color_z))
    plt.show()

def demo_save():
    """
    Check saving of coordinate data.
    """
    ofpath = _get_data_path("coordinate_data", "A_Raw_Example-1.omf")
    if not os.path.isfile(ofpath):
        raise ValueError("file(s) not found: %r"%(ofpath,))
    oreader = OMFReader()
    omfdata = oreader.read(ofpath)
    omf2sld = OMF2SLD()
    omf2sld.set_data(omfdata)
    writer = SLDReader()
    writer.write("out.txt", omf2sld.output)

def sas_gen_c(self, qx, qy=None):
    """
    C interface to sas_gen, for comparison to new python interface.

    Note: this requires the old C implementation which may have already
    been removed from the repository.
    """
    from . import _sld2i

    x, y, z = self.data_x, self.data_y, self.data_z
    if self.is_avg:
        x, y, z = transform_center(x, y, z)
    sld = self.data_sldn - self.params['solvent_SLD']
    vol = self.data_vol
    mx, my, mz = self.data_mx, self.data_my, self.data_mz
    in_spin = self.params['Up_frac_in']
    out_spin = self.params['Up_frac_out']
    s_theta = self.params['Up_theta']
    s_phi = self.params['Up_phi']
    scale = self.params['scale']
    total_volume = self.params['total_volume']
    background = self.params['background']

    is_magnetic = (mx is not None and my is not None and mz is not None)
    if not is_magnetic:
        mx = my = mz = np.zeros_like(x)
    args = (
        (1 if self.is_avg else 0),
        # WARNING: 
        # To compare new to old need to swap the inputs.  Also need to
        # reverse the sign.
        x, y, z, sld, mx, mz, my, vol, in_spin, out_spin, s_theta, s_phi)
    model = _sld2i.new_GenI(*args)
    I_out = np.empty_like(qx)
    if qy is not None and len(qy) > 0:
        qx, qy = _vec(qx), _vec(qy)
        _sld2i.genicomXY(model, qx, qy, I_out)
    else:
        qx = _vec(qx)
        _sld2i.genicom(model, qx, I_out)

    vol_correction = self.data_total_volume / total_volume
    result = (scale * vol_correction) * I_out + background
    return result

def realspace_Iq(self, qx, qy):
    """
    Compute Iq for GenSAS object using sasmodels/explore/realspace.py
    """
    from realspace import calc_Iq_magnetic, calc_Iqxy
    from realspace import calc_Pr, calc_Iq_from_Pr, calc_Iq_avg, r_bins

    x, y, z = self.data_x, self.data_y, self.data_z
    if self.is_avg:
        x, y, z = transform_center(x, y, z)
    rho = (self.data_sldn - self.params['solvent_SLD'])*1e6
    volume = self.data_vol
    rho_m = (self.data_mx, self.data_my, self.data_mz)
    in_spin = self.params['Up_frac_in']
    out_spin = self.params['Up_frac_out']
    s_theta = self.params['Up_theta']
    s_phi = self.params['Up_phi']
    scale = self.params['scale']
    total_volume = self.params['total_volume']
    background = self.params['background']

    is_magnetic = all(v is not None for v in rho_m)

    #print("qx, qy", qx, qy)
    if is_magnetic:
        rho_m = np.vstack(rho_m)*1e6

    points = np.vstack((x, y, z)).T
    if qy is None:
        if self.is_avg:
            I_out = calc_Iq_avg(qx, rho, points, volume)
        else:
            rmax = np.linalg.norm(np.max(points, axis=0) - np.min(points, axis=0))
            r = r_bins(qx, rmax, over_sampling=10)
            Pr = calc_Pr(r, rho, points, volume)
            #import pylab; pylab.plot(r, Pr); pylab.figure()
            I_out = calc_Iq_from_Pr(qx, r, Pr)
    else:
        if is_magnetic:
            I_out = calc_Iq_magnetic(
                qx, qy, rho, rho_m, points, volume,
                up_frac_i=in_spin, up_frac_f=out_spin, up_angle=s_theta, up_phi=s_phi,
                )
        else:
            I_out = calc_Iqxy(qx, qy, rho, points, volume=volume, dtype='d')

    vol_correction = self.data_total_volume / total_volume
    #print("vol correction", vol_correction, self.data_total_volume, total_volume)
    result = (scale * vol_correction) * I_out + background
    return result

# author: Ben (https://stackoverflow.com/users/874660/ben)
# https://stackoverflow.com/questions/8130823/set-matplotlib-3d-plot-aspect-ratio/19248731#19248731
def set_axis_equal_3D(ax):
    """
    Set equal axes on a 3D plot.
    """
    extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
    sz = extents[:, 1] - extents[:, 0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize/2
    for ctr, dim in zip(centers, 'xyz'):
        getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)

def compare(obj, qx, qy=None, plot_points=False, theory=None):
    """
    Compare GenSAS calculator *obj* to old C and sasmodels versions.

    *theory* is the I(q) value for the shape, if known.
    """
    from matplotlib import pyplot as plt
    from timeit import default_timer as timer

    try:
        import realspace
        use_realspace = True
    except ImportError:
        use_realspace = False

    try:
        from . import _sld2i
        # old model is too slow for large number of points
        use_oldmodel = (len(obj.data_x) <= 21000)
    except ImportError:
        use_oldmodel = False

    #use_realspace = oldmodel = False
    use_theory = (theory is not None)
    I_theory = (theory, "theory") if use_theory else None

    if use_realspace:
        start = timer()
        I_realspace = (realspace_Iq(obj, qx, qy), "realspace")
        print("realspace time:", timer() - start)
    else:
        I_realspace = None

    start = timer()
    I_new = obj.calculate_Iq(qx, qy)
    print("New time:", timer() - start)
    new_label = "New"

    if use_oldmodel:
        start = timer()
        I_old = (sas_gen_c(obj, qx, qy), "old")
        print("Old time:", timer() - start)
    else:
        I_old = None

    def select(a, b, c):
        if a is None and b is None:
            return c, None, None
        elif a is None:
            return b, c, None
        else:
            return a, b, c
    base, other, extra = select(I_theory, I_old, I_realspace)
    #base, other, extra = select(I_theory, I_realspace, I_old)

    def calc_rel_err(target, label):
        rel_error = np.abs(target - I_new)/np.abs(target)
        index = (I_new > I_new.max()/10)
        ratio = np.mean(target[index]/I_new[index])
        print(label, "rel error =", rel_error[~np.isnan(rel_error)].max(),
              ", %s/New ="%label, ratio)
    if use_theory:
        calc_rel_err(*I_theory)
    if use_oldmodel:
        calc_rel_err(*I_old)
    if use_realspace:
        calc_rel_err(*I_realspace)

    if base is not None:
        #rel_error = 0.5*np.abs(base[0] - I_new)/(np.abs(base[0])+np.abs(I_new))
        #rel_error = np.abs(base[0]/np.sum(base[0]) - I_new/np.sum(I_new))
        #rel_label = "|%s/sum(%s) - %s/sum(%s)|" % (base[1], base[1], new_label, new_label)
        rel_error = np.abs(base[0] - I_new)/np.abs(base[0])
        rel_label = "|%s - %s|/|%s|" % (base[1], new_label, base[1])
        #print(rel_label, "=", rel_error[~np.isnan(rel_error)].max())
    else:
        rel_error, rel_label = None, None

    if qy is not None and len(qy) > 0:
        plt.subplot(131)
        plt.pcolormesh(qx, qy, np.log10(I_new))
        plt.axis('equal')
        plt.title(new_label)
        plt.colorbar()

        if base is not None:
            if other is None:
                plt.subplot(131)
            else:
                plt.subplot(232)
            plt.pcolormesh(qx, qy, np.log10(base[0]))
            plt.axis('equal')
            plt.title(base[1])
            plt.colorbar()
        if other is not None:
            plt.subplot(235)
            plt.pcolormesh(qx, qy, np.log10(other[0]))
            plt.axis('equal')
            plt.colorbar()
            plt.title(other[1])
        if rel_error is not None:
            plt.subplot(133)
            if False:
                plt.pcolormesh(qx, qy, base[0] - I_new)
                plt.title("%s - %s" % (base[1], new_label))
            else:
                plt.pcolormesh(qx, qy, rel_error)
                plt.title(rel_label)
            plt.axis('equal')
            plt.colorbar()
    else:
        if use_realspace:
            plt.loglog(qx, I_realspace[0], '-', label=I_realspace[1])
        if use_oldmodel:
            plt.loglog(qx, I_old[0], '-', label=I_old[1])
        if use_theory:
            plt.loglog(qx, I_theory[0], '-', label=I_theory[1])
        plt.loglog(qx, I_new, '-', label=new_label)
        plt.legend()

    if plot_points:
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure()
        ax = Axes3D(fig)
        #ax = fig.add_subplot((111), projection='3d')
        ax.plot(obj.data_x, obj.data_y, obj.data_z, '.', c="g",
                alpha=0.7, markeredgecolor='gray', rasterized=True)
        set_axis_equal_3D(ax)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')

    plt.show()

def demo_oommf():
    """
    Calculate theory from saved OOMMF magnetic data.
    """
    path = _get_data_path("coordinate_data", "A_Raw_Example-1.omf")
    reader = OMFReader()
    omfdata = reader.read(path)
    omf2sld = OMF2SLD()
    omf2sld.set_data(omfdata)
    data = omf2sld.output
    model = GenSAS()
    model.set_sld_data(data)
    model.params['background'] = 1e-7
    q = np.linspace(-0.1, 0.1, 31)
    qx, qy = np.meshgrid(q, q)
    compare(model, qx, qy)

def demo_pdb(is_avg=False):
    """
    Calculation I(q) for object in pdb file.
    """
    #filename = "diamond.pdb"
    filename = "dna.pdb"
    path = _get_data_path("coordinate_data", filename)
    reader = PDBReader()
    data = reader.read(path)
    model = GenSAS()
    model.set_sld_data(data)
    model.set_is_avg(is_avg)
    #print(filename, "has", len(model.data_x), "points")
    q = np.linspace(0, 1, 1350)
    compare(model, q)

def demo_shape(shape='ellip', samples=2000, nq=100, view=(60, 30, 0),
               qmax=0.5, use_2d=False, **kw):
    """
    Sample from shape with analytic model.

    *shape* is one of the shapes from sasmodels/explore/realspace.py

    *samples* is the number of sample points

    *view* is the rotation angle for the shape

    *qmax* is the max q value

    *use_2d* produces a 2D shape rather

    Remaining keywords are specific to the shape.  See def build_SHAPE(...)
    in realspace.py for details.
    """
    import realspace

    builder = realspace.SHAPE_FUNCTIONS[shape]
    shape, fx, fxy = builder(**kw)
    sampling_density = samples / shape.volume
    if shape.is_magnetic:
        rho, rho_m, points = shape.sample_magnetic(sampling_density)
        rho, rho_m = rho*1e-6, rho_m*1e-6
        mx, my, mz = rho_m
        up_i, up_f, up_angle, up_phi = shape.spin
    else:
        rho, points = shape.sample(sampling_density)
        rho = rho*1e-6
        mx = my = mz = None
        up_i, up_f, up_angle, up_phi = 0.5, 0.5, 90.0, 0.0
    points = realspace.apply_view(points, view)
    volume = shape.volume / len(points)
    #print("shape, pixel volume", shape.volume, shape.volume/len(points))
    x, y, z = points.T
    data = MagSLD(x, y, z, sld_n=rho, vol_pix=volume,
                  sld_mx=mx, sld_my=my, sld_mz=mz)
    model = GenSAS()
    model.set_sld_data(data)
    #print("vol", data.vol_pix[:10], model.data_vol[:10])
    model.set_is_avg(False)
    model.params['scale'] = 1.0
    model.params['background'] = 1e-2
    model.params['Up_frac_in'] = up_i
    model.params['Up_frac_out'] = up_f
    model.params['Up_theta'] = up_angle
    model.params['Up_phi'] = up_phi
    if use_2d or shape.is_magnetic:
        q = np.linspace(-qmax, qmax, nq)
        qx, qy = np.meshgrid(q, q)
        theory = fxy(qx, qy, view)
    else:
        qmax = np.log10(qmax)
        qx = np.logspace(qmax-3, qmax, nq)
        qy = None
        theory = fx(qx)
    theory = model.params['scale']*theory + model.params['background']
    compare(model, qx, qy, plot_points=False, theory=theory)





def demo():
    """
    Run a GenSAS operation demo.
    """
    #demo_load()
    #demo_save()
    #print(test())
    #test()
    #demo_pdb(is_avg=True)
    #demo_pdb(is_avg=False)
    #demo_oommf()

    # Comparison to sasmodels.
    # See sasmodels/explore/realspace.py:build_SHAPE for parameters.
    pars = dict(
        # Shape + qrange + magnetism (only for ellip).
        #shape='ellip', rab=125, rc=50, qmax=0.1,
        #shape='ellip', rab=25, rc=50, qmax=0.1,
        shape='ellip', rab=125, rc=50, qmax=0.05, rho_m=5, theta_m=20, phi_m=30, up_i=1, up_f=0, up_angle=35, up_phi=35,

        # 1D or 2D curve (ignored for magnetism).
        #use_2d=False,
        use_2d=True,

        # Particle orientation.
        view=(30, 60, 0),

        # Number of points in the volume.
        #samples=2000, nq=100,
        samples=20000, nq=51,
        #samples=200000, nq=20,
        #samples=20000000, nq=10,
        )
    demo_shape(**pars)

def _setup_realspace_path():
    """
    Put sasmodels/explore on path so realspace
    """
    try:
        import realspace
    except ImportError:
        from os.path import join as joinpath, realpath, dirname
        path = realpath(joinpath(dirname(__file__),
                                 '..', '..', '..', '..', '..',
                                 'sasmodels', 'explore'))
        sys.path.insert(0, path)
        logger.info("inserting %r into python path for realspace", path)

if __name__ == "__main__":
    _setup_realspace_path()
    demo()

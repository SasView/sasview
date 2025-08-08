# pylint: disable=invalid-name
"""
SAS generic computation and sld file readers.

Calculation checked by sampling from an ellipsoid and comparing Iq with the
1D, 2D oriented and 2D oriented magnetic analytical model from sasmodels.
"""

import logging
import os
import sys

import numpy as np
from periodictable import formula, nsf
from scipy.spatial.transform import Rotation


def decode(s):
    return s.decode() if isinstance(s, bytes) else s

MFACTOR_AM = 2.90636E-12
MFACTOR_MT = 2.3128E-9
METER2ANG = 1.0E+10
# Avogadro constant [1/mol]
NA = 6.02214129e+23

def _vec(v):
    return np.ascontiguousarray(v, 'd') if v is not None else None

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

class GenSAS:
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
        self.data_vol = None # [A^3]
        self.is_avg = False
        self.is_elements = False
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
        self.uvw_to_UVW=Rotation.from_rotvec([0,0,0])
        self.xyz_to_UVW=Rotation.from_rotvec([0,0,0])
        self.transformed_positions = None
        self.transformed_magnetic_slds = None
        self.transformed_angles = None
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

    def reset_transformations(self):
        """Set previous transformations as invalid
        """
        self.transformed_positions = None
        self.transformed_magnetic_slds = None
        self.transformed_angles = None

    def transform_positions(self):
        """Transform position data"""
        if self.transformed_positions is not None:
            return self.transformed_positions
        position_data = np.column_stack((self.data_x, self.data_y, self.data_z))
        self.transformed_positions = np.transpose(self.xyz_to_UVW.apply(position_data))
        return self.transformed_positions

    def transform_magnetic_slds(self):
        if self.transformed_magnetic_slds is not None:
            return self.transformed_magnetic_slds
        if self.data_mx is None and self.data_my is None and self.data_mz is None:
            return None, None, None
        else:
            if self.data_mx is not None:
                data_len = len(self.data_mx)
            elif self.data_mx is not None:
                data_len = len(self.data_my)
            else:
                data_len = len(self.data_mz)
            sld_mx, sld_my, sld_mz = [sld if sld is not None else np.zeros(data_len) for sld in (self.data_mx, self.data_my, self.data_mz)]
            # apply transformation from sample coords to beamline coords
            magnetic_data = np.column_stack((sld_mx, sld_my, sld_mz))
            self.transformed_magnetic_slds = np.transpose(self.xyz_to_UVW.apply(magnetic_data))
            return self.transformed_magnetic_slds

    def transform_angles(self):
        if self.transformed_angles is not None:
            return self.transformed_angles
        s_theta = np.radians(self.params['Up_theta'])
        s_phi = np.radians(self.params['Up_phi'])
        p_hat = np.array([np.sin(s_theta) * np.cos(s_phi), np.sin(s_theta) * np.sin(s_phi), np.cos(s_theta)])
        p_hat = self.uvw_to_UVW.apply(p_hat)
        # remove floating point errors in rotation giving |value| > 1 with max and min
        s_theta = np.degrees(np.arccos(max( min( p_hat[2] , 1), -1)))
        # do not require special values for atan2 as numpy uses C standard values for cases such as (0,0)
        s_phi = np.degrees(np.arctan2(p_hat[1], p_hat[0]))
        self.transformed_angles = (s_theta, s_phi)
        return self.transformed_angles

    def calculate_Iq(self, qx, qy=None):
        """
        Evaluate the function
        :Param x: array of x-values
        :Param y: array of y-values
        :return: function value
        """
        from .geni import Iq, Iqxy
        # transform position data from sample to beamline coords
        x, y, z = self.transform_positions()
        sld = self.data_sldn - self.params['solvent_SLD']
        vol = self.data_vol
        if qy is not None and len(qy) > 0:
            # 2-D calculation
            qx, qy = _vec(qx), _vec(qy)
            # MagSLD can have sld_m = None, although in practice usually a zero array
            # if all are None can continue as normal, otherwise set None to array of zeroes to allow rotations
            mx, my, mz = self.transform_magnetic_slds()
            in_spin = self.params['Up_frac_in']
            out_spin = self.params['Up_frac_out']
            # transform angles from environment to beamline coords
            s_theta, s_phi = self.transform_angles()

            if self.is_elements:
                I_out = Iqxy(
                    qx, qy, x, y, z, sld, vol, mx, my, mz,
                    in_spin, out_spin, s_theta, s_phi,
                    self.data_elements, self.is_elements)
            else:
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

    def set_rotations(self, uvw_to_UVW=Rotation.from_rotvec([0,0,0]), xyz_to_UVW=Rotation.from_rotvec([0,0,0])):
        """Set the rotations for the coordinate systems

        The rotation matrices are given for the COMPONENTS of the vectors - that is xyz_to_UVW
        transforms the components of a vector from the xyz to UVW frame. This is the same rotation that
        transforms the basis vectors from UVW to xyz.
        """
        self.uvw_to_UVW = uvw_to_UVW
        self.xyz_to_UVW = xyz_to_UVW
        self.reset_transformations()

    # TODO: rename set_sld_data() since it does more than set sld
    def set_sld_data(self, sld_data=None):
        """
        Sets sld_data
        """
        self.sld_data = sld_data
        self.is_elements = sld_data.is_elements
        if self.is_elements:
            self.data_elements = sld_data.elements
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
        self.reset_transformations()

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
        if self.is_elements:
            msg = "The data must be a grid of pixels - not elements"
            raise ValueError(msg)
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


    def file_verification(self, nuc_data, mag_data):
        """Verifies that enabled files are compatible and can be combined

        When the user wishes to combine two different files for nuclear (nuc_data) and magnetic
        (mag_data) data they must have the same 3D data points in real-space. This function
        decides whther verification of this is necessary and if so carries it out.
        In the case that the two files have the same real-space data points in different
        orders this function re-orders the stored data within the MagSLD objects to make
        them align. The full verification is only carried out once for any pair of loaded
        files.
        """


        if not (nuc_data is not None and mag_data is not None):
            # no conflicts if only 1/0 file(s) loaded - therefore restore functionality immediately
            return True

        # ensure both files are point or element type- not a mixture
        if (nuc_data.is_elements and not mag_data.is_elements) or \
           (not nuc_data.is_elements and mag_data.is_elements):
            logging.error("ERROR: files must both be point-wise or element-wise")
            return False

        # check each file has the same number of coords
        if nuc_data.pos_x.size != mag_data.pos_x.size:
            logging.error("ERROR: files have a different number of data points")
            return False

        # check the coords match up 1-to-1
        nuc_coords = np.array(np.column_stack((nuc_data.pos_x, nuc_data.pos_y, nuc_data.pos_z)))
        mag_coords = np.array(np.column_stack((mag_data.pos_x, mag_data.pos_y, mag_data.pos_z)))
        # TODO: should this have a floating point tolerance??
        if np.array_equal(nuc_coords, mag_coords):
            if not nuc_data.is_elements:
                # arrays are already sorted in the same order, so files match
                return True
            else:
                points_already_match = True
        else:
            # now check if coords are in wrong order or don't match
            nuc_sort_order = np.lexsort((nuc_data.pos_z, nuc_data.pos_y, nuc_data.pos_x))
            mag_sort_order = np.lexsort((mag_data.pos_z, mag_data.pos_y, mag_data.pos_x))
            nuc_coords = nuc_coords[nuc_sort_order]
            mag_coords = mag_coords[mag_sort_order]
            # check if sorted data points are equal
            if np.array_equal(nuc_coords, mag_coords):
                # if data points are equal then resort both lists into the same order
                # is this too time consuming for long lists? logging info?
                # 1) coords
                nuc_data.pos_x, nuc_data.pos_y, nuc_data.pos_z = np.transpose(nuc_coords)
                mag_data.pos_x, mag_data.pos_y, mag_data.pos_z = np.transpose(mag_coords)
                # 2) mag_data array params that must be in same order as coords
                if not nuc_data.is_elements:
                    params = ["sld_n", "sld_mx", "sld_my", "sld_mz", "vol_pix", "pix_symbol"]
                else:
                    params = ["pix_symbol"]
                for item in params:
                    nuc_val = getattr(nuc_data, item)
                    if nuc_val is not None:
                        # data should already be a np array, we cast to an ndarray as a check
                        # very fast if data is already an instance of ndarray as expected because function
                        # returns the array as-is
                        setattr(nuc_data, item, np.asanyarray(nuc_val)[nuc_sort_order])
                    mag_val = getattr(mag_data, item)
                    if mag_val is not None:
                        setattr(mag_data, item, np.asanyarray(mag_val)[mag_sort_order])
                # Do NOT need to edit CONECT data (line_x, line_y, line_z as these lines are given by
                # absolute positions not references to pos_x, pos_y, pos_z).
                if not nuc_data.is_elements:
                    return True
                else:

                    points_already_match = False
            else:
                # if sorted lists not equal then data points aren't equal
                logging.error("ERROR: files have different real space position data")
                return False

        if nuc_data.are_elements_array != mag_data.are_elements_array:
            # If files don't have the same value for this they do not match anyway.
            logging.error("ERROR: files must contain the same elements")
            return False
        if nuc_data.are_elements_array: # already in np array - can check rapidly
            if points_already_match:
                if np.array_equal(nuc_data.elements, mag_data.elements): # straight match - immediately confirm
                    return True
                # convert each element into a list of vertices - do not bmag_data comparing each face separately
                # while technically with a large number of points one could describe multiple different
                # elements, this is not possible from .vtk element types - and would massively slow down verification.
                # np.unique also sorts the vertices
                nuc_elements_sort = np.unique(nuc_data.elements.reshape((nuc_data.elements.shape[0], -1)), axis=-1)
                mag_elements_sort = np.unique(mag_data.elements.reshape((mag_data.elements.shape[0], -1)), axis=-1)
            else:
                # get reverse permutation
                # when positions were changed each index was sent to a new position - this finds the
                # position each index was sent to by inverting the permuation
                nuc_permutation = np.argsort(nuc_sort_order)
                mag_permutation = np.argsort(mag_sort_order)
                nuc_elements_sort = np.unique(nuc_data.elements.reshape((nuc_data.elements.shape[0], -1)), axis=-1)
                mag_elements_sort = np.unique(mag_data.elements.reshape((mag_data.elements.shape[0], -1)), axis=-1)
                # must resort after point positions changed
                nuc_elements_sort = np.sort(nuc_permutation[nuc_elements_sort], axis=1)
                mag_elements_sort = np.sort(mag_permutation[mag_elements_sort], axis=1)
            # elements in each file should now be described by the same real space point indices
            # we sort them into order and directly compare them
            nuc_elements_sort_order = np.lexsort(np.transpose(nuc_elements_sort))
            mag_elements_sort_order = np.lexsort(np.transpose(mag_elements_sort))
            if not np.array_equal(nuc_elements_sort[nuc_elements_sort_order, :], mag_elements_sort[mag_elements_sort_order, :]):
                logging.error("ERROR: files must contain the same elements")
                return False

            # if the sorted elements did match we must reposition all the 'per cell' values so the files match
            nuc_data.elements = nuc_data.elements[nuc_elements_sort_order, ...]
            mag_data.elements = mag_data.elements[mag_elements_sort_order, ...]
            params = ["sld_n", "sld_mx", "sld_my", "sld_mz", "vol_pix"]
            for item in params:
                nuc_val = getattr(nuc_data, item)
                if nuc_val is not None:
                    # data should already be a np array, we cast to an ndarray as a check
                    # very fast if data is already an instance of ndarray as expected becuase function
                    # returns the array as-is
                    setattr(nuc_data, item, np.asanyarray(nuc_val)[nuc_elements_sort_order])
                mag_val = getattr(mag_data, item)
                if mag_val is not None:
                    setattr(mag_data, item, np.asanyarray(mag_val)[mag_elements_sort_order])
            if not points_already_match:
                # if the points were moved we must also update all indices
                nuc_data.elements = nuc_permutation[nuc_data.elements]
                mag_data.elements = mag_permutation[mag_data.elements]
            return True

        else:
            # the files have different cell types within themselves - the elements are not already in a np array
            # as np does not support jagged arrays
            nuc_elements = []
            mag_elements = []
            # get the unique vertices of each element - see the note above about how this is not technically
            # a perfect validation.
            if points_already_match:
                for element in nuc_data.elements:
                    nuc_elements.append(np.sort(list(set([vertex for face in element for vertex in face]))))
                for element in mag_data.elements:
                    mag_elements.append(np.sort(list(set([vertex for face in element for vertex in face]))))
            else:
                # ensure the real space point indices match if they were also sorted
                nuc_permutation = np.argsort(nuc_sort_order)
                mag_permutation = np.argsort(mag_sort_order)
                for element in nuc_data.elements:
                    nuc_elements.append(np.sort(list(set([nuc_permutation[vertex] for face in element for vertex in face]))))
                for element in mag_data.elements:
                    mag_elements.append(np.sort(list(set([mag_permutation[vertex] for face in element for vertex in face]))))
            nuc_lengths = [len(i) for i in nuc_elements]
            mag_lengths = [len(i) for i in mag_elements]
            if max(nuc_lengths) != max(mag_lengths): # if files have different lengthed elements cannot match
                logging.error("ERROR: files must contain the same elements")
                return False

            # sort element vertices into a np array with '-1' filling up the empty slots
            r = np.arange(max(nuc_lengths))
            nuc_elements_sort = -np.ones((len(nuc_elements), max(nuc_lengths)))
            for i in range(len(nuc_elements)):
                nuc_elements_sort[i, :nuc_lengths[i]] = nuc_elements[i]
            mag_elements_sort = -np.ones((len(mag_elements), max(mag_lengths)))
            for i in range(len(mag_elements)):
                mag_elements_sort[i, :mag_lengths[i]] = mag_elements[i]
            # sort the elements and directly compare them against each mag_data
            nuc_elements_sort_order = np.lexsort(np.transpose(nuc_elements_sort))
            mag_elements_sort_order = np.lexsort(np.transpose(mag_elements_sort))
            if not np.array_equal(nuc_elements_sort[nuc_elements_sort_order, :], mag_elements_sort[mag_elements_sort_order, :]):
                logging.error("ERROR: files must contain the same elements")
                return False

            # if the sorted elements did match we must reposition all the 'per cell' values so the files match
            nuc_data.elements = [nuc_data.elements[i] for i in nuc_elements_sort_order]
            mag_data.elements = [mag_data.elements[i] for i in mag_elements_sort_order]
            params = ["sld_n", "sld_mx", "sld_my", "sld_mz", "vol_pix"]
            for item in params:
                nuc_val = getattr(nuc_data, item)
                if nuc_val is not None:
                    # data should already be a np array, we cast to an ndarray as a check
                    # very fast if data is already an instance of ndarray as expected becuase function
                    # returns the array as-is
                    setattr(nuc_data, item, np.asanyarray(nuc_val)[nuc_elements_sort_order])
                mag_val = getattr(mag_data, item)
                if mag_val is not None:
                    setattr(mag_data, item, np.asanyarray(mag_val)[mag_elements_sort_order])
            if not points_already_match:
                nuc_data.elements = [[[nuc_permutation[v] for v in f] for f in e] for e in nuc_data.elements]
                mag_data.elements = [[[mag_permutation[v] for v in f] for f in e] for e in mag_data.elements]

        return True



class VTKReader:
    """
    Class to read and process .vtk files
    """

    type_name = "VTK"
    ## Wildcards
    type = ["vtk files (*.VTK, *.vtk)|*.vtk"]
    ## List of allowed extensions
    ext = ['.vtk', '.VTK']

    def read(self, path):
        """This function reads in a vtk file

        :param path: The filepath to be loaded
        :type path: string
        :return: A MagSLD instance containing the loaded data or None if loading failed
        :rtype: MagSLD or None
        """
        try:
            #load in the file
            # for standard see https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf
            input_f = open(path, 'rb')
            buff = decode(input_f.read())
            lines = buff.split('\n')
            #remove blank lines - allowed in file standard - returns as an iterator
            lines = filter(None, (line.rstrip(" \r") for line in lines))
            input_f.close()
            #first lines should be a file type of the form "# vtk DataFile Version x.x"
            header = next(lines)
            if len(header) < 23:
                logging.error("not a vtk file")
                return None
            elif header[:23] != "# vtk DataFile Version ":
                logging.error("not a vtk file")
                return None
            elif float(header[23:]) > 3:
                logging.error("vtk file version > 3.0")
                return None
            #skip title
            next(lines)
            #check file is ascii not binary
            if next(lines)[:5].upper() != "ASCII":
                logging.error("cannot read binary vtk")
                return None
            # determine dataset format and call appropriate loader to return a MagSLD of suitable type
            dataset_format = [item.strip() for item in next(lines).split()]
            if dataset_format[0].upper() != "DATASET":
                logging.error("vtk file must have geometry section to be used in calulator")
                return None
            if dataset_format[1].upper() == "UNSTRUCTURED_GRID":
                return self.unstructured_grid_read(lines, path)
            else:
                logging.error("vtk dataset format " + dataset_format + " is not supported")
                return None
        except Exception as error:
            logging.exception(error)
            return None

    def unstructured_grid_read(self, lines, path):
        """Processes .vtk files in ASCII unstructured_grid format

        :param lines: an iterator with the (non-empty) lines of the file, starting one line
                        after the DATASET marker
        :type lines: iterator
        :param path: The filepath to be loaded
        :type path: string
        :return: A MagSLD instance containing the loaded data or None if loading failed
        :rtype: MagSLD or None
        """
        # get information on points
        point_data = next(lines).split()
        if point_data[0].upper() != "POINTS":
            logging.error("Expected POINTS as next section in vtk file format unstructured grid")
        num_points = int(point_data[1])
        # ignore datatype  - all can be read as float in python
        # cannot read in with np as data not guaranteed to be on a grid with new lines after each point - although this is standard
        points = []
        while len(points) < 3*num_points:
            #casting to int and float can handle whitespace - shouldn't need to strip()
            points += [float(item) for item in next(lines).split()]
        points = np.array(points).reshape((num_points, 3))
        pos_x, pos_y, pos_z = np.hsplit(points, 3)
        # read in the element data
        element_data = next(lines).split()
        if element_data[0].upper() != "CELLS":
            logging.error("Expected CELLS as next section in vtk file format unstructured grid")
        num_elements = int(element_data[1])
        len_elements = int(element_data[2])
        # must load and store carfeully: filetype does not guarantee that elements are line by line
        # or all of the same type, cannot immediately cast to np array as cannot support potential jagged arrays
        elements_raw = []
        while len(elements_raw) < len_elements:
            elements_raw += [int(item) for item in next(lines).split()]
        # convert element data from a list of integers into a list of lists of element vertices
        elements_sorted = []
        elements_sizes = []
        index = 0
        while index < len(elements_raw):
            element_size = elements_raw[index]
            elements_sorted.append(elements_raw[index+1:(index+element_size+1)])
            elements_sizes.append(element_size)
            index+=element_size+1
        #sanity check the file has the same number of elements as stated
        if num_elements != len(elements_sorted):
            logging.error("error while reading cells - specified number is inconsistent with data")
            return None
        #get information on the element types
        element_type_data = next(lines).split()
        if element_type_data[0].upper() != "CELL_TYPES":
            logging.error("Expected CELL_TYPES as next section in vtk file format unstructured grid")
        num_element_types = int(element_type_data[1])
        # sanity check same number of element types as elements
        if num_element_types != num_elements:
            logging.error("error while reading cell types - specified number is inconsistent with cells")
            return None
        element_types = []
        while len(element_types) < num_element_types:
            element_types += [int(item) for item in next(lines).split()]
        # rewrite elements as list of faces with vertices
        # elements has form elements x faces x vertex_indices
        elements = [self.get_faces(elements_sorted[i], element_types[i]) for i in range(num_elements)]
        # get the volumes of each element
        vols = np.array([self.get_vols(elements_sorted[i], element_types[i], points) for i in range(num_elements)])
        # get the element attributes - nuclear/magnetic sld data
        attribute_data = self.load_data_attributes(lines, num_points, num_elements)
        if attribute_data is None:
            return None
        point_data, element_data = attribute_data
        # remove None type elements
        if None in elements:
            i = 0
            while i < len(elements):
                if elements[i] is None:
                    for data in element_data:
                        del data[0][i]
                    del elements[i]
                    del vols[i]
                else:
                    i += 1
        #convert point data to element data - for now a standard mean function
        if len(point_data) > 0:
            logging.info("Attributes provided per point - averaging to produce 'per cell' data")
            if max(elements_sizes) != min(elements_sizes):
                # If the number of vertices per cell is not constant then add 'dummy values'
                # so that array is not jagged - even with additional points np can calulate
                # much faster - so we need non-jagged arrays
                max_size = max(elements_sizes)
                points_adj = np.concatenate((points, [[0,0,0]]), axis=0) # add null point to make array non-jagged
                for attr in point_data: # add null value for new vertices to point to
                    attr[0] = np.concatenate((attr[0], [np.zeros(attr[2])]))
                new_index = len(points)
                cells_sorted_adj = np.array([i + [new_index]*(max_size-j) for i,j in zip(elements_sorted, elements_sizes)])
            else:
                points_adj = points # if aray already non-jagged no need to alter it
                cells_sorted_adj = np.array(elements_sorted)
            vertices = points_adj[cells_sorted_adj]
            means = np.mean(vertices, axis=1)
            dists = means[:, None, :]-vertices
            weights = 1/(np.sum(dists*dists, axis=2)) # use inverse distance weighting with power factor 2
            # If we added dummy values set their weights to 0 so they are not used in calulation
            if max(elements_sizes) != min(elements_sizes):
                weights[cells_sorted_adj == len(points_adj)-1] = 0
            for attr in point_data:
                vals = attr[0][cells_sorted_adj]
                val_means = np.sum(vals*weights[..., None], axis=1)/np.sum(weights[..., None], axis=1)
                element_data.append([val_means, attr[1], attr[2]])
        # identify data read in as nuclear and magnetic data - for now uses sizes rather than names
        # so the user doesn't have to get exactly the right names on the data
        if len(element_data) == 1:
            if element_data[0][2] == 1:
                sld_n = element_data[0][0]
                sld_mx = np.zeros_like(sld_n)
                sld_my = np.zeros_like(sld_n)
                sld_mz = np.zeros_like(sld_n)
            elif element_data[0][2] == 3:
                sld_mx, sld_my, sld_mz = np.hsplit(element_data[0][0], 3)
            else:
                logging.error("Data attributes did not have 1 or 3 components - cannot interpret as nuclear or magnetic SLD")
                return None
        elif len(element_data) == 2:
            if element_data[0][2] == 1 and element_data[1][2] == 3:
                sld_n = element_data[0][0]
                sld_mx, sld_my, sld_mz = np.hsplit(element_data[1][0], 3)
            elif element_data[0][2] == 3 and element_data[1][2] == 1:
                sld_n = element_data[1][0]
                sld_mx, sld_my, sld_mz = np.hsplit(element_data[0][0], 3)
            else:
                logging.error("Data attributes did not have 1 or 3 components - cannot interpret as nuclear and magnetic SLDs")
                return None
        else:
            logging.error("Data attributes cannot be interpreted as nuclear and/or magnetic SLDs")
            return None
        # need to flatten as hsplit leaves a length 1 axis
        output = MagSLD(pos_x.flatten(), pos_y.flatten(), pos_z.flatten(), sld_n.flatten(), sld_mx.flatten(), sld_my.flatten(), sld_mz.flatten())
        output.filename = os.path.basename(path)
        # check if elements can be written as np array - all elements have same number of faces - all faces have same number of vertices
        are_elements_array = False
        if all(element_types[0] == x for x in element_types) and not (element_types[0] == 13) and not (element_types[0] == 14):
            elements = np.array(elements)
            are_elements_array = True
        output.set_elements(elements, are_elements_array)
        output.set_pixel_symbols('pixel') # draw points as pixels
        output.set_pixel_volumes(vols)
        return output

    def load_data_attributes(self, lines, num_points, num_elements):
        """Extract the data attributes from the file

        In the vtk file format the data attributes (POINT_DATA and CELL_DATA) are the last part of
        the file. This function processes that data and returns it.

        :param lines: The lines from the file - with the next line being either POINT_DATA or CELL_DATA.
        :type lines: iterator
        :param num_points: The number of points in the loaded file.
        :type num_points: int
        :param num_elements: The number of elements in the loaded file.
        :type num_elements: int
        :return: Either the loaded data attributes of None if loading failed. The data is a 2-tuple of lists
                of attributes - each attribute being a list of length 3 containing:
                the data as a list, the name of the attribute and the number of components of the attribute.
                The first list in the tuple is data associated with points, and the second is data
                associated with elements.
        :rtype: 2-tuple
        """
        # get data attributes
        data_type_info = next(lines).split()
        #cell and point data can come in either order
        if data_type_info[0].strip().upper() == "CELL_DATA":
            first_set = [num_elements, "CELL_DATA", "cells"]
            second_set = [num_points, "POINT_DATA", "points"]
        elif data_type_info[0].strip().upper() == "POINT_DATA":
            first_set = [num_points, "POINT_DATA", "points"]
            second_set = [num_elements, "CELL_DATA", "cells"]
        else:
            logging.error("error while reading file line: " + data_type_info + ". Expected data attributes POINT_DATA or CELL_DATA")
            return None
        if int(data_type_info[1]) != first_set[0]:
            logging.error("error while reading " + first_set[1] + " attributes - incompatible with number of " + first_set[2])
            return None
        first_data, nextLine = self.load_attribute(lines, first_set[0])
        if first_data is None:
            return None
        if int(nextLine.split()[1]) != second_set[0]:
            logging.error("error while reading " + second_set[1] + " attributes - incompatible with number of " + second_set[2])
            return None
        second_data, _ = self.load_attribute(lines, second_set[0]) # cell_data already read by prev. function so starts from correct position
        if second_data is None:
            return None
        if data_type_info[0].strip().upper() == "CELL_DATA":
            return (second_data, first_data)
        else:
            return (first_data, second_data)

    def load_attribute(self, lines, size):
        """Returns a single set of data - either point data or element data

        :param lines: The lines of the file - with the next lines being the first after the descriptor
                        POINT_DATA or CELL_DATA.
        :type lines: iterator
        :param size: The expected length of each attribute - either the number of points or number of elements.
        :type size: int
        :return: a tuple containg both the data loaded - and the next lines in the file - which is None
                    if the file is ended.
        :rtype: 2-tuple
        """
        # loop over lines - no need to worry about infinite loop as will stop at end of file if required
        data = []
        while True:
            nextLine = next(lines, None)
            # check if end of data attributes of this type
            if nextLine is None:
                return data, None
            nextLineSplit = nextLine.split()
            attribute = []
            if nextLineSplit[0].strip().upper() == "CELL_DATA" or nextLineSplit[0].upper() == "POINT_DATA":
                return data, nextLine
            elif nextLineSplit[0].strip().upper() == "SCALARS":
                dataType = "SCALAR"
                dataName = nextLineSplit[1].strip()
                if len(nextLineSplit) <= 3:
                    components = 1
                else:
                    components = int(nextLineSplit[3]) # do not care about type - python can convert all to float
                # check for lookup table
                nextLine = next(lines)
                if not nextLine.split()[0].strip().upper() == "LOOKUP_TABLE":
                    attribute += [float(item) for item in nextLine.split()]
            elif nextLineSplit[0].strip().upper() == "VECTORS":
                dataType = "VECTOR"
                dataName = nextLineSplit[1].strip()
                components = 3
            else:
                logging.error("Data type " + nextLineSplit[0].strip() + " is not currently accepted")
                return None, None
            while len(attribute) < size*components:
                #casting to int and float can handle whitespace - shouldn't need to strip()
                attribute += [float(item) for item in next(lines).split()]
            attribute = np.reshape(np.array(attribute), (size, components))
            data.append([attribute, dataName, components])

    def get_faces(self, e, element_type):
        """Returns the faces of the elements

        This function takes in the vertices and element type of an element and returns
        a list of faces - the orientation of the vertices in each face does not appear
        to be guaranteed in the vtk file format.

        :param e: The vertices (as indices) of the element in the order as given in the .vtk file
                    specification.
        :type e: list of int
        :param element_type: The element_type (as given in the file specification).
        :type element_type: int
        :return: A list of faces which is in turn a list of vertex indices, None if the element type is not supported
        :rtype: list of list of int or None
        """
        # e = cell_elements - shortened for brevity in code
        #returns points in faces
        if element_type == 10: # tetrahedron
            return [[e[0], e[2], e[1]],
                    [e[0], e[1], e[3]],
                    [e[0], e[3], e[2]],
                    [e[1], e[2], e[3]]]
        elif element_type == 11 or element_type == 12: # voxel (rectangular cuboid) or hexahedron
            return [[e[0], e[2], e[3], e[1]],
                    [e[0], e[1], e[5], e[4]],
                    [e[1], e[3], e[7], e[5]],
                    [e[3], e[2], e[6], e[7]],
                    [e[2], e[0], e[4], e[6]],
                    [e[4], e[5], e[7], e[6]]]
        elif element_type == 13: # wedge
            return [[e[0], e[3], e[4], e[1]],
                    [e[0]. e[2], e[5], e[3]],
                    [e[1], e[4], e[5], e[2]],
                    [e[0], e[1], e[2]],
                    [e[3], e[5], e[4]]]
        elif element_type == 14: # quadrilateral based pyramid
            return [[e[0], e[3], e[2], e[1]],
                    [e[0], e[1], e[4]],
                    [e[3], e[0], e[4]],
                    [e[2], e[3], e[4]],
                    [e[1], e[2], e[4]]]
        else:
            logging.error("element type (CELL_TYPE=" + str(element_type) + ") is not supported - skipping element")
            return None

    def get_vols(self, e, element_type, v):
        """Returns the volumes of the elements

        This function takes in the vertices and element type of an element and returns
        the real space volume of each element.

        :param e: the vertices (as indexes) of the element in the order as given in the .vtk file
                    specification.
        :type e: list of int
        :param element_type: The element_type (as given in the file specification).
        :type element_type: int
        :param v: A list of real space positions which are indexed by `e`.
        :type v: list
        :return: The volume of the element.
        :rtype: float
        """
        if element_type == 10: # tetrahedron
            return np.abs(np.dot(v[e[0]]-v[e[3]], np.cross(v[e[1]]-v[e[3]], v[e[2]]-v[e[3]])))/6
        elif element_type == 11: # voxel
            return np.abs(np.dot(v[e[0]]-v[e[2]], np.cross(v[e[0]]-v[e[1]], v[e[0]]-v[e[4]])))
        elif element_type == 12: # hexahedron
            vals = np.array([[e[2], e[4], e[7], e[1]],
                             [e[0], e[1], e[2], e[4]],
                             [e[1], e[4], e[7], e[5]],
                             [e[1], e[2], e[3], e[7]],
                             [e[2], e[4], e[6], e[7]]])
            vert = v[vals]
            return np.sum(np.abs(np.sum(vert[:,0]-vert[:,3] * np.cross(vert[:,1]-vert[:,3], vert[:,2]-vert[:,3]), axis=-1)))/6
        elif element_type == 13: # wedge
            vals = np.array([[e[0], e[1], e[2], e[5]],
                             [e[0], e[1], e[3], e[5]],
                             [e[1], e[3], e[4], e[5]]])
            vert = v[vals]
            return np.sum(np.abs(np.sum(vert[:,0]-vert[:,3] * np.cross(vert[:,1]-vert[:,3], vert[:,2]-vert[:,3]), axis=-1)))/6
        elif element_type == 14: # quadrilateral based pyramid
            vals = np.array([[e[0], e[1], e[2], e[4]],
                             [e[0], e[3], e[2], e[4]]])
            vert = v[vals]
            return np.sum(np.abs(np.sum(vert[:,0]-vert[:,3] * np.cross(vert[:,1]-vert[:,3], vert[:,2]-vert[:,3]), axis=-1)))/6
        else:
            return None

class OMF2SLD:
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
        # self.remove_null_points(True, False)
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
                logging.error(exc)
        self.output = MagSLD(self.pos_x[mask], self.pos_y[mask],
                             self.pos_z[mask], self.sld_n[mask],
                             self.mx[mask], self.my[mask], self.mz[mask])
        self.output.set_pix_type('pixel')
        self.output.set_pixel_symbols('pixel')
        self.output.filename = omfdata.filename

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




class OMFReader:
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
        mx = []
        my = []
        mz = []
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
                        mx.append(_mx)
                        my.append(_my)
                        mz.append(_mz)
                    except Exception as exc:
                        # Skip non-data lines
                        logging.error(str(exc)+" when processing %r"%line)
                elif line:
                # Reading Header; Segment count ignored
                    s_line = line.split(":", 1)
                    if s_line[0].lower().count("oommf") > 0:
                        if len(s_line) < 2:
                            s_line = line.split(" ",1)
                        oommf = s_line[1].strip()

                    if s_line[0].lower().count("title") > 0:
                        title = s_line[1].strip()
                    if s_line[0].lower().count("desc") > 0:
                        desc += s_line[1].strip()
                        desc += '\n'
                    if s_line[0].lower().count("meshtype") > 0:
                        meshtype = s_line[1].strip()
                    if s_line[0].lower().count("meshunit") > 0:
                        meshunit = s_line[1].strip()
                        if meshunit.count("m") < 1:
                            msg = "Error: \n"
                            msg += "We accept only m as meshunit"
                            logging.error(msg)
                            return None
                    if s_line[0].lower().count("xbase") > 0:
                        xbase = s_line[1].strip()
                    if s_line[0].lower().count("ybase") > 0:
                        ybase = s_line[1].strip()
                    if s_line[0].lower().count("zbase") > 0:
                        zbase = s_line[1].strip()
                    if s_line[0].lower().count("xstepsize") > 0:
                        xstepsize = s_line[1].strip()
                    if s_line[0].lower().count("ystepsize") > 0:
                        ystepsize = s_line[1].strip()
                    if s_line[0].lower().count("zstepsize") > 0:
                        zstepsize = s_line[1].strip()
                    if s_line[0].lower().count("xnodes") > 0:
                        xnodes = s_line[1].strip()
                    if s_line[0].lower().count("ynodes") > 0:
                        ynodes = s_line[1].strip()
                    if s_line[0].lower().count("znodes") > 0:
                        znodes = s_line[1].strip()
                    if s_line[0].lower().count("xmin") > 0:
                        xmin = s_line[1].strip()
                    if s_line[0].lower().count("ymin") > 0:
                        ymin = s_line[1].strip()
                    if s_line[0].lower().count("zmin") > 0:
                        zmin = s_line[1].strip()
                    if s_line[0].lower().count("xmax") > 0:
                        xmax = s_line[1].strip()
                    if s_line[0].lower().count("ymax") > 0:
                        ymax = s_line[1].strip()
                    if s_line[0].lower().count("zmax") > 0:
                        zmax = s_line[1].strip()
                    if s_line[0].lower().count("valueunit") > 0:
                        valueunit = s_line[1].strip()
                        if valueunit.count("mT") < 1 and valueunit.count("A/m") < 1:
                            msg = "Error: \n"
                            msg += "We accept only mT or A/m as valueunit"
                            logging.error(msg)
                            return None
                        elif "mT" in valueunit or "A/m" in valueunit:
                            valueunit = valueunit.split(" ", 1)
                            valueunit = valueunit[0].strip()
                    if s_line[0].lower().count("valuemultiplier") > 0:
                        valuemultiplier = s_line[1].strip()
                    else:
                        valuemultiplier = 1
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
            mx = np.reshape(mx, (len(mx),))
            my = np.reshape(my, (len(my),))
            mz = np.reshape(mz, (len(mz),))
            output.set_m(mx, my, mz)
            omf2sld = OMF2SLD()
            omf2sld.set_data(output)
            output = omf2sld.get_output()
            return output
        except Exception:
            msg = "%s is not supported: \n" % path
            msg += "We accept only Text format OMF file."
            logging.warning(msg)
            return None

class PDBReader:
    """
    PDB reader class: limited for reading the lines starting with 'ATOM'
    """

    logger = logging.getLogger("sas_gen.PDBReader")

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
        connected_pairs = set()

        atom_value_dict = {}

        try:
            input_f = open(path, 'rb')
            buff = decode(input_f.read())
            lines = buff.split('\n')
            input_f.close()
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
                        pos_x.append(_pos_x)
                        pos_y.append(_pos_y)
                        pos_z.append(_pos_z)
                        try:
                            if atom_name in atom_value_dict:
                                sld_n.append(atom_value_dict[atom_name][0])
                                vol_pix.append(atom_value_dict[atom_name][1])
                            else:
                                val = nsf.neutron_sld(atom_name)[0]
                                # sld in Ang^-2 unit
                                val *= 1.0e-6
                                sld_n.append(val)
                                atom = formula(atom_name)
                                # # cm to A units
                                vol = 1.0e+24 * atom.mass / atom.density / NA
                                vol_pix.append(vol)
                                atom_value_dict[atom_name] = [val, vol]

                        except Exception:
                            self.logger.warning("Warning: set the sld of %s to zero"% atom_name)
                            sld_n.append(0.0)

                        sld_mx.append(0)
                        sld_my.append(0)
                        sld_mz.append(0)
                        pix_symbol.append(atom_name)

                    elif line[0:6] == 'CONECT':
                        # Interpret the bonding section of the PDB

                        # split remainder of line into 5 character sections
                        rest = line[6:]
                        parts = [rest[i:i+5] for i in range(0, len(rest), 5)]

                        # Convert to indices
                        bonded_indices = []
                        for part in parts:

                            try:
                                index = int(part) - 1
                                bonded_indices.append(index)

                            except ValueError:
                                pass

                        # Store pairs in canonical order
                        a = bonded_indices[0]
                        for b in bonded_indices[1:]:
                            if a > b:
                                a, b = b, a
                            connected_pairs.add((a, b))

                except Exception as exc:
                    self.logger.error(f"Failed to read line: {line}")
                    self.logger.exception(exc)
                    self.logger.error(f"Aborting reading of file {path}.")
                    return None

            # Reshape stuff for file

            pos_x = np.reshape(pos_x, (-1, ))
            pos_y = np.reshape(pos_y, (-1, ))
            pos_z = np.reshape(pos_z, (-1, ))

            n_atoms = len(pos_x)
            ordered_pairs = sorted([(a, b) for a, b in connected_pairs if a < n_atoms and b < n_atoms])  # Why *not* sort
            x_lines = [(pos_x[a], pos_x[b]) for a, b in ordered_pairs]
            y_lines = [(pos_y[a], pos_y[b]) for a, b in ordered_pairs]
            z_lines = [(pos_z[a], pos_z[b]) for a, b in ordered_pairs]

            sld_n = np.reshape(sld_n, (-1, ))

            sld_mx = np.reshape(sld_mx, (-1, ))
            sld_my = np.reshape(sld_my, (-1, ))
            sld_mz = np.reshape(sld_mz, (-1, ))

            vol_pix = np.reshape(vol_pix, (-1, ))
            pix_symbol = np.reshape(pix_symbol, (-1, ))

            output = MagSLD(pos_x, pos_y, pos_z, sld_n, sld_mx, sld_my, sld_mz)
            output.set_conect_lines(x_lines, y_lines, z_lines)
            output.filename = os.path.basename(path)
            output.set_pix_type('atom')
            output.set_pixel_symbols(pix_symbol)
            output.set_nodes()
            output.set_pixel_volumes(vol_pix)
            output.sld_unit = '1/A^(2)'
            return output

        except Exception as e:
            self.logger.exception(e)
            return None

    def write(self, path, data):
        """
        Write
        """
        print("Not implemented... ")

class SLDReader:
    """SLD reader for text files.

    format:
    1 line of header - may give any information
    n lines of data points of the form:

    4 columns: x        y       z       sld
    6 columns: x        y       z       mx      my      mz
    7 columns: x        y       z       sld     mx      my      mz
    8 columns: x        y       z       sld     mx      my      mz      volume

    where all n lines have the same format.
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
        if data is None or data.shape[0] not in (4, 6, 7, 8):
            logging.error("%r is not an sld file" % path)
            return None
        if data.shape[0] == 4:
            x, y, z, sld = data[:4]
            mx = np.zeros_like(sld)
            my = np.zeros_like(sld)
            mz = np.zeros_like(sld)
        elif data.shape[0] == 6:
            x, y, z, mx, my, mz = data[:6]
            sld = np.zeros_like(mx)
        else:
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
        if data.is_elements:
            logging.error("cannot save finite element data as a .sld file")
            return
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


class OMFData:
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

        return _str

    def set_m(self, mx, my, mz):
        """
        Set the Mx, My, Mz values
        """
        self.mx = mx
        self.my = my
        self.mz = mz

class MagSLD:
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
        :params : All should be np 1D array
        """
        self.is_data = True
        self.is_elements = False # is this a finite-element based mesh
        self.are_elements_array = False # are all elements of the same type

        self.elements = []
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

        self.line_x: list[tuple[float, float]] | None = None
        self.line_y: list[tuple[float, float]] | None = None
        self.line_z: list[tuple[float, float]] | None = None

        self.sld_mx = sld_mx
        self.sld_my = sld_my
        self.sld_mz = sld_mz

        self.vol_pix = vol_pix
        self.data_length = len(pos_x)
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

    def set_sldn(self, sld_n, non_zero_mag_only=True):
        """
        Sets neutron SLD.

        Warning: if *sld_n* is a scalar and attribute *is_data* is True, then
        only pixels with non-zero magnetism will be set by default. Use
        the argument non_zero_mag_only=False to change this
        """
        if isinstance(sld_n, float):
            if self.is_data and non_zero_mag_only:
                # For data, put the value to only the pixels w non-zero M
                is_nonzero = (np.fabs(self.sld_mx) +
                              np.fabs(self.sld_my) +
                              np.fabs(self.sld_mz)).nonzero()
                if len(is_nonzero[0]) > 0:
                    self.sld_n = np.zeros(self.data_length)
                    self.sld_n[is_nonzero] = sld_n
                else:
                    self.sld_n = np.full(self.data_length, sld_n)
            else:
                # For non-data, put the value to all the pixels
                self.sld_n = np.full(self.data_length, sld_n)
        else:
            self.sld_n = sld_n

    def set_sldms(self, sld_mx, sld_my, sld_mz):
        r"""
        Sets mx, my, mz and abs(m).
        """ # Note: escaping
        if isinstance(sld_mx, float):
            self.sld_mx = np.full(self.data_length, sld_mx)
        else:
            self.sld_mx = sld_mx
        if isinstance(sld_my, float):
            self.sld_my = np.full(self.data_length, sld_my)
        else:
            self.sld_my = sld_my
        if isinstance(sld_mz, float):
            self.sld_mz = np.full(self.data_length, sld_mz)
        else:
            self.sld_mz = sld_mz


    def set_pixel_symbols(self, symbol='pixel'):
        """
        Set pixel
        :Params pixel: str; pixel or atomic symbol, or array of strings
        """
        if self.sld_n is None:
            return
        if symbol.__class__.__name__ == 'str':
            self.pix_symbol = np.repeat(symbol, len(self.pos_x))
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
            self.vol_pix = np.repeat(vol, self.data_length)
        else:
            # TODO: raise error rather than silently ignore
            self.vol_pix = None

    def set_elements(self, elements, are_elements_array):
        """Set elements for a non-rectangular grid

        This sets element data for the object allowing non rectangular grids to be used.
        It sets a boolean flag in the class, stores the structure of the elements and
        sets the pixel type to 'element', and hence nodes and stepsize to None. Once
        this flag is enabled the sld data is expected to match up to elements as opposed
        to points.

        :param elements: The elements which describe the volume. This should be a list
            (of elements) of a list (of faces) of a list (of vertex indices). It may be a
            jagged array due to the freedom of the .vtk file format. Faces may not be
            triangulised.
        :type elements: list
        """
        self.is_elements = True
        self.are_elements_array = are_elements_array
        self.elements = elements
        self.pix_type = "elements"
        self.data_length = len(elements)
        self.set_nodes()

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
                # default pix volume
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

    def set_conect_lines(self,
                         line_x: list[tuple[float, float]],
                         line_y: list[tuple[float, float]],
                         line_z: list[tuple[float, float]]):
        """
        Set bonding line data if taken from pdb
        """
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

    model = GenSAS()
    model.set_sld_data(omfdata.output)
    q = np.linspace(0, 0.1, 11)[1:]
    return model.runXY([q, q])

# =======================================================================
#
# Code to check the speed and correctness of the generic sas calculation.
#
# =======================================================================

def _get_data_path(*path_parts):
    from os.path import dirname, realpath
    from os.path import join as joinpath
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

    writer = SLDReader()
    writer.write("out.txt", omfdata.output)

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
    from realspace import calc_Iq_avg, calc_Iq_from_Pr, calc_Iq_magnetic, calc_Iqxy, calc_Pr, r_bins

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
                up_frac_i=in_spin, up_frac_f=out_spin, up_theta=s_theta, up_phi=s_phi,
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
    extents = np.array([getattr(ax, f'get_{dim}lim')() for dim in 'xyz'])
    sz = extents[:, 1] - extents[:, 0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize/2
    for ctr, dim in zip(centers, 'xyz'):
        getattr(ax, f'set_{dim}lim')(ctr - r, ctr + r)

def compare(obj, qx, qy=None, plot_points=False, theory=None):
    """
    Compare GenSAS calculator *obj* to old C and sasmodels versions.

    *theory* is the I(q) value for the shape, if known.
    """
    from timeit import default_timer as timer

    from matplotlib import pyplot as plt

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

    data = omfdata.output
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
        up_i, up_f, up_theta, up_phi = shape.spin
    else:
        rho, points = shape.sample(sampling_density)
        rho = rho*1e-6
        mx = my = mz = None
        up_i, up_f, up_theta, up_phi = 0.5, 0.5, 90.0, 0.0
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
    model.params['Up_theta'] = up_theta
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
        shape='ellip', rab=125, rc=50, qmax=0.05, rho_m=5, theta_m=20, phi_m=30, up_i=1, up_f=0, up_theta=35, up_phi=35,

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
        from os.path import dirname, realpath
        from os.path import join as joinpath
        path = realpath(joinpath(dirname(__file__),
                                 '..', '..', '..', '..', '..',
                                 'sasmodels', 'explore'))
        sys.path.insert(0, path)
        logging.info("inserting %r into python path for realspace", path)

if __name__ == "__main__":
    _setup_realspace_path()
    demo()

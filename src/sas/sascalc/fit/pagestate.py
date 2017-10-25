"""
Class that holds a fit page state
"""
# TODO: Refactor code so we don't need to use getattr/setattr
################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# See the license text in license.txt
#
# copyright 2009, University of Tennessee
################################################################################
import time
import os
import sys
import copy
import logging
import numpy as np
import traceback

import xml.dom.minidom
from xml.dom.minidom import parseString
from xml.dom.minidom import getDOMImplementation
from lxml import etree

from sasmodels import convert
import sasmodels.weights

from sas.sasview import __version__ as SASVIEW_VERSION

import sas.sascalc.dataloader
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.readers.cansas_reader import get_content, write_node
from sas.sascalc.dataloader.data_info import Data2D, Collimation, Detector
from sas.sascalc.dataloader.data_info import Process, Aperture

logger = logging.getLogger(__name__)

# Information to read/write state as xml
FITTING_NODE_NAME = 'fitting_plug_in'
CANSAS_NS = {"ns": "cansas1d/1.0"}

CUSTOM_MODEL = 'Plugin Models'
CUSTOM_MODEL_OLD = 'Customized Models'

LIST_OF_DATA_ATTRIBUTES = [["is_data", "is_data", "bool"],
                           ["group_id", "data_group_id", "string"],
                           ["data_name", "data_name", "string"],
                           ["data_id", "data_id", "string"],
                           ["name", "name", "string"],
                           ["data_name", "data_name", "string"]]
LIST_OF_STATE_ATTRIBUTES = [["qmin", "qmin", "float"],
                            ["qmax", "qmax", "float"],
                            ["npts", "npts", "float"],
                            ["categorycombobox", "categorycombobox", "string"],
                            ["formfactorcombobox", "formfactorcombobox",
                             "string"],
                            ["structurecombobox", "structurecombobox",
                             "string"],
                            ["multi_factor", "multi_factor", "float"],
                            ["magnetic_on", "magnetic_on", "bool"],
                            ["enable_smearer", "enable_smearer", "bool"],
                            ["disable_smearer", "disable_smearer", "bool"],
                            ["pinhole_smearer", "pinhole_smearer", "bool"],
                            ["slit_smearer", "slit_smearer", "bool"],
                            ["enable_disp", "enable_disp", "bool"],
                            ["disable_disp", "disable_disp", "bool"],
                            ["dI_noweight", "dI_noweight", "bool"],
                            ["dI_didata", "dI_didata", "bool"],
                            ["dI_sqrdata", "dI_sqrdata", "bool"],
                            ["dI_idata", "dI_idata", "bool"],
                            ["enable2D", "enable2D", "bool"],
                            ["cb1", "cb1", "bool"],
                            ["tcChi", "tcChi", "float"],
                            ["dq_l", "dq_l", "float"],
                            ["dq_r", "dq_r", "float"],
                            ["dx_percent", "dx_percent", "float"],
                            ["dxl", "dxl", "float"],
                            ["dxw", "dxw", "float"]]

LIST_OF_MODEL_ATTRIBUTES = [["values", "values"],
                            ["weights", "weights"]]

DISPERSION_LIST = [["disp_obj_dict", "disp_obj_dict", "string"]]

LIST_OF_STATE_PARAMETERS = [["parameters", "parameters"],
                            ["str_parameters", "str_parameters"],
                            ["orientation_parameters", "orientation_params"],
                            ["dispersity_parameters",
                             "orientation_params_disp"],
                            ["fixed_param", "fixed_param"],
                            ["fittable_param", "fittable_param"]]
LIST_OF_DATA_2D_ATTR = [["xmin", "xmin", "float"],
                        ["xmax", "xmax", "float"],
                        ["ymin", "ymin", "float"],
                        ["ymax", "ymax", "float"],
                        ["_xaxis", "_xaxis", "string"],
                        ["_xunit", "_xunit", "string"],
                        ["_yaxis", "_yaxis", "string"],
                        ["_yunit", "_yunit", "string"],
                        ["_zaxis", "_zaxis", "string"],
                        ["_zunit", "_zunit", "string"]]
LIST_OF_DATA_2D_VALUES = [["qx_data", "qx_data", "float"],
                          ["qy_data", "qy_data", "float"],
                          ["dqx_data", "dqx_data", "float"],
                          ["dqy_data", "dqy_data", "float"],
                          ["data", "data", "float"],
                          ["q_data", "q_data", "float"],
                          ["err_data", "err_data", "float"],
                          ["mask", "mask", "bool"]]


def parse_entry_helper(node, item):
    """
    Create a numpy list from value extrated from the node

    :param node: node from each the value is stored
    :param item: list name of three strings.the two first are name of data
        attribute and the third one is the type of the value of that
        attribute. type can be string, float, bool, etc.

    : return: numpy array
    """
    if node is not None:
        if item[2] == "string":
            return str(node.get(item[0]).strip())
        elif item[2] == "bool":
            try:
                return node.get(item[0]).strip() == "True"
            except Exception:
                return None
        else:
            try:
                return float(node.get(item[0]))
            except Exception:
                return None


class PageState(object):
    """
    Contains information to reconstruct a page of the fitpanel.
    """
    def __init__(self, model=None, data=None):
        """
        Initialize the current state

        :param model: a selected model within a page
        :param data:

        """
        self.file = None
        # Time of state creation
        self.timestamp = time.time()
        # Data member to store the dispersion object created
        self.disp_obj_dict = {}
        # ------------------------
        # Data used for fitting
        self.data = data
        # model data
        self.theory_data = None
        # Is 2D
        self.is_2D = False
        self.images = None

        # save additional information on data that dataloader.reader
        # does not read
        self.is_data = None
        self.data_name = ""

        if self.data is not None:
            self.data_name = self.data.name
        self.data_id = None
        if self.data is not None and hasattr(self.data, "id"):
            self.data_id = self.data.id
        self.data_group_id = None
        if self.data is not None and hasattr(self.data, "group_id"):
            self.data_group_id = self.data.group_id

        # reset True change the state of existing button
        self.reset = False

        # flag to allow data2D plot
        self.enable2D = False
        # model on which the fit would be performed
        self.model = model
        self.m_name = None
        # list of process done to model
        self.process = []
        # fit page manager
        self.manager = None
        # Event_owner is the owner of model event
        self.event_owner = None
        # page name
        self.page_name = ""
        # Contains link between model, its parameters, and panel organization
        self.parameters = []
        # String parameter list that can not be fitted
        self.str_parameters = []
        # Contains list of parameters that cannot be fitted and reference to
        # panel objects
        self.fixed_param = []
        # Contains list of parameters with dispersity and reference to
        # panel objects
        self.fittable_param = []
        # orientation parameters
        self.orientation_params = []
        # orientation parameters for gaussian dispersity
        self.orientation_params_disp = []
        self.dq_l = None
        self.dq_r = None
        self.dx_percent = None
        self.dx_old = False
        self.dxl = None
        self.dxw = None
        # list of dispersion parameters
        self.disp_list = []
        if self.model is not None:
            self.disp_list = self.model.getDispParamList()

        self.disp_cb_dict = {}
        self.values = {}
        self.weights = {}

        # contains link between a model and selected parameters to fit
        self.param_toFit = []
        # save the state of the context menu
        self.saved_states = {}
        # save selection of combobox
        self.formfactorcombobox = None
        self.categorycombobox = None
        self.structurecombobox = None

        # radio box to select type of model
        # self.shape_rbutton = False
        # self.shape_indep_rbutton = False
        # self.struct_rbutton = False
        # self.plugin_rbutton = False
        # the indice of the current selection
        self.disp_box = 0
        # Qrange
        # Q range
        self.qmin = 0.001
        self.qmax = 0.1
        # reset data range
        self.qmax_x = None
        self.qmin_x = None

        self.npts = None
        self.name = ""
        self.multi_factor = None
        self.magnetic_on = False
        # enable smearering state
        self.enable_smearer = False
        self.disable_smearer = True
        self.pinhole_smearer = False
        self.slit_smearer = False
        # weighting options
        self.dI_noweight = False
        self.dI_didata = True
        self.dI_sqrdata = False
        self.dI_idata = False
        # disperity selection
        self.enable_disp = False
        self.disable_disp = True

        # state of selected all check button
        self.cb1 = False
        # store value of chisqr
        self.tcChi = None
        self.version = (1, 0, 0)

    def clone(self):
        """
        Create a new copy of the current object
        """
        model = None
        if self.model is not None:
            model = self.model.clone()
            model.name = self.model.name
        obj = PageState(model=model)
        obj.file = copy.deepcopy(self.file)
        obj.data = copy.deepcopy(self.data)
        if self.data is not None:
            self.data_name = self.data.name
        obj.data_name = self.data_name
        obj.is_data = self.is_data

        obj.categorycombobox = self.categorycombobox
        obj.formfactorcombobox = self.formfactorcombobox
        obj.structurecombobox = self.structurecombobox

        # obj.shape_rbutton = self.shape_rbutton
        # obj.shape_indep_rbutton = self.shape_indep_rbutton
        # obj.struct_rbutton = self.struct_rbutton
        # obj.plugin_rbutton = self.plugin_rbutton

        obj.manager = self.manager
        obj.event_owner = self.event_owner
        obj.disp_list = copy.deepcopy(self.disp_list)

        obj.enable2D = copy.deepcopy(self.enable2D)
        obj.parameters = copy.deepcopy(self.parameters)
        obj.str_parameters = copy.deepcopy(self.str_parameters)
        obj.fixed_param = copy.deepcopy(self.fixed_param)
        obj.fittable_param = copy.deepcopy(self.fittable_param)
        obj.orientation_params = copy.deepcopy(self.orientation_params)
        obj.orientation_params_disp = \
            copy.deepcopy(self.orientation_params_disp)
        obj.enable_disp = copy.deepcopy(self.enable_disp)
        obj.disable_disp = copy.deepcopy(self.disable_disp)
        obj.tcChi = self.tcChi

        if len(self.disp_obj_dict) > 0:
            for k, v in self.disp_obj_dict.items():
                obj.disp_obj_dict[k] = v
        if len(self.disp_cb_dict) > 0:
            for k, v in self.disp_cb_dict.items():
                obj.disp_cb_dict[k] = v
        if len(self.values) > 0:
            for k, v in self.values.items():
                obj.values[k] = v
        if len(self.weights) > 0:
            for k, v in self.weights.items():
                obj.weights[k] = v
        obj.enable_smearer = copy.deepcopy(self.enable_smearer)
        obj.disable_smearer = copy.deepcopy(self.disable_smearer)
        obj.pinhole_smearer = copy.deepcopy(self.pinhole_smearer)
        obj.slit_smearer = copy.deepcopy(self.slit_smearer)
        obj.dI_noweight = copy.deepcopy(self.dI_noweight)
        obj.dI_didata = copy.deepcopy(self.dI_didata)
        obj.dI_sqrdata = copy.deepcopy(self.dI_sqrdata)
        obj.dI_idata = copy.deepcopy(self.dI_idata)
        obj.dq_l = copy.deepcopy(self.dq_l)
        obj.dq_r = copy.deepcopy(self.dq_r)
        obj.dx_percent = copy.deepcopy(self.dx_percent)
        obj.dx_old = copy.deepcopy(self.dx_old)
        obj.dxl = copy.deepcopy(self.dxl)
        obj.dxw = copy.deepcopy(self.dxw)
        obj.disp_box = copy.deepcopy(self.disp_box)
        obj.qmin = copy.deepcopy(self.qmin)
        obj.qmax = copy.deepcopy(self.qmax)
        obj.multi_factor = self.multi_factor
        obj.magnetic_on = self.magnetic_on
        obj.npts = copy.deepcopy(self.npts)
        obj.cb1 = copy.deepcopy(self.cb1)
        obj.version = copy.deepcopy(self.version)

        for name, state in self.saved_states.items():
            copy_name = copy.deepcopy(name)
            copy_state = state.clone()
            obj.saved_states[copy_name] = copy_state
        return obj

    def _old_first_model(self):
        """
        Handle save states from 4.0.1 and before where the first item in the
        selection boxes of category, formfactor and structurefactor were not
        saved.
        :return: None
        """
        if self.categorycombobox == CUSTOM_MODEL_OLD:
            self.categorycombobox = CUSTOM_MODEL
        if self.formfactorcombobox == '':
            FIRST_FORM = {
                'Shapes' : 'BCCrystalModel',
                'Uncategorized' : 'LineModel',
                'StructureFactor' : 'HardsphereStructure',
                'Ellipsoid' : 'core_shell_ellipsoid',
                'Lamellae' : 'lamellar',
                'Paracrystal' : 'bcc_paracrystal',
                'Parallelepiped' : 'core_shell_parallelepiped',
                'Shape Independent' : 'be_polyelectrolyte',
                'Sphere' : 'adsorbed_layer',
                'Structure Factor' : 'hardsphere',
                CUSTOM_MODEL : ''
            }
            if self.categorycombobox == '':
                if len(self.parameters) == 3:
                    self.categorycombobox = "Shape-Independent"
                    self.formfactorcombobox = 'PowerLawAbsModel'
                elif len(self.parameters) == 9:
                    self.categorycombobox = 'Cylinder'
                    self.formfactorcombobox = 'barbell'
                else:
                    msg = "Save state does not have enough information to load"
                    msg += " the all of the data."
                    logger.warning(msg=msg)
            else:
                self.formfactorcombobox = FIRST_FORM[self.categorycombobox]

    @staticmethod
    def param_remap_to_sasmodels_convert(params, is_string=False):
        """
        Remaps the parameters for sasmodels conversion

        :param params: list of parameters (likely self.parameters)
        :return: remapped dictionary of parameters
        """
        p = dict()
        for fittable, name, value, _, uncert, lower, upper, units in params:
            if not value:
                value = np.nan
            if not uncert or uncert[1] == '' or uncert[1] == 'None':
                uncert[0] = False
                uncert[1] = np.nan
            if not upper or upper[1] == '' or upper[1] == 'None':
                upper[0] = False
                upper[1] = np.nan
            if not lower or lower[1] == '' or lower[1] == 'None':
                lower[0] = False
                lower[1] = np.nan
            if is_string:
                p[name] = str(value)
            else:
                p[name] = float(value)
            p[name + ".fittable"] = bool(fittable)
            p[name + ".std"] = float(uncert[1])
            p[name + ".upper"] = float(upper[1])
            p[name + ".lower"] = float(lower[1])
            p[name + ".units"] = units
        return p

    @staticmethod
    def param_remap_from_sasmodels_convert(params):
        """
        Converts {name : value} map back to [] param list
        :param params: parameter map returned from sasmodels
        :return: None
        """
        p_map = []
        for name, info in params.items():
            if ".fittable" in name or ".std" in name or ".upper" in name or \
                            ".lower" in name or ".units" in name:
                pass
            else:
                fittable = params.get(name + ".fittable", True)
                std = params.get(name + ".std", '0.0')
                upper = params.get(name + ".upper", 'inf')
                lower = params.get(name + ".lower", '-inf')
                units = params.get(name + ".units")
                if std is not None and std is not np.nan:
                    std = [True, str(std)]
                else:
                    std = [False, '']
                if lower is not None and lower is not np.nan:
                    lower = [True, str(lower)]
                else:
                    lower = [True, '-inf']
                if upper is not None and upper is not np.nan:
                    upper = [True, str(upper)]
                else:
                    upper = [True, 'inf']
                param_list = [bool(fittable), str(name), str(info),
                              "+/-", std, lower, upper, str(units)]
                p_map.append(param_list)
        return p_map

    def _convert_to_sasmodels(self):
        """
        Convert parameters to a form usable by sasmodels converter

        :return: None
        """
        # Create conversion dictionary to send to sasmodels
        self._old_first_model()
        p = self.param_remap_to_sasmodels_convert(self.parameters)
        structurefactor, params = convert.convert_model(self.structurecombobox,
                                                        p, False, self.version)
        formfactor, params = convert.convert_model(self.formfactorcombobox,
                                                   params, False, self.version)
        if len(self.str_parameters) > 0:
            str_pars = self.param_remap_to_sasmodels_convert(
                self.str_parameters, True)
            formfactor, str_params = convert.convert_model(
                self.formfactorcombobox, str_pars, False, self.version)
            for key, value in str_params.items():
                params[key] = value

        if self.formfactorcombobox == 'SphericalSLDModel':
            self.multi_factor += 1
        self.formfactorcombobox = formfactor
        self.structurecombobox = structurefactor
        self.parameters = []
        self.parameters = self.param_remap_from_sasmodels_convert(params)

    def _repr_helper(self, list, rep):
        """
        Helper method to print a state
        """
        for item in list:
            rep += "parameter name: %s \n" % str(item[1])
            rep += "value: %s\n" % str(item[2])
            rep += "selected: %s\n" % str(item[0])
            rep += "error displayed : %s \n" % str(item[4][0])
            rep += "error value:%s \n" % str(item[4][1])
            rep += "minimum displayed : %s \n" % str(item[5][0])
            rep += "minimum value : %s \n" % str(item[5][1])
            rep += "maximum displayed : %s \n" % str(item[6][0])
            rep += "maximum value : %s \n" % str(item[6][1])
            rep += "parameter unit: %s\n\n" % str(item[7])
        return rep

    def __repr__(self):
        """
        output string for printing
        """
        rep = "\nState name: %s\n" % self.file
        t = time.localtime(self.timestamp)
        time_str = time.strftime("%b %d %Y %H:%M:%S ", t)

        rep += "State created: %s\n" % time_str
        rep += "State form factor combobox selection: %s\n" % \
               self.formfactorcombobox
        rep += "State structure factor combobox selection: %s\n" % \
               self.structurecombobox
        rep += "is data : %s\n" % self.is_data
        rep += "data's name : %s\n" % self.data_name
        rep += "data's id : %s\n" % self.data_id
        if self.model is not None:
            m_name = self.model.__class__.__name__
            if m_name == 'Model':
                m_name = self.m_name
            rep += "model name : %s\n" % m_name
        else:
            rep += "model name : None\n"
        rep += "multi_factor : %s\n" % str(self.multi_factor)
        rep += "magnetic_on : %s\n" % str(self.magnetic_on)
        rep += "model type (Category) selected: %s\n" % self.categorycombobox
        rep += "data : %s\n" % str(self.data)
        rep += "Plotting Range: min: %s, max: %s, steps: %s\n" % \
               (str(self.qmin), str(self.qmax), str(self.npts))
        rep += "Dispersion selection : %s\n" % str(self.disp_box)
        rep += "Smearing enable : %s\n" % str(self.enable_smearer)
        rep += "Smearing disable : %s\n" % str(self.disable_smearer)
        rep += "Pinhole smearer enable : %s\n" % str(self.pinhole_smearer)
        rep += "Slit smearer enable : %s\n" % str(self.slit_smearer)
        rep += "Dispersity enable : %s\n" % str(self.enable_disp)
        rep += "Dispersity disable : %s\n" % str(self.disable_disp)
        rep += "Slit smearer enable: %s\n" % str(self.slit_smearer)

        rep += "dI_noweight : %s\n" % str(self.dI_noweight)
        rep += "dI_didata : %s\n" % str(self.dI_didata)
        rep += "dI_sqrdata : %s\n" % str(self.dI_sqrdata)
        rep += "dI_idata : %s\n" % str(self.dI_idata)

        rep += "2D enable : %s\n" % str(self.enable2D)
        rep += "All parameters checkbox selected: %s\n" % self.cb1
        rep += "Value of Chisqr : %s\n" % str(self.tcChi)
        rep += "dq_l  : %s\n" % self.dq_l
        rep += "dq_r  : %s\n" % self.dq_r
        rep += "dx_percent  : %s\n" % str(self.dx_percent)
        rep += "dxl  : %s\n" % str(self.dxl)
        rep += "dxw : %s\n" % str(self.dxw)
        rep += "model  : %s\n\n" % str(self.model)
        temp_parameters = []
        temp_fittable_param = []
        if self.data.__class__.__name__ == "Data2D":
            self.is_2D = True
        else:
            self.is_2D = False
        if self.data is not None:
            if not self.is_2D:
                for item in self.parameters:
                    if item not in self.orientation_params:
                        temp_parameters.append(item)
                for item in self.fittable_param:
                    if item not in self.orientation_params_disp:
                        temp_fittable_param.append(item)
            else:
                temp_parameters = self.parameters
                temp_fittable_param = self.fittable_param

            rep += "number parameters(self.parameters): %s\n" % \
                   len(temp_parameters)
            rep = self._repr_helper(list=temp_parameters, rep=rep)
            rep += "number str_parameters(self.str_parameters): %s\n" % \
                   len(self.str_parameters)
            rep = self._repr_helper(list=self.str_parameters, rep=rep)
            rep += "number fittable_param(self.fittable_param): %s\n" % \
                   len(temp_fittable_param)
            rep = self._repr_helper(list=temp_fittable_param, rep=rep)
        return rep

    def _get_report_string(self):
        """
        Get the values (strings) from __str__ for report
        """
        # Dictionary of the report strings
        repo_time = ""
        model_name = ""
        title = ""
        title_name = ""
        file_name = ""
        param_string = ""
        paramval_string = ""
        chi2_string = ""
        q_range = ""
        strings = self.__repr__()
        fixed_parameter = False
        lines = strings.split('\n')
        # get all string values from __str__()
        for line in lines:
            # Skip lines which are not key: value pairs, which includes
            # blank lines and freeform notes in SASNotes fields.
            if not ':' in line:
                #msg = "Report string expected 'name: value' but got %r" % line
                #logger.error(msg)
                continue

            name, value = [s.strip() for s in line.split(":", 1)]
            if name == "State created":
                repo_time = value
            elif name == "parameter name":
                val_name = value.split(".")
                if len(val_name) > 1:
                    if val_name[1].count("width"):
                        param_string += value + ','
                    else:
                        continue
                else:
                    param_string += value + ','
            elif name == "value":
                param_string += value + ','
            elif name == "selected":
                # remember if it is fixed when reporting error value
                fixed_parameter = (value == u'False')
            elif name == "error value":
                if fixed_parameter:
                    param_string += '(fixed),'
                else:
                    param_string += value + ','
            elif name == "parameter unit":
                param_string += value + ':'
            elif name == "Value of Chisqr":
                chi2 = ("Chi2/Npts = " + value)
                chi2_string = CENTRE % chi2
            elif name == "Title":
                if len(value.strip()) == 0:
                    continue
                title = value + " [" + repo_time + "]"
                title_name = HEADER % title
            elif name == "data":
                try:
                    # parsing "data : File:     filename [mmm dd hh:mm]"
                    name = value.split(':', 1)[1].strip()
                    file_value = "File name:" + name
                    file_name = CENTRE % file_value
                    if len(title) == 0:
                        title = name + " [" + repo_time + "]"
                        title_name = HEADER % title
                except Exception:
                    msg = "While parsing 'data: ...'\n"
                    logger.error(msg + traceback.format_exc())
            elif name == "model name":
                try:
                    modelname = "Model name:" + value
                except Exception:
                    modelname = "Model name:" + " NAN"
                model_name = CENTRE % modelname

            elif name == "Plotting Range":
                try:
                    parts = value.split(':')
                    q_range = parts[0] + " = " + parts[1] \
                            + " = " + parts[2].split(",")[0]
                    q_name = ("Q Range:    " + q_range)
                    q_range = CENTRE % q_name
                except Exception:
                    msg = "While parsing 'Plotting Range: ...'\n"
                    logger.error(msg + traceback.format_exc())

        paramval = ""
        for lines in param_string.split(":"):
            line = lines.split(",")
            if len(lines) > 0:
                param = line[0]
                param += " = " + line[1]
                if len(line[2].split()) > 0 and not line[2].count("None"):
                    param += " +- " + line[2]
                if len(line[3].split()) > 0 and not line[3].count("None"):
                    param += " " + line[3]
                if not paramval.count(param):
                    paramval += param + "\n"
                    paramval_string += CENTRE % param + "\n"

        text_string = "\n\n\n%s\n\n%s\n%s\n%s\n\n%s" % \
                      (title, file, q_name, chi2, paramval)

        title_name = self._check_html_format(title_name)
        file_name = self._check_html_format(file_name)
        title = self._check_html_format(title)

        html_string = title_name + "\n" + file_name + \
                                   "\n" + model_name + \
                                   "\n" + q_range + \
                                   "\n" + chi2_string + \
                                   "\n" + ELINE + \
                                   "\n" + paramval_string + \
                                   "\n" + ELINE + \
                                   "\n" + FEET_1 % title

        return html_string, text_string, title

    def _check_html_format(self, name):
        """
        Check string '%' for html format
        """
        if name.count('%'):
            name = name.replace('%', '&#37')

        return name

    def report(self, fig_urls):
        """
        Invoke report dialog panel

        : param figs: list of pylab figures [list]
        """
        # get the strings for report
        html_str, text_str, title = self._get_report_string()
        # Allow 2 figures to append
        image_links = [FEET_2%fig for fig in fig_urls]

        # final report html strings
        report_str = html_str + ELINE.join(image_links)

        return report_str, text_str

    def _to_xml_helper(self, thelist, element, newdoc):
        """
        Helper method to create xml file for saving state
        """
        for item in thelist:
            sub_element = newdoc.createElement('parameter')
            sub_element.setAttribute('name', str(item[1]))
            sub_element.setAttribute('value', str(item[2]))
            sub_element.setAttribute('selected_to_fit', str(item[0]))
            sub_element.setAttribute('error_displayed', str(item[4][0]))
            sub_element.setAttribute('error_value', str(item[4][1]))
            sub_element.setAttribute('minimum_displayed', str(item[5][0]))
            sub_element.setAttribute('minimum_value', str(item[5][1]))
            sub_element.setAttribute('maximum_displayed', str(item[6][0]))
            sub_element.setAttribute('maximum_value', str(item[6][1]))
            sub_element.setAttribute('unit', str(item[7]))
            element.appendChild(sub_element)

    def to_xml(self, file="fitting_state.fitv", doc=None,
               entry_node=None, batch_fit_state=None):
        """
        Writes the state of the fit panel to file, as XML.

        Compatible with standalone writing, or appending to an
        already existing XML document. In that case, the XML document is
        required. An optional entry node in the XML document may also be given.

        :param file: file to write to
        :param doc: XML document object [optional]
        :param entry_node: XML node within the XML document at which we
                           will append the data [optional]
        :param batch_fit_state: simultaneous fit state
        """
        # Check whether we have to write a standalone XML file
        if doc is None:
            impl = getDOMImplementation()
            doc_type = impl.createDocumentType(FITTING_NODE_NAME, "1.0", "1.0")
            newdoc = impl.createDocument(None, FITTING_NODE_NAME, doc_type)
            top_element = newdoc.documentElement
        else:
            # We are appending to an existing document
            newdoc = doc
            try:
                top_element = newdoc.createElement(FITTING_NODE_NAME)
            except Exception:
                string = etree.tostring(doc, pretty_print=True)
                newdoc = parseString(string)
                top_element = newdoc.createElement(FITTING_NODE_NAME)
            if entry_node is None:
                newdoc.documentElement.appendChild(top_element)
            else:
                try:
                    entry_node.appendChild(top_element)
                except Exception:
                    node_name = entry_node.tag
                    node_list = newdoc.getElementsByTagName(node_name)
                    entry_node = node_list.item(0)
                    entry_node.appendChild(top_element)

        attr = newdoc.createAttribute("version")
        attr.nodeValue = SASVIEW_VERSION
        # attr.nodeValue = '1.0'
        top_element.setAttributeNode(attr)

        # File name
        element = newdoc.createElement("filename")
        if self.file is not None:
            element.appendChild(newdoc.createTextNode(str(self.file)))
        else:
            element.appendChild(newdoc.createTextNode(str(file)))
        top_element.appendChild(element)

        element = newdoc.createElement("timestamp")
        element.appendChild(newdoc.createTextNode(time.ctime(self.timestamp)))
        attr = newdoc.createAttribute("epoch")
        attr.nodeValue = str(self.timestamp)
        element.setAttributeNode(attr)
        top_element.appendChild(element)

        # Inputs
        inputs = newdoc.createElement("Attributes")
        top_element.appendChild(inputs)

        if self.data is not None and hasattr(self.data, "group_id"):
            self.data_group_id = self.data.group_id
        if self.data is not None and hasattr(self.data, "is_data"):
            self.is_data = self.data.is_data
        if self.data is not None:
            self.data_name = self.data.name
        if self.data is not None and hasattr(self.data, "id"):
            self.data_id = self.data.id

        for item in LIST_OF_DATA_ATTRIBUTES:
            element = newdoc.createElement(item[0])
            element.setAttribute(item[0], str(getattr(self, item[1])))
            inputs.appendChild(element)

        for item in LIST_OF_STATE_ATTRIBUTES:
            element = newdoc.createElement(item[0])
            element.setAttribute(item[0], str(getattr(self, item[1])))
            inputs.appendChild(element)

        # For self.values ={ disp_param_name: [vals,...],...}
        # and for self.weights ={ disp_param_name: [weights,...],...}
        for item in LIST_OF_MODEL_ATTRIBUTES:
            element = newdoc.createElement(item[0])
            value_list = getattr(self, item[1])
            for key, value in value_list.items():
                sub_element = newdoc.createElement(key)
                sub_element.setAttribute('name', str(key))
                for val in value:
                    sub_element.appendChild(newdoc.createTextNode(str(val)))

                element.appendChild(sub_element)
            inputs.appendChild(element)

        # Create doc for the dictionary of self.disp_obj_dic
        for tagname, varname, tagtype in DISPERSION_LIST:
            element = newdoc.createElement(tagname)
            value_list = getattr(self, varname)
            for key, value in value_list.items():
                sub_element = newdoc.createElement(key)
                sub_element.setAttribute('name', str(key))
                sub_element.setAttribute('value', str(value))
                element.appendChild(sub_element)
            inputs.appendChild(element)

        for item in LIST_OF_STATE_PARAMETERS:
            element = newdoc.createElement(item[0])
            self._to_xml_helper(thelist=getattr(self, item[1]),
                                element=element, newdoc=newdoc)
            inputs.appendChild(element)

        # Combined and Simultaneous Fit Parameters
        if batch_fit_state is not None:
            batch_combo = newdoc.createElement('simultaneous_fit')
            top_element.appendChild(batch_combo)

            # Simultaneous Fit Number For Linking Later
            element = newdoc.createElement('sim_fit_number')
            element.setAttribute('fit_number', str(batch_fit_state.fit_page_no))
            batch_combo.appendChild(element)

            # Save constraints
            constraints = newdoc.createElement('constraints')
            batch_combo.appendChild(constraints)
            for constraint in batch_fit_state.constraints_list:
                if constraint.model_cbox.GetValue() != "":
                    # model_cbox, param_cbox, egal_txt, constraint,
                    # btRemove, sizer
                    doc_cons = newdoc.createElement('constraint')
                    doc_cons.setAttribute('model_cbox',
                                          str(constraint.model_cbox.GetValue()))
                    doc_cons.setAttribute('param_cbox',
                                          str(constraint.param_cbox.GetValue()))
                    doc_cons.setAttribute('egal_txt',
                                          str(constraint.egal_txt.GetLabel()))
                    doc_cons.setAttribute('constraint',
                                          str(constraint.constraint.GetValue()))
                    constraints.appendChild(doc_cons)

            # Save all models
            models = newdoc.createElement('model_list')
            batch_combo.appendChild(models)
            for model in batch_fit_state.model_list:
                doc_model = newdoc.createElement('model_list_item')
                doc_model.setAttribute('checked', str(model[0].GetValue()))
                keys = model[1].keys()
                doc_model.setAttribute('name', str(keys[0]))
                values = model[1].get(keys[0])
                doc_model.setAttribute('fit_number', str(model[2]))
                doc_model.setAttribute('fit_page_source', str(model[3]))
                doc_model.setAttribute('model_name', str(values.model.id))
                models.appendChild(doc_model)

            # Select All Checkbox
            element = newdoc.createElement('select_all')
            if batch_fit_state.select_all:
                element.setAttribute('checked', 'True')
            else:
                element.setAttribute('checked', 'False')
            batch_combo.appendChild(element)

        # Save the file
        if doc is None:
            fd = open(file, 'w')
            fd.write(newdoc.toprettyxml())
            fd.close()
            return None
        else:
            return newdoc

    def _from_xml_helper(self, node, list):
        """
        Helper function to write state to xml
        """
        for item in node:
            name = item.get('name')
            value = item.get('value')
            selected_to_fit = (item.get('selected_to_fit') == "True")
            error_displayed = (item.get('error_displayed') == "True")
            error_value = item.get('error_value')
            minimum_displayed = (item.get('minimum_displayed') == "True")
            minimum_value = item.get('minimum_value')
            maximum_displayed = (item.get('maximum_displayed') == "True")
            maximum_value = item.get('maximum_value')
            unit = item.get('unit')
            list.append([selected_to_fit, name, value, "+/-",
                         [error_displayed, error_value],
                         [minimum_displayed, minimum_value],
                         [maximum_displayed, maximum_value], unit])

    def from_xml(self, file=None, node=None):
        """
        Load fitting state from a file

        :param file: .fitv file
        :param node: node of a XML document to read from
        """
        if file is not None:
            msg = "PageState no longer supports non-CanSAS"
            msg += " format for fitting files"
            raise RuntimeError(msg)

        if node.get('version'):
            # Get the version for model conversion purposes
            self.version = tuple(int(e) for e in
                                 str.split(node.get('version'), "."))
            # The tuple must be at least 3 items long
            while len(self.version) < 3:
                ver_list = list(self.version)
                ver_list.append(0)
                self.version = tuple(ver_list)

            # Get file name
            entry = get_content('ns:filename', node)
            if entry is not None and entry.text:
                self.file = entry.text.strip()
            else:
                self.file = ''

            # Get time stamp
            entry = get_content('ns:timestamp', node)
            if entry is not None and entry.get('epoch'):
                try:
                    self.timestamp = float(entry.get('epoch'))
                except Exception:
                    msg = "PageState.fromXML: Could not"
                    msg += " read timestamp\n %s" % sys.exc_value
                    logger.error(msg)

            if entry is not None:
                # Parse fitting attributes
                entry = get_content('ns:Attributes', node)
                for item in LIST_OF_DATA_ATTRIBUTES:
                    node = get_content('ns:%s' % item[0], entry)
                    setattr(self, item[0], parse_entry_helper(node, item))

                dx_old_node = get_content('ns:%s' % 'dx_min', entry)
                for item in LIST_OF_STATE_ATTRIBUTES:
                    if item[0] == "dx_percent" and dx_old_node is not None:
                        dxmin = ["dx_min", "dx_min", "float"]
                        setattr(self, item[0], parse_entry_helper(dx_old_node,
                                                                  dxmin))
                        self.dx_old = True
                    else:
                        node = get_content('ns:%s' % item[0], entry)
                        setattr(self, item[0], parse_entry_helper(node, item))

                for item in LIST_OF_STATE_PARAMETERS:
                    node = get_content("ns:%s" % item[0], entry)
                    self._from_xml_helper(node=node,
                                          list=getattr(self, item[1]))

                # Recover disp_obj_dict from xml file
                self.disp_obj_dict = {}
                for tagname, varname, tagtype in DISPERSION_LIST:
                    node = get_content("ns:%s" % tagname, entry)
                    for attr in node:
                        parameter = str(attr.get('name'))
                        value = attr.get('value')
                        if value.startswith("<"):
                            try:
                                # <path.to.NamedDistribution object/instance...>
                                cls_name = value[1:].split()[0].split('.')[-1]
                                cls = getattr(sasmodels.weights, cls_name)
                                value = cls.type
                            except Exception:
                                base = "unable to load distribution %r for %s"
                                logger.error(base, value, parameter)
                                continue
                        disp_obj_dict = getattr(self, varname)
                        disp_obj_dict[parameter] = value

                # get self.values and self.weights dic. if exists
                for tagname, varname in LIST_OF_MODEL_ATTRIBUTES:
                    node = get_content("ns:%s" % tagname, entry)
                    dic = {}
                    value_list = []
                    for par in node:
                        name = par.get('name')
                        values = par.text.split()
                        # Get lines only with numbers
                        for line in values:
                            try:
                                val = float(line)
                                value_list.append(val)
                            except Exception:
                                # pass if line is empty (it happens)
                                msg = ("Error reading %r from %s %s\n"
                                       % (line, tagname, name))
                                logger.error(msg + traceback.format_exc())
                        dic[name] = np.array(value_list)
                    setattr(self, varname, dic)

class SimFitPageState(object):
    """
    State of the simultaneous fit page for saving purposes
    """

    def __init__(self):
        # Sim Fit Page Number
        self.fit_page_no = None
        # Select all data
        self.select_all = False
        # Data sets sent to fit page
        self.model_list = []
        # Data sets to be fit
        self.model_to_fit = []
        # Number of constraints
        self.no_constraint = 0
        # Dictionary of constraints
        self.constraint_dict = {}
        # List of constraints
        self.constraints_list = []

    def __repr__(self):
        # TODO: should use __str__, not __repr__ (similarly for PageState)
        # TODO: could use a nicer representation
        repr = """\
fit page number : %(fit_page_no)s
select all : %(select_all)s
model_list : %(model_list)s
model to fit : %(model_to_fit)s
number of construsts : %(no_constraint)s
constraint dict : %(constraint_dict)s
constraints list : %(constraints_list)s
"""%self.__dict__
        return repr

class Reader(CansasReader):
    """
    Class to load a .fitv fitting file
    """
    # File type
    type_name = "Fitting"

    # Wildcards
    type = ["Fitting files (*.fitv)|*.fitv"
            "SASView file (*.svs)|*.svs"]
    # List of allowed extensions
    ext = ['.fitv', '.FITV', '.svs', 'SVS']

    def __init__(self, call_back=None, cansas=True):
        CansasReader.__init__(self)
        """
        Initialize the call-back method to be called
        after we load a file

        :param call_back: call-back method
        :param cansas:  True = files will be written/read in CanSAS format
                        False = write CanSAS format

        """
        # Call back method to be executed after a file is read
        self.call_back = call_back
        # CanSAS format flag
        self.cansas = cansas
        self.state = None
        # batch fitting params for saving
        self.batchfit_params = []

    def get_state(self):
        return self.state

    def read(self, path):
        """
        Load a new P(r) inversion state from file

        :param path: file path

        """
        if self.cansas:
            return self._read_cansas(path)

    def _parse_state(self, entry):
        """
        Read a fit result from an XML node

        :param entry: XML node to read from
        :return: PageState object
        """
        # Create an empty state
        state = None
        # Locate the P(r) node
        try:
            nodes = entry.xpath('ns:%s' % FITTING_NODE_NAME,
                                namespaces=CANSAS_NS)
            if nodes:
                # Create an empty state
                state = PageState()
                state.from_xml(node=nodes[0])

        except Exception:
            logger.info("XML document does not contain fitting information.\n"
                        + traceback.format_exc())

        return state

    def _parse_simfit_state(self, entry):
        """
        Parses the saved data for a simultaneous fit
        :param entry: XML object to read from
        :return: XML object for a simultaneous fit or None
        """
        nodes = entry.xpath('ns:%s' % FITTING_NODE_NAME,
                            namespaces=CANSAS_NS)
        if nodes:
            simfitstate = nodes[0].xpath('ns:simultaneous_fit',
                                         namespaces=CANSAS_NS)
            if simfitstate:
                sim_fit_state = SimFitPageState()
                simfitstate_0 = simfitstate[0]
                all = simfitstate_0.xpath('ns:select_all',
                                          namespaces=CANSAS_NS)
                atts = all[0].attrib
                checked = atts.get('checked')
                sim_fit_state.select_all = bool(checked)
                model_list = simfitstate_0.xpath('ns:model_list',
                                                 namespaces=CANSAS_NS)
                model_list_items = model_list[0].xpath('ns:model_list_item',
                                                       namespaces=CANSAS_NS)
                for model in model_list_items:
                    attrs = model.attrib
                    sim_fit_state.model_list.append(attrs)

                constraints = simfitstate_0.xpath('ns:constraints',
                                                  namespaces=CANSAS_NS)
                constraint_list = constraints[0].xpath('ns:constraint',
                                                       namespaces=CANSAS_NS)
                for constraint in constraint_list:
                    attrs = constraint.attrib
                    sim_fit_state.constraints_list.append(attrs)

                return sim_fit_state
            else:
                return None

    def _parse_save_state_entry(self, dom):
        """
        Parse a SASentry

        :param node: SASentry node

        :return: Data1D/Data2D object

        """
        node = dom.xpath('ns:data_class', namespaces=CANSAS_NS)
        return_value, _ = self._parse_entry(dom)
        return return_value, _

    def _read_cansas(self, path):
        """
        Load data and fitting information from a CanSAS XML file.

        :param path: file path
        :return: Data1D object if a single SASentry was found,
                    or a list of Data1D objects if multiple entries were found,
                    or None of nothing was found
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        output = []
        simfitstate = None
        basename = os.path.basename(path)
        root, extension = os.path.splitext(basename)
        ext = extension.lower()
        try:
            if os.path.isfile(path):
                if ext in self.ext or ext == '.xml':
                    tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                    # Check the format version number
                    # Specifying the namespace will take care of the file
                    # format version
                    root = tree.getroot()
                    entry_list = root.xpath('ns:SASentry',
                                            namespaces=CANSAS_NS)
                    for entry in entry_list:
                        fitstate = self._parse_state(entry)
                        # state could be None when .svs file is loaded
                        # in this case, skip appending to output
                        if fitstate is not None:
                            try:
                                sas_entry, _ = self._parse_save_state_entry(
                                    entry)
                            except:
                                raise
                            sas_entry.meta_data['fitstate'] = fitstate
                            sas_entry.filename = fitstate.file
                            output.append(sas_entry)

            else:
                self.call_back(format=ext)
                raise RuntimeError("%s is not a file" % path)

            # Return output consistent with the loader's api
            if len(output) == 0:
                self.call_back(state=None, datainfo=None, format=ext)
                return None
            else:
                for data in output:
                    # Call back to post the new state
                    state = data.meta_data['fitstate']
                    t = time.localtime(state.timestamp)
                    time_str = time.strftime("%b %d %H:%M", t)
                    # Check that no time stamp is already appended
                    max_char = state.file.find("[")
                    if max_char < 0:
                        max_char = len(state.file)
                    original_fname = state.file[0:max_char]
                    state.file = original_fname + ' [' + time_str + ']'

                    if state is not None and state.is_data is not None:
                        data.is_data = state.is_data

                    data.filename = state.file
                    state.data = data
                    state.data.name = data.filename  # state.data_name
                    state.data.id = state.data_id
                    if state.is_data is not None:
                        state.data.is_data = state.is_data
                    if data.run_name is not None and len(data.run_name) != 0:
                        if isinstance(data.run_name, dict):
                            # Note: key order in dict is not guaranteed, so sort
                            name = data.run_name.keys()[0]
                        else:
                            name = data.run_name
                    else:
                        name = original_fname
                    state.data.group_id = name
                    state.version = fitstate.version
                    # store state in fitting
                    self.call_back(state=state, datainfo=data, format=ext)
                    self.state = state
                simfitstate = self._parse_simfit_state(entry)
                if simfitstate is not None:
                    self.call_back(state=simfitstate)

                return output
        except:
            self.call_back(format=ext)
            raise

    def write(self, filename, datainfo=None, fitstate=None):
        """
        Write the content of a Data1D as a CanSAS XML file only for standalone

        :param filename: name of the file to write
        :param datainfo: Data1D object
        :param fitstate: PageState object

        """
        # Sanity check
        if self.cansas:
            # Add fitting information to the XML document
            doc = self.write_toXML(datainfo, fitstate)
            # Write the XML document
        else:
            doc = fitstate.to_xml(file=filename)

        # Save the document no matter the type
        fd = open(filename, 'w')
        fd.write(doc.toprettyxml())
        fd.close()

    def write_toXML(self, datainfo=None, state=None, batchfit=None):
        """
        Write toXML, a helper for write(),
        could be used by guimanager._on_save()

        : return: xml doc
        """

        self.batchfit_params = batchfit
        if state.data is None or not state.data.is_data:
            return None
        # make sure title and data run are filled.
        if state.data.title is None or state.data.title == '':
            state.data.title = state.data.name
        if state.data.run_name is None or state.data.run_name == {}:
            state.data.run = [str(state.data.name)]
            state.data.run_name[0] = state.data.name

        data = state.data
        doc, sasentry = self._to_xml_doc(data)

        if state is not None:
            doc = state.to_xml(doc=doc, file=data.filename, entry_node=sasentry,
                               batch_fit_state=self.batchfit_params)

        return doc

# Simple html report template
HEADER = "<html>\n"
HEADER += "<head>\n"
HEADER += "<meta http-equiv=Content-Type content='text/html; "
HEADER += "charset=windows-1252'> \n"
HEADER += "<meta name=Generator >\n"
HEADER += "</head>\n"
HEADER += "<body lang=EN-US>\n"
HEADER += "<div class=WordSection1>\n"
HEADER += "<p class=MsoNormal><b><span ><center><font size='4' >"
HEADER += "%s</font></center></span></center></b></p>"
HEADER += "<p class=MsoNormal>&nbsp;</p>"
PARA = "<p class=MsoNormal><font size='4' > %s \n"
PARA += "</font></p>"
CENTRE = "<p class=MsoNormal><center><font size='4' > %s \n"
CENTRE += "</font></center></p>"
FEET_1 = \
"""
<p class=MsoNormal>&nbsp;</p>
<br>
<p class=MsoNormal><b><span ><center> <font size='4' > Graph
</font></span></center></b></p>
<p class=MsoNormal>&nbsp;</p>
<center>
<br><font size='4' >Model Computation</font>
<br><font size='4' >Data: "%s"</font><br>
"""
FEET_2 = \
"""<img src="%s" ></img>
"""
FEET_3 = \
"""</center>
</div>
</body>
</html>
"""
ELINE = """<p class=MsoNormal>&nbsp;</p>
"""

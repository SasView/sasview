################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################
"""
This module manages all data loaded into the application. Data_manager makes
available all data loaded  for the current perspective.

All modules "creating Data" posts their data to data_manager .
Data_manager  make these new data available for all other perspectives.
"""
#
# REDUNDANT CLASS!!!
# ALL THE FUNCTIONALITY IS BEING MOVED TO GuiManager.py
#
import os
import copy
import logging
import json
import time
import re
from io import BytesIO
import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Plotting.Plottables import PlottableTheory1D
from sas.qtgui.Plotting.Plottables import PlottableFit1D
from sas.qtgui.Plotting.Plottables import Text
from sas.qtgui.Plotting.Plottables import Chisq
from sas.qtgui.Plotting.Plottables import View

from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.MainWindow.DataState import DataState

# used for import/export
from sasdata.dataloader.data_info import Sample, Source, Vector

from sas.system.version import __version__ as SASVIEW_VERSION


class DataManager(object):
    """
    Manage a list of data
    """
    def __init__(self):
        """
        Store opened path and data object created at the loading time
        :param auto_plot: if True the datamanager sends data to plotting
        plugin.
        :param auto_set_data: if True the datamanager sends to the current
        perspective
        """
        self.stored_data = {}
        self.message = ""
        self.data_name_dict = {}
        self.count = 0
        self.list_of_id = []
        self.time_stamp = time.time()

    def __str__(self):
        _str  = ""
        _str += "No of states  is %s \n" % str(len(self.stored_data))
        n_count = 0
        for  value in list(self.stored_data.values()):
            n_count += 1
            _str += "State No %s \n"  % str(n_count)
            _str += str(value) + "\n"
        return _str

    def create_gui_data(self, data, path=None):
        """
        Receive data from loader and create a data to use for guiframe
        """

        if issubclass(Data2D, data.__class__):
            new_plot = Data2D(image=None, err_image=None)
        else:
            new_plot = Data1D(x=[], y=[], dx=None, dy=None)

        # Add a note with the SasView version to the data for export purposes
        if not isinstance(data.notes, list):
            data.notes = [data.notes]
        data.notes.append(f'Data file generated by SasView v{SASVIEW_VERSION}')

        new_plot.copy_from_datainfo(data)
        data.clone_without_data(clone=new_plot)
        #creating a name for data
        title = ""
        file_name = os.path.basename(path) if path is not None else os.path.basename(data.filename)
        if data.title:
            name = data.title
        elif file_name:
            name = file_name
        elif data.run:
            name = data.run[0]
        else:
            name = "data"
        name = self.rename(name)
        #find title
        if data.title.strip():
            title = data.title
        if title.strip() == "":
            title = file_name

        stripped_filename = new_plot.filename.strip()
        if not stripped_filename:
            new_plot.filename = file_name
        if stripped_filename != os.path.basename(stripped_filename):
            new_plot.filename = file_name

        new_plot.name = name
        new_plot.title = title
        ## allow to highlight data when plotted
        new_plot.interactive = True
        ## when 2 data have the same id override the 1 st plotted
        self.time_stamp += 1
        new_plot.id = str(name) + str(self.time_stamp)
        ##group_id specify on which panel to plot this data
        new_plot.group_id = str(name) + str(self.time_stamp)
        new_plot.is_data = True
        new_plot.path = path
        new_plot.list_group_id = []
        # Assign the plot role to data
        new_plot.plot_role = DataRole.ROLE_DATA
        ##post data to plot
        # plot data
        return new_plot

    def rename(self, name):
        """
        rename data
        """
        # name of the data allow to differentiate data when plotted
        try:
            name = GuiUtils.parseName(name=name, expression="_")
        except TypeError:
            # bad name sent to rename
            return ""

        # Explicitly match [0-9]+ at the end of the name
        result = re.split(r"\[[0-9]+\]$", name)
        base_name = result[0].strip()

        # data_name_dict: {'baseName': [0, 1, .. n]}
        # Match 'test' and 'test [1]' to {'test': [0,1, .. n]}
        if base_name not in self.data_name_dict:
            self.data_name_dict[name] = [0]
        else:
            number = max(self.data_name_dict[base_name]) + 1
            self.data_name_dict[base_name].append(number)
            name = f"{base_name} [{number}]"
        return name

    def add_data(self, data_list):
        """
        receive a list of data items for storage
        """
        for id, data in data_list.items():
            if id  in self.stored_data:
                msg = "Data manager already stores %s" % str(data.name)
                msg += ""
                logging.info(msg)
                data_state = self.stored_data[id]
                data_state.data = data
            else:
                data_state = DataState(data)
                data_state.id = id
                data_state.path = data.path
                self.stored_data[id] = data_state

    def update_data(self, prev_data, new_data):
        """
        """
        if prev_data.id not in list(self.stored_data.keys()):
            return None, {}
        data_state = self.stored_data[prev_data.id]
        self.stored_data[new_data.id]  = data_state.clone()
        self.stored_data[new_data.id].data = new_data
        if prev_data.id in list(self.stored_data.keys()):
            del self.stored_data[prev_data.id]
        return prev_data.id, {new_data.id: self.stored_data[new_data.id]}

    def update_theory(self, theory, data_id=None, state=None):
        """
        """
        uid = data_id
        if data_id is None and theory is not None:
            uid = theory.id
        if uid in list(self.stored_data.keys()):
             data_state = self.stored_data[uid]
        else:
            data_state = DataState()
        data_state.uid = uid
        data_state.set_theory(theory_data=theory, theory_state=state)
        self.stored_data[uid] = data_state
        return {uid: self.stored_data[uid]}


    def get_message(self):
        """
        return message
        """
        return self.message

    def get_by_id(self, id_list=None):
        """
        """
        _selected_data = {}
        _selected_theory_list = {}
        if id_list is None:
            return
        for d_id in self.stored_data:
            for search_id in id_list:
                data_state = self.stored_data[d_id]
                data = data_state.data
                theory_list = data_state.get_theory()
                if search_id == d_id:
                    _selected_data[search_id] = data
                if search_id in list(theory_list.keys()):
                     _selected_theory_list[search_id] = theory_list[search_id]

        return _selected_data, _selected_theory_list


    def freeze(self, theory_id):
        """
        """
        return self.freeze_theory(list(self.stored_data.keys()), theory_id)

    def freeze_theory(self, data_id, theory_id):
        """
        """
        selected_theory = {}
        for d_id in data_id:
            if d_id in self.stored_data:
                data_state = self.stored_data[d_id]
                theory_list = data_state.get_theory()
                for t_id in theory_id:
                    if t_id in list(theory_list.keys()):
                        theory_data, theory_state = theory_list[t_id]
                        new_theory = copy.deepcopy(theory_data)
                        new_theory.id  = time.time()
                        new_theory.is_data = True
                        new_theory.name += '_@' + \
                                    str(new_theory.id)[7:-1].replace('.', '')
                        new_theory.title = new_theory.name
                        new_theory.label = new_theory.name
                        selected_theory[new_theory.id] = DataState(new_theory)
                        self.stored_data[new_theory.id] = \
                                    selected_theory[new_theory.id]

        return selected_theory


    def delete_data(self, data_id, theory_id=None, delete_all=False):
        """
        """
        for d_id in data_id:
            if d_id in list(self.stored_data.keys()):
                data_state = self.stored_data[d_id]
                self.remove_item_from_data_name_dict(data_state.data.name)
                del self.stored_data[d_id]

        self.delete_theory(data_id, theory_id)
        if delete_all:
            self.stored_data = {}
            self.data_name_dict = {}

    def remove_item_from_data_name_dict(self, name):
        """
        Remove 'name' or 'name [n]' from data_name_dict
        """
        # Split on whitespace - split 'name [n]' into list of len() == 2
        data_name_split = re.split(r"\[[0-9]+\]$", name)
        base_name = data_name_split[0].strip()
        if name in self.data_name_dict:
            self.data_name_dict[name].remove(0)
            # Remove empty lists from dictionary
            if not self.data_name_dict[name]:
                del self.data_name_dict[name]
            return True
        elif base_name in self.data_name_dict:
            number_match = name[len(data_name_split[0]) - 1:].strip()
            number = int(number_match[1:-1]) if len(data_name_split) > 1 else 0
            if number in self.data_name_dict[base_name]:
                self.data_name_dict[base_name].remove(number)
            # Remove empty lists from dictionary
            if not self.data_name_dict[base_name]:
                del self.data_name_dict[base_name]
            return True
        return False

    def delete_theory(self, data_id, theory_id):
        """
        """
        for d_id in data_id:
            if d_id in self.stored_data:
                data_state = self.stored_data[d_id]
                theory_list = data_state.get_theory()
                if theory_id in list(theory_list.keys()):
                    del theory_list[theory_id]
        #del pure theory
        self.delete_by_id(theory_id)

    def delete_by_id(self, id_list=None):
        """
        save data and path
        """
        for id in id_list:
            if id in self.stored_data:
                if self.remove_item_from_data_name_dict(self.stored_data[id].name):
                    del self.stored_data[id]

    def get_by_name(self, name_list=None):
        """
        return a list of data given a list of data names
        """
        _selected_data = {}
        for selected_name in name_list:
            for id, data_state in self.stored_data.items():
                if data_state.data.name == selected_name:
                    _selected_data[id] = data_state.data
        return _selected_data

    def delete_by_name(self, name_list=None):
        """
        save data and path
        """
        for selected_name in name_list:
            stored_data = copy.deepcopy(self.stored_data)
            for id, data_state in stored_data.items():
                if data_state.data.name == selected_name:
                    if self.remove_item_from_data_name_dict(selected_name):
                        del self.stored_data[id]

    def update_stored_data(self, name_list=None):
        """ update stored data after deleting files in Data Explorer """
        self.delete_by_name(name_list)

    def get_data_state(self, data_id):
        """
        Send list of selected data
        """
        _selected_data_state = {}
        for id in data_id:
            if id in list(self.stored_data.keys()):
                _selected_data_state[id] = self.stored_data[id]
        return _selected_data_state

    def get_all_data(self):
        """
        return list of all available data
        """
        return self.stored_data

    def assign(self, other):
        self.stored_data = other.stored_data
        self.message = other.message
        self.data_name_dict = other.data_name_dict
        self.count = other.count
        self.list_of_id = other.list_of_id
        self.time_stamp = other.time_stamp

    def save_to_writable(self, fp):
        """
        save content of stored_data to fp (a .write()-supporting file-like object)
        """

        def add_type(dict, type):
            dict['__type__'] = type.__name__
            return dict

        def jdefault(o):
            """
            objects that can't otherwise be serialized need to be converted
            """
            # tuples and sets (TODO: default JSONEncoder converts tuples to lists, create custom Encoder that preserves tuples)
            if isinstance(o, (tuple, set)):
                content = { 'data': list(o) }
                return add_type(content, type(o))

            # "simple" types
            if isinstance(o, (Sample, Source, Vector)):
                return add_type(o.__dict__, type(o))
            if isinstance(o, (Plottable, View)):
                return add_type(o.__dict__, type(o))

            # DataState
            if isinstance(o, DataState):
                # don't store parent
                content = o.__dict__.copy()
                content.pop('parent')
                return add_type(content, type(o))

            # ndarray
            if isinstance(o, np.ndarray):
                buffer = BytesIO()
                np.save(buffer, o)
                buffer.seek(0)
                content = { 'data': buffer.read().decode('latin-1') }
                return add_type(content, type(o))

            # not supported
            logging.info("data cannot be serialized to json: %s" % type(o))
            return None

        json.dump(self.stored_data, fp, indent=2, sort_keys=True, default=jdefault)


    def load_from_readable(self, fp):
        """
        load content from tp to stored_data (a .read()-supporting file-like object)
        """

        supported = [
            tuple, set,
            Sample, Source, Vector,
            Plottable, Data1D, Data2D, PlottableTheory1D, PlottableFit1D, Text, Chisq, View,
            DataState, np.ndarray]

        lookup = dict((cls.__name__, cls) for cls in supported)

        class TooComplexException(Exception):
            pass

        def simple_type(cls, data, level):
            class Empty(object):
                def __init__(self):
                    for key, value in data.items():
                        setattr(self, key, generate(value, level))

            # create target object
            o = Empty()
            o.__class__ = cls

            return o

        def construct(type, data, level):
            try:
                cls = lookup[type]
            except KeyError:
                logging.info('unknown type: %s' % type)
                return None

            # tuples and sets
            if cls in (tuple, set):
                # convert list to tuple/set
                return cls(generate(data['data'], level))

            # "simple" types
            if cls in (Sample, Source, Vector):
                return simple_type(cls, data, level)
            if issubclass(cls, Plottable) or (cls == View):
                return simple_type(cls, data, level)

            # DataState
            if cls == DataState:
                o = simple_type(cls, data, level)
                o.parent = None # TODO: set to ???
                return o

            # ndarray
            if cls == np.ndarray:
                buffer = BytesIO()
                buffer.write(data['data'].encode('latin-1'))
                buffer.seek(0)
                return np.load(buffer)

            logging.info('not implemented: %s, %s' % (type, cls))
            return None

        def generate(data, level):
            if level > 16: # recursion limit (arbitrary number)
                raise TooComplexException()
            else:
                level += 1

            if isinstance(data, dict):
                try:
                    type = data['__type__']
                except KeyError:
                    # if dictionary doesn't have __type__ then it is assumed to be just an ordinary dictionary
                    o = {}
                    for key, value in data.items():
                        o[key] = generate(value, level)
                    return o

                return construct(type, data, level)

            if isinstance(data, list):
                return [generate(item, level) for item in data]

            return data

        new_stored_data = {}
        for id, data in json.load(fp).items():
            try:
                new_stored_data[id] = generate(data, 0)
            except TooComplexException:
                logging.info('unable to load %s' % id)

        self.stored_data = new_stored_data


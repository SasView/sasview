"""
Inferface containing information to store data, model, range of data, etc...
and retreive this information. This is an inferface
for a fitProblem i.e relationship between data and model.
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################
import copy

from sas.sascalc.fit.qsmearing import smear_selection

class FitProblem(object):
    """
    Define the relationship between data and model, including range, weights,
    etc.
    """
    def __init__(self):
        """
        contains information about data and model to fit
        """
        ## data used for fitting
        self.fit_data = None
        self.theory_data = None
        self.residuals = None
        # original data: should not be modified
        self.original_data = None
        ## the current model
        self.model = None
        ## if 1 this fit problem will be selected to fit , if 0
        ## it will not be selected for fit
        self.schedule = 0
        ##list containing parameter name and value
        self.list_param = []
        self.list_param2fit = []
        ## smear object to smear or not data1D
        self.smearer_computed = False
        self.smearer_enable = False
        self.smearer_computer_value = None
        ## fitting range
        self.qmin = None
        self.qmax = None
        # fit weight
        self.weight = None
        self.result = None
        self.fit_tab_caption = None
        self.name_per_page = None

    def enable_smearing(self, flag=False):
        """
        :param flag: bool.When flag is 1 get the computer smear value. When
            flag is 0 ingore smear value.
        """
        self.smearer_enable = flag

    def set_smearer(self, smearer):
        """
        save reference of  smear object on fitdata

        :param smear: smear object from DataLoader

        """
        self.smearer_computer_value = smearer

    def get_smearer(self):
        """
        return smear object
        """
        if not self.smearer_enable:
            return None
        if not self.smearer_computed:
            #smeari_selection should be call only once per fitproblem
            self.smearer_computer_value = smear_selection(self.fit_data,
                                                          self.model)
            self.smearer_computed = True
        return self.smearer_computer_value

    def save_model_name(self, name):
        """
        """
        self.name_per_page = name

    def get_name(self):
        """
        """
        return self.name_per_page

    def set_model(self, model):
        """
        associates each model with its new created name
        :param model: model selected
        :param name: name created for model
        """
        self.model = model
        self.smearer_computer_value = smear_selection(self.fit_data,
                                                      self.model)
        self.smearer_computed = True

    def get_model(self):
        """
        :return: saved model
        """
        return self.model

    def set_residuals(self, residuals):
        """
        save a copy of residual
        :param data: data selected
        """
        self.residuals = residuals

    def get_residuals(self):
        """
        :return: residuals
        """
        return self.residuals

    def set_theory_data(self, data):
        """
        save a copy of the data select to fit

        :param data: data selected

        """
        self.theory_data = copy.deepcopy(data)

    def get_theory_data(self):
        """
        :return: theory generated with the current model and data of this class
        """
        return self.theory_data

    def set_fit_data(self, data):
        """
        Store data associated with this class
        :param data: list of data selected
        """
        self.original_data = None
        self.fit_data = None
        # original data: should not be modified
        self.original_data = data
        # fit data: used for fit and can be modified for convenience
        self.fit_data = copy.deepcopy(data)
        self.smearer_computer_value = smear_selection(self.fit_data, self.model)
        self.smearer_computed = True
        self.result = None

    def get_fit_data(self):
        """
        :return: data associate with this class
        """
        return self.fit_data

    def get_origin_data(self):
        """
        """
        return self.original_data

    def set_weight(self, is2d, flag=None):
        """
        Received flag and compute error on data.
        :param flag: flag to transform error of data.
        :param is2d: flag to distinguish 1D to 2D Data
        """
        from sas.sasgui.perspectives.fitting.utils import get_weight
        # send original data for weighting
        self.weight = get_weight(data=self.original_data, is2d=is2d, flag=flag)
        if is2d:
            self.fit_data.err_data = self.weight
        else:
            self.fit_data.dy = self.weight

    def get_weight(self):
        """
        returns weight array
        """
        return self.weight

    def set_param2fit(self, list):
        """
        Store param names to fit (checked)
        :param list: list of the param names
        """
        self.list_param2fit = list

    def get_param2fit(self):
        """
        return the list param names to fit
        """
        return self.list_param2fit

    def set_model_param(self, name, value=None):
        """
        Store the name and value of a parameter of this fitproblem's model
        :param name: name of the given parameter
        :param value: value of that parameter
        """
        self.list_param.append([name, value])

    def get_model_param(self):
        """
        return list of couple of parameter name and value
        """
        return self.list_param

    def schedule_tofit(self, schedule=0):
        """
        set schedule to true to decide if this fit  must be performed
        """
        self.schedule = schedule

    def get_scheduled(self):
        """
        return true or false if a problem as being schedule for fitting
        """
        return self.schedule

    def set_range(self, qmin=None, qmax=None):
        """
        set fitting range
        :param qmin: minimum value to consider for the fit range
        :param qmax: maximum value to consider for the fit range
        """
        self.qmin = qmin
        self.qmax = qmax

    def get_range(self):
        """
        :return: fitting range

        """
        return self.qmin, self.qmax

    def clear_model_param(self):
        """
        clear constraint info
        """
        self.list_param = []

    def set_fit_tab_caption(self, caption):
        """
        """
        self.fit_tab_caption = str(caption)

    def get_fit_tab_caption(self):
        """
        """
        return self.fit_tab_caption

    def set_graph_id(self, id):
        """
        Set graph id (from data_group_id at the time the graph produced)
        """
        self.graph_id = id

    def get_graph_id(self):
        """
        Get graph_id
        """
        return self.graph_id

    def set_result(self, result):
        """
        """
        self.result = result

    def get_result(self):
        """
        get result
        """
        return self.result


class FitProblemDictionary(dict):
    """
    This module implements a dictionary of fitproblem objects
    """
    def __init__(self):
        dict.__init__(self)
        ## the current model
        self.model = None
        ## if 1 this fit problem will be selected to fit , if 0
        ## it will not be selected for fit
        self.schedule = 0
        ##list containing parameter name and value
        self.list_param = []
        ## fitting range
        self.qmin = None
        self.qmax = None
        self.graph_id = None
        self._smear_on = False
        self.scheduled = 0
        self.fit_tab_caption = ''
        self.nbr_residuals_computed = 0
        self.batch_inputs = {}
        self.batch_outputs = {}

    def enable_smearing(self, flag=False, fid=None):
        """
        :param flag: bool.When flag is 1 get the computer smear value. When
            flag is 0 ingore smear value.
        """
        self._smear_on = flag
        if fid is None:
            for value in list(self.values()):
                value.enable_smearing(flag)
        elif fid in self:
            self[fid].enable_smearing(flag)

    def set_smearer(self, smearer, fid=None):
        """
        save reference of  smear object on fitdata
        :param smear: smear object from DataLoader
        """
        if fid is None:
            for value in list(self.values()):
                value.set_smearer(smearer)
        elif fid in self:
            self[fid].set_smearer(smearer)

    def get_smearer(self, fid=None):
        """
        return smear object
        """
        if fid in self:
            return self[fid].get_smearer()

    def save_model_name(self, name, fid=None):
        """
        """
        if fid is None:
            for value in list(self.values()):
                value.save_model_name(name)
        elif fid in self:
            self[fid].save_model_name(name)

    def get_name(self, fid=None):
        """
        """
        result = []
        if fid is None:
            for value in list(self.values()):
                result.append(value.get_name())
        elif fid in self:
            result.append(self[fid].get_name())
        return result

    def set_model(self, model, fid=None):
        """
        associates each model with its new created name
        :param model: model selected
        :param name: name created for model
        """
        self.model = model
        if fid is None:
            for value in list(self.values()):
                value.set_model(self.model)
        elif fid in self:
            self[fid].set_model(self.model)

    def get_model(self, fid):
        """
        :return: saved model
        """
        if fid in self:
            return self[fid].get_model()

    def set_fit_tab_caption(self, caption):
        """
        store the caption of the page associated with object
        """
        self.fit_tab_caption = caption

    def get_fit_tab_caption(self):
        """
        Return the caption of the page associated with object
        """
        return self.fit_tab_caption

    def set_residuals(self, residuals, fid):
        """
        save a copy of residual
        :param data: data selected
        """
        if fid in self:
            self[fid].set_residuals(residuals)

    def get_residuals(self, fid):
        """
        :return: residuals
        """
        if fid in self:
            return self[fid].get_residuals()

    def set_theory_data(self, fid, data=None):
        """
        save a copy of the data select to fit
        :param data: data selected
        """
        if fid in self:
            self[fid].set_theory_data(data)

    def get_theory_data(self, fid):
        """
        :return: list of data dList
        """
        if fid in self:
            return self[fid].get_theory_data()

    def add_data(self, data):
        """
        Add data to the current dictionary of fitproblem. if data id does not
        exist create a new fit problem.
        :note: only data changes in the fit problem
        """
        if data.id not in self:
            self[data.id] = FitProblem()
        self[data.id].set_fit_data(data)

    def set_fit_data(self, data):
        """
        save a copy of the data select to fit
        :param data: data selected

        """
        self.clear()
        if data is None:
            data = []
        for d in data:
            if d is not None:
                if d.id not in self:
                    self[d.id] = FitProblem()
                self[d.id].set_fit_data(d)
                self[d.id].set_model(self.model)
                self[d.id].set_range(self.qmin, self.qmax)

    def get_fit_data(self, fid):
        """
        return data for the given fitproblem id
        :param fid: key representing a fitproblem, usually extract from data id
        """
        if fid in self:
            return self[fid].get_fit_data()

    def set_model_param(self, name, value=None, fid=None):
        """
        Store the name and value of a parameter of this fitproblem's model
        :param name: name of the given parameter
        :param value: value of that parameter
        """
        if fid is None:
            for value in list(self.values()):
                value.set_model_param(name, value)
        elif fid in self:
            self[fid].set_model_param(name, value)

    def get_model_param(self, fid):
        """
        return list of couple of parameter name and value
        """
        if fid in self:
            return self[fid].get_model_param()

    def set_param2fit(self, list):
        """
        Store param names to fit (checked)
        :param list: list of the param names
        """
        self.list_param2fit = list

    def get_param2fit(self):
        """
        return the list param names to fit
        """
        return self.list_param2fit

    def schedule_tofit(self, schedule=0):
        """
        set schedule to true to decide if this fit  must be performed
        """
        self.scheduled = schedule
        for value in list(self.values()):
            value.schedule_tofit(schedule)

    def get_scheduled(self):
        """
        return true or false if a problem as being schedule for fitting
        """
        return self.scheduled

    def set_range(self, qmin=None, qmax=None, fid=None):
        """
        set fitting range
        """
        self.qmin = qmin
        self.qmax = qmax
        if fid is None:
            for value in list(self.values()):
                value.set_range(self.qmin, self.qmax)
        elif fid in self:
            self[fid].value.set_range(self.qmin, self.qmax)

    def get_range(self, fid):
        """
        :return: fitting range
        """
        if fid in self:
            return self[fid].get_range()

    def set_weight(self, is2d, flag=None, fid=None):
        """
        fit weight
        """
        if fid is None:
            for value in list(self.values()):
                value.set_weight(flag=flag, is2d=is2d)
        elif fid in self:
            self[fid].set_weight(flag=flag, is2d=is2d)

    def get_weight(self, fid=None):
        """
        return fit weight
        """
        if fid in self:
            return self[fid].get_weight()

    def clear_model_param(self, fid=None):
        """
        clear constraint info
        """
        if fid is None:
            for value in list(self.values()):
                value.clear_model_param()
        elif fid in self:
            self[fid].clear_model_param()

    def get_fit_problem(self):
        """
        return fitproblem contained in this dictionary
        """
        return list(self.values())

    def set_result(self, result, fid):
        """
        """
        if fid in self:
            self[fid].set_result(result)

    def set_batch_result(self, batch_inputs, batch_outputs):
        """
        set a list of result
        """
        self.batch_inputs = batch_inputs
        self.batch_outputs = batch_outputs

    def get_result(self, fid):
        """
        get result
        """
        if fid in self:
            return self[fid].get_result()

    def get_batch_result(self):
        """
        get result
        """
        return self.batch_inputs, self.batch_outputs

    def set_graph_id(self, id):
        """
        Set graph id (from data_group_id at the time the graph produced)
        """
        self.graph_id = id

    def get_graph_id(self):
        """
        Get graph_id
        """
        return self.graph_id

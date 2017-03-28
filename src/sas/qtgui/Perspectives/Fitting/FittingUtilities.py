from PyQt4 import QtGui
from PyQt4 import QtCore

import numpy
from copy import deepcopy

from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D

def replaceShellName(param_name, value):
    """
    Updates parameter name from <param_name>[n_shell] to <param_name>value
    """
    assert '[' in param_name
    return param_name[:param_name.index('[')]+str(value)

def getIterParams(model):
    """
    Returns a list of all multi-shell parameters in 'model'
    """
    return list(filter(lambda par: "[" in par.name, model.iq_parameters))

def getMultiplicity(model):
    """
    Finds out if 'model' has multishell parameters.
    If so, returns the name of the counter parameter and the number of shells
    """
    iter_params = getIterParams(model)
    param_name = ""
    param_length = 0
    if iter_params:
        param_length = iter_params[0].length
        param_name = iter_params[0].length_control
        if param_name is None and '[' in iter_params[0].name:
            param_name = iter_params[0].name[:iter_params[0].name.index('[')]
    return (param_name, param_length)

def addParametersToModel(parameters, model):
    """
    Update local ModelModel with sasmodel parameters
    """
    multishell_parameters = getIterParams(parameters)
    multishell_param_name, _ = getMultiplicity(parameters)

    for param in parameters.iq_parameters:
        # don't include shell parameters
        if param.name == multishell_param_name:
            continue
        # Modify parameter name from <param>[n] to <param>1
        item_name = param.name
        if param in multishell_parameters:
            continue
        #    item_name = replaceShellName(param.name, 1)

        item1 = QtGui.QStandardItem(item_name)
        item1.setCheckable(True)
        # check for polydisp params
        if param.polydisperse:
            poly_item = QtGui.QStandardItem("Polydispersity")
            item1_1 = QtGui.QStandardItem("Distribution")
            # Find param in volume_params
            for p in parameters.form_volume_parameters:
                if p.name != param.name:
                    continue
                item1_2 = QtGui.QStandardItem(str(p.default))
                item1_3 = QtGui.QStandardItem(str(p.limits[0]))
                item1_4 = QtGui.QStandardItem(str(p.limits[1]))
                item1_5 = QtGui.QStandardItem(p.units)
                poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                break
            # Add the polydisp item as a child
            item1.appendRow([poly_item])
        # Param values
        item2 = QtGui.QStandardItem(str(param.default))
        # TODO: the error column.
        # Either add a proxy model or a custom view delegate
        #item_err = QtGui.QStandardItem()
        item3 = QtGui.QStandardItem(str(param.limits[0]))
        item4 = QtGui.QStandardItem(str(param.limits[1]))
        item5 = QtGui.QStandardItem(param.units)
        model.appendRow([item1, item2, item3, item4, item5])

def addSimpleParametersToModel(parameters, model):
    """
    Update local ModelModel with sasmodel parameters
    """
    for param in parameters.iq_parameters:
        # Create the top level, checkable item
        item_name = param.name
        item1 = QtGui.QStandardItem(item_name)
        item1.setCheckable(True)
        # Param values
        item2 = QtGui.QStandardItem(str(param.default))
        # TODO: the error column.
        # Either add a proxy model or a custom view delegate
        #item_err = QtGui.QStandardItem()
        item3 = QtGui.QStandardItem(str(param.limits[0]))
        item4 = QtGui.QStandardItem(str(param.limits[1]))
        item5 = QtGui.QStandardItem(param.units)
        model.appendRow([item1, item2, item3, item4, item5])

def addCheckedListToModel(model, param_list):
    """
    Add a QItem to model. Makes the QItem checkable
    """
    assert isinstance(model, QtGui.QStandardItemModel)
    item_list = [QtGui.QStandardItem(item) for item in param_list]
    item_list[0].setCheckable(True)
    model.appendRow(item_list)

def addHeadersToModel(model):
    """
    Adds predefined headers to the model
    """
    model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
    model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))
    model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
    model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
    model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("[Units]"))

def addPolyHeadersToModel(model):
    """
    Adds predefined headers to the model
    """
    model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Parameter"))
    model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("PD[ratio]"))
    model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("Min"))
    model.setHeaderData(3, QtCore.Qt.Horizontal, QtCore.QVariant("Max"))
    model.setHeaderData(4, QtCore.Qt.Horizontal, QtCore.QVariant("Npts"))
    model.setHeaderData(5, QtCore.Qt.Horizontal, QtCore.QVariant("Nsigs"))
    model.setHeaderData(6, QtCore.Qt.Horizontal, QtCore.QVariant("Function"))

def addShellsToModel(parameters, model, index):
    """
    Find out multishell parameters and update the model with the requested number of them
    """
    multishell_parameters = getIterParams(parameters)

    for i in xrange(index):
        for par in multishell_parameters:
            # Create the name: <param>[<i>], e.g. "sld1" for parameter "sld[n]"
            param_name = replaceShellName(par.name, i+1)
            item1 = QtGui.QStandardItem(param_name)
            item1.setCheckable(True)
            # check for polydisp params
            if par.polydisperse:
                poly_item = QtGui.QStandardItem("Polydispersity")
                item1_1 = QtGui.QStandardItem("Distribution")
                # Find param in volume_params
                for p in parameters.form_volume_parameters:
                    if p.name != par.name:
                        continue
                    item1_2 = QtGui.QStandardItem(str(p.default))
                    item1_3 = QtGui.QStandardItem(str(p.limits[0]))
                    item1_4 = QtGui.QStandardItem(str(p.limits[1]))
                    item1_5 = QtGui.QStandardItem(p.units)
                    poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                    break
                item1.appendRow([poly_item])

            item2 = QtGui.QStandardItem(str(par.default))
            item3 = QtGui.QStandardItem(str(par.limits[0]))
            item4 = QtGui.QStandardItem(str(par.limits[1]))
            item5 = QtGui.QStandardItem(par.units)
            model.appendRow([item1, item2, item3, item4, item5])

def calculateChi2(reference_data, current_data):
    """
    Calculate Chi2 value between two sets of data
    """

    # WEIGHING INPUT
    #from sas.sasgui.perspectives.fitting.utils import get_weight
    #flag = self.get_weight_flag()
    #weight = get_weight(data=self.data, is2d=self._is_2D(), flag=flag)

    if reference_data == None:
       return chisqr

    # temporary default values for index and weight
    index = None
    weight = None

    # Get data: data I, theory I, and data dI in order
    if isinstance(reference_data, Data2D):
        if index == None:
            index = numpy.ones(len(current_data.data), dtype=bool)
        if weight != None:
            current_data.err_data = weight
        # get rid of zero error points
        index = index & (current_data.err_data != 0)
        index = index & (numpy.isfinite(current_data.data))
        fn = current_data.data[index]
        gn = reference_data.data[index]
        en = current_data.err_data[index]
    else:
        # 1 d theory from model_thread is only in the range of index
        if index == None:
            index = numpy.ones(len(current_data.y), dtype=bool)
        if weight != None:
            current_data.dy = weight
        if current_data.dy == None or current_data.dy == []:
            dy = numpy.ones(len(current_data.y))
        else:
            ## Set consistently w/AbstractFitengine:
            # But this should be corrected later.
            dy = deepcopy(current_data.dy)
            dy[dy == 0] = 1
        fn = current_data.y[index]
        gn = reference_data.y
        en = dy[index]
    # Calculate the residual
    try:
        res = (fn - gn) / en
    except ValueError:
        print "Chi2 calculations: Unmatched lengths %s, %s, %s" % (len(fn), len(gn), len(en))
        return

    residuals = res[numpy.isfinite(res)]
    chisqr = numpy.average(residuals * residuals)

    return chisqr

def binary_encode(i, digits):
    return [i >> d & 1 for d in xrange(digits)]


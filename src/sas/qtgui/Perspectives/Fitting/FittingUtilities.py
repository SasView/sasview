import copy

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import numpy

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

model_header_captions = ['Parameter', 'Value', 'Min', 'Max', 'Units']

model_header_tooltips = ['Select parameter for fitting',
                         'Enter parameter value',
                         'Enter minimum value for parameter',
                         'Enter maximum value for parameter',
                         'Unit of the parameter']

poly_header_captions = ['Parameter', 'PD[ratio]', 'Min', 'Max', 'Npts', 'Nsigs',
                        'Function', 'Filename']

poly_header_tooltips = ['Select parameter for fitting',
                        'Enter polydispersity ratio (STD/mean). '
                        'STD: standard deviation from the mean value',
                        'Enter minimum value for parameter',
                        'Enter maximum value for parameter',
                        'Enter number of points for parameter',
                        'Enter number of sigmas parameter',
                        'Select distribution function',
                        'Select filename with user-definable distribution']

error_tooltip = 'Error value for fitted parameter'
header_error_caption = 'Error'

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
    return list([par for par in model.iq_parameters if "[" in par.name])

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

def addParametersToModel(parameters, kernel_module, is2D):
    """
    Update local ModelModel with sasmodel parameters
    """
    multishell_parameters = getIterParams(parameters)
    multishell_param_name, _ = getMultiplicity(parameters)
    params = parameters.iqxy_parameters if is2D else parameters.iq_parameters
    item = []
    for param in params:
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
        item1.setEditable(False)
        # item_err = QtGui.QStandardItem()
        # check for polydisp params
        if param.polydisperse:
            poly_item = QtGui.QStandardItem("Polydispersity")
            poly_item.setEditable(False)
            item1_1 = QtGui.QStandardItem("Distribution")
            item1_1.setEditable(False)
            # Find param in volume_params
            for p in parameters.form_volume_parameters:
                if p.name != param.name:
                    continue
                width = kernel_module.getParam(p.name+'.width')
                type = kernel_module.getParam(p.name+'.type')

                item1_2 = QtGui.QStandardItem(str(width))
                item1_2.setEditable(False)
                item1_3 = QtGui.QStandardItem()
                item1_3.setEditable(False)
                item1_4 = QtGui.QStandardItem()
                item1_4.setEditable(False)
                item1_5 = QtGui.QStandardItem(type)
                item1_5.setEditable(False)
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
        item5.setEditable(False)
        item.append([item1, item2, item3, item4, item5])
    return item

def addSimpleParametersToModel(parameters, is2D):
    """
    Update local ModelModel with sasmodel parameters
    """
    params = parameters.iqxy_parameters if is2D else parameters.iq_parameters
    item = []
    for param in params:
        # Create the top level, checkable item
        item_name = param.name
        item1 = QtGui.QStandardItem(item_name)
        item1.setCheckable(True)
        item1.setEditable(False)
        # Param values
        # TODO: add delegate for validation of cells
        item2 = QtGui.QStandardItem(str(param.default))
        item4 = QtGui.QStandardItem(str(param.limits[0]))
        item5 = QtGui.QStandardItem(str(param.limits[1]))
        item6 = QtGui.QStandardItem(param.units)
        item6.setEditable(False)
        item.append([item1, item2, item4, item5, item6])
    return item

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
    for i, item in enumerate(model_header_captions):
        model.setHeaderData(i, QtCore.Qt.Horizontal, item)

    model.header_tooltips = copy.copy(model_header_tooltips)

def addErrorHeadersToModel(model):
    """
    Adds predefined headers to the model
    """
    model_header_error_captions = copy.copy(model_header_captions)
    model_header_error_captions.insert(2, header_error_caption)
    for i, item in enumerate(model_header_error_captions):
        model.setHeaderData(i, QtCore.Qt.Horizontal, item)

    model_header_error_tooltips = copy.copy(model_header_tooltips)
    model_header_error_tooltips.insert(2, error_tooltip)
    model.header_tooltips = copy.copy(model_header_error_tooltips)

def addPolyHeadersToModel(model):
    """
    Adds predefined headers to the model
    """
    for i, item in enumerate(poly_header_captions):
        model.setHeaderData(i, QtCore.Qt.Horizontal, item)

    model.header_tooltips = copy.copy(poly_header_tooltips)


def addErrorPolyHeadersToModel(model):
    """
    Adds predefined headers to the model
    """
    poly_header_error_captions = copy.copy(poly_header_captions)
    poly_header_error_captions.insert(2, header_error_caption)
    for i, item in enumerate(poly_header_error_captions):
        model.setHeaderData(i, QtCore.Qt.Horizontal, item)

    poly_header_error_tooltips = copy.copy(poly_header_tooltips)
    poly_header_error_tooltips.insert(2, error_tooltip)
    model.header_tooltips = copy.copy(poly_header_error_tooltips)

def addShellsToModel(parameters, model, index):
    """
    Find out multishell parameters and update the model with the requested number of them
    """
    multishell_parameters = getIterParams(parameters)

    for i in range(index):
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
    chisqr = None
    if reference_data is None:
        return chisqr

    # temporary default values for index and weight
    index = None
    weight = None

    # Get data: data I, theory I, and data dI in order
    if isinstance(reference_data, Data2D):
        if index is None:
            index = numpy.ones(len(current_data.data), dtype=bool)
        if weight is not None:
            current_data.err_data = weight
        # get rid of zero error points
        index = index & (current_data.err_data != 0)
        index = index & (numpy.isfinite(current_data.data))
        fn = current_data.data[index]
        gn = reference_data.data[index]
        en = current_data.err_data[index]
    else:
        # 1 d theory from model_thread is only in the range of index
        if index is None:
            index = numpy.ones(len(current_data.y), dtype=bool)
        if weight is not None:
            current_data.dy = weight
        if current_data.dy is None or current_data.dy == []:
            dy = numpy.ones(len(current_data.y))
        else:
            ## Set consistently w/AbstractFitengine:
            # But this should be corrected later.
            dy = copy.deepcopy(current_data.dy)
            dy[dy == 0] = 1
        fn = current_data.y[index]
        gn = reference_data.y
        en = dy[index]
    # Calculate the residual
    try:
        res = (fn - gn) / en
    except ValueError:
        #print "Chi2 calculations: Unmatched lengths %s, %s, %s" % (len(fn), len(gn), len(en))
        return None

    residuals = res[numpy.isfinite(res)]
    chisqr = numpy.average(residuals * residuals)

    return chisqr

def residualsData1D(reference_data, current_data):
    """
    Calculate the residuals for difference of two Data1D sets
    """
    # temporary default values for index and weight
    index = None
    weight = None

    # 1d theory from model_thread is only in the range of index
    if current_data.dy is None or current_data.dy == []:
        dy = numpy.ones(len(current_data.y))
    else:
        dy = weight if weight is not None else numpy.ones(len(current_data.y))
        dy[dy == 0] = 1
    fn = current_data.y[index][0]
    gn = reference_data.y
    en = dy[index][0]
    # build residuals
    residuals = Data1D()
    if len(fn) == len(gn):
        y = (fn - gn)/en
        residuals.y = -y
    else:
        # TODO: fix case where applying new data from file on top of existing model data
        try:
            y = (fn - gn[index][0]) / en
            residuals.y = y
        except ValueError:
            # value errors may show up every once in a while for malformed columns,
            # just reuse what's there already
            pass

    residuals.x = current_data.x[index][0]
    residuals.dy = numpy.ones(len(residuals.y))
    residuals.dx = None
    residuals.dxl = None
    residuals.dxw = None
    residuals.ytransform = 'y'
    # For latter scale changes
    residuals.xaxis('\\rm{Q} ', 'A^{-1}')
    residuals.yaxis('\\rm{Residuals} ', 'normalized')

    return residuals

def residualsData2D(reference_data, current_data):
    """
    Calculate the residuals for difference of two Data2D sets
    """
    # temporary default values for index and weight
    # index = None
    weight = None

    # build residuals
    residuals = Data2D()
    # Not for trunk the line below, instead use the line above
    current_data.clone_without_data(len(current_data.data), residuals)
    residuals.data = None
    fn = current_data.data
    gn = reference_data.data
    en = current_data.err_data if weight is None else weight
    residuals.data = (fn - gn) / en
    residuals.qx_data = current_data.qx_data
    residuals.qy_data = current_data.qy_data
    residuals.q_data = current_data.q_data
    residuals.err_data = numpy.ones(len(residuals.data))
    residuals.xmin = min(residuals.qx_data)
    residuals.xmax = max(residuals.qx_data)
    residuals.ymin = min(residuals.qy_data)
    residuals.ymax = max(residuals.qy_data)
    residuals.q_data = current_data.q_data
    residuals.mask = current_data.mask
    residuals.scale = 'linear'
    # check the lengths
    if len(residuals.data) != len(residuals.q_data):
        return None
    return residuals

def plotResiduals(reference_data, current_data):
    """
    Create Data1D/Data2D with residuals, ready for plotting
    """
    data_copy = copy.deepcopy(current_data)
    # Get data: data I, theory I, and data dI in order
    method_name = current_data.__class__.__name__
    residuals_dict = {"Data1D": residualsData1D,
                      "Data2D": residualsData2D}

    residuals = residuals_dict[method_name](reference_data, data_copy)

    theory_name = str(current_data.name.split()[0])
    residuals.name = "Residuals for " + str(theory_name) + "[" + \
                    str(reference_data.filename) + "]"
    residuals.title = residuals.name
    residuals.ytransform = 'y'

    # when 2 data have the same id override the 1 st plotted
    # include the last part if keeping charts for separate models is required
    residuals.id = "res" + str(reference_data.id) # + str(theory_name)
    # group_id specify on which panel to plot this data
    group_id = reference_data.group_id
    residuals.group_id = "res" + str(group_id)

    # Symbol
    residuals.symbol = 0
    residuals.hide_error = False

    return residuals

def binary_encode(i, digits):
    return [i >> d & 1 for d in range(digits)]

def getWeight(data, is2d, flag=None):
    """
    Received flag and compute error on data.
    :param flag: flag to transform error of data.
    """
    weight = None
    if is2d:
        dy_data = data.err_data
        data = data.data
    else:
        dy_data = data.dy
        data = data.y

    if flag == 0:
        weight = numpy.ones_like(data)
    elif flag == 1:
        weight = dy_data
    elif flag == 2:
        weight = numpy.sqrt(numpy.abs(data))
    elif flag == 3:
        weight = numpy.abs(data)
    return weight

import copy

import numpy
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting.AssociatedComboBox import AssociatedComboBox
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.sascalc.fit.expression import check_constraints

model_header_captions = ['Parameter', 'Value', 'Min', 'Max', 'Units']

model_header_tooltips = ['Select parameter for fitting',
                         'Enter parameter value',
                         'Enter minimum value for parameter',
                         'Enter maximum value for parameter',
                         'Unit of the parameter']

poly_header_captions = ['Parameter', 'PD[ratio]', 'Min', 'Max', 'Npts', 'Nsigs',
                        'Function', 'Filename']

poly_header_tooltips = ['Select parameter for fitting',
                        'Enter polydispersity ratio (Std deviation/mean).\n'+
                        'For angles this can be either std deviation or half width (for uniform distributions) in degrees',
                        'Enter minimum value for parameter',
                        'Enter maximum value for parameter',
                        'Enter number of points for parameter',
                        'Enter number of sigmas parameter',
                        'Select distribution function',
                        'Select filename with user-definable distribution']

error_tooltip = 'Error value for fitted parameter'
header_error_caption = 'Error'

class ToolTippedItemModel(QtGui.QStandardItemModel):
    """
    Subclass from QStandardItemModel to allow displaying tooltips in
    QTableView model.
    """
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Displays tooltip for each column's header
        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if role == QtCore.Qt.ToolTipRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.header_tooltips[section])

        return QtGui.QStandardItemModel.headerData(self, section, orientation, role)

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

def createFixedChoiceComboBox(param, item_row):
    """
    Determines whether param is a fixed-choice parameter, modifies items in item_row appropriately and returns a combo
    box containing the fixed choices. Returns None if param is not fixed-choice.

    item_row is a list of QStandardItem objects for insertion into the parameter table.
    """

    # Determine whether this is a fixed-choice parameter. There are lots of conditionals, simply because the
    # implementation is not yet concrete; there are several possible indicators that the parameter is fixed-choice.
    # TODO: (when the sasmodels implementation is concrete, clean this up)
    choices = None
    if isinstance(param.choices, (list, tuple)) and len(param.choices) > 0:
        # The choices property is concrete in sasmodels, probably will use this
        choices = param.choices
    elif isinstance(param.units, (list, tuple)):
        choices = [str(x) for x in param.units]

    cbox = None
    if choices is not None:
        # Use combo box for input, if it is fixed-choice
        cbox = AssociatedComboBox(item_row[1], idx_as_value=True)
        cbox.addItems(choices)
        if param.default is not None and param.default <= len(choices):
            # set the param default value in the combobox
            cbox.setCurrentIndex(param.default)
        item_row[2].setEditable(False)
        item_row[3].setEditable(False)

    return cbox

def addParametersToModel(parameters, kernel_module, is2D, model=None, view=None):
    """
    Update local ModelModel with sasmodel parameters.
    Actually appends to model, if model and view params are not None.
    Always returns list of lists of QStandardItems.
    """
    multishell_parameters = getIterParams(parameters)
    multishell_param_name, _ = getMultiplicity(parameters)

    if is2D:
        params = [p for p in parameters.kernel_parameters if p.type != 'magnetic']
    else:
        params = parameters.iq_parameters

    rows = []
    for param in params:
        # don't include shell parameters
        if param.name == multishell_param_name:
            continue

        # Modify parameter name from <param>[n] to <param>1
        item_name = param.name
        if param in multishell_parameters:
            continue

        item1 = QtGui.QStandardItem(item_name)
        item1.setCheckable(True)
        item1.setEditable(False)

        # check for polydisp params
        if param.polydisperse:
            poly_item = QtGui.QStandardItem("Polydispersity")
            poly_item.setEditable(False)
            poly_item.setSelectable(False)
            item1_1 = QtGui.QStandardItem("Distribution")
            item1_1.setEditable(False)
            item1_1.setSelectable(False)

            # Find param in volume_params
            poly_pars = copy.deepcopy(parameters.form_volume_parameters)
            if is2D:
                poly_pars += parameters.orientation_parameters
            for p in poly_pars:
                if p.name != param.name:
                    continue
                width = kernel_module.getParam(p.name+'.width')
                ptype = kernel_module.getParam(p.name+'.type')
                item1_2 = QtGui.QStandardItem(str(width))
                item1_2.setEditable(False)
                item1_2.setSelectable(False)
                item1_3 = QtGui.QStandardItem()
                item1_3.setEditable(False)
                item1_3.setSelectable(False)
                item1_4 = QtGui.QStandardItem()
                item1_4.setEditable(False)
                item1_4.setSelectable(False)
                item1_5 = QtGui.QStandardItem(ptype)
                item1_5.setEditable(False)
                item1_5.setSelectable(False)
                poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                break

            # Add the polydisp item as a child
            item1.appendRow([poly_item])

        # Param values
        item2 = QtGui.QStandardItem(str(param.default))
        item3 = QtGui.QStandardItem(str(param.limits[0]))
        item4 = QtGui.QStandardItem(str(param.limits[1]))
        item5 = QtGui.QStandardItem(str(param.units))
        item5.setEditable(False)

        # Check if fixed-choice (returns combobox, if so, also makes some items uneditable)
        row = [item1, item2, item3, item4, item5]
        cbox = createFixedChoiceComboBox(param, row)

        # Append to the model and use the combobox, if required
        if None not in (model, view):
            model.appendRow(row)
            if cbox:
                view.setIndexWidget(item2.index(), cbox)

        rows.append(row)

    return rows

def addSimpleParametersToModel(parameters, is2D, parameters_original=None, model=None, view=None, row_num=None):
    """
    Update local ModelModel with sasmodel parameters (non-dispersed, non-magnetic)
    Actually appends to model, if model and view params are not None.
    Always returns list of lists of QStandardItems.

    parameters_original: list of parameters before any tagging on their IDs,
    e.g. for product model (so that those are the display names; see below)
    """
    if is2D:
        params = [p for p in parameters.kernel_parameters if p.type != 'magnetic']
    else:
        params = parameters.iq_parameters

    if parameters_original:
        # 'parameters_original' contains the parameters as they are to be DISPLAYED,
        # while 'parameters' contains the parameters as they were renamed;
        # this is for handling name collisions in product model.
        # The 'real name' of the parameter will be stored in the item's user data.
        if is2D:
            params_orig = [p for p in parameters_original.kernel_parameters if p.type != 'magnetic']
        else:
            params_orig = parameters_original.iq_parameters
    else:
        # no difference in names anyway
        params_orig = params

    rows = []
    for param, param_orig in zip(params, params_orig):
        # Create the top level, checkable item
        item_name = param_orig.name
        item1 = QtGui.QStandardItem(item_name)
        item1.setData(param.name, QtCore.Qt.UserRole)
        item1.setCheckable(False)
        item1.setEditable(False)

        # Param values
        # TODO: add delegate for validation of cells
        item2 = QtGui.QStandardItem(str(param.default))
        item3 = QtGui.QStandardItem(str(param.limits[0]))
        item4 = QtGui.QStandardItem(str(param.limits[1]))
        item5 = QtGui.QStandardItem(str(param.units))
        item5.setEditable(False)

        # Check if fixed-choice (returns combobox, if so, also makes some items uneditable)
        row = [item1, item2, item3, item4, item5]
        cbox = createFixedChoiceComboBox(param, row)

        # Append to the model and use the combobox, if required
        if None not in (model, view):

            if row_num is None:
                model.appendRow(row)
            else:
                model.insertRow(row_num, row)
                row_num += 1
            if cbox:
                item1.setCheckable(False)
                item3.setText("")
                item4.setText("")
                item3.setEditable(False)
                item4.setEditable(False)
                view.setIndexWidget(item2.index(), cbox)
            else:
                item1.setCheckable(True)

        rows.append(row)

    return rows

def markParameterDisabled(model, row):
    """Given the QModel row number, format to show it is not available for fitting"""

    # If an error column is present, there are a total of 6 columns.
    items = [model.item(row, c) for c in range(6)]

    model.blockSignals(True)

    for item in items:
        if item is None:
            continue
        item.setEditable(False)
        item.setCheckable(False)

    item = items[0]

    font = QtGui.QFont()
    font.setItalic(True)
    item.setFont(font)
    item.setForeground(QtGui.QBrush(QtGui.QColor(100, 100, 100)))
    item.setToolTip("This parameter cannot be fitted.")

    model.blockSignals(False)

def addCheckedListToModel(model, param_list):
    """
    Add a QItem to model. Makes the QItem checkable
    """
    assert isinstance(model, QtGui.QStandardItemModel)
    item_list = [QtGui.QStandardItem(item) for item in param_list]
    item_list[0].setCheckable(True)
    model.appendRow(item_list)

def addHeadingRowToModel(model, name):
    """adds a non-interactive top-level row to the model"""
    header_row = [QtGui.QStandardItem() for i in range(5)]
    header_row[0].setText(name)

    font = header_row[0].font()
    font.setBold(True)
    header_row[0].setFont(font)

    for item in header_row:
        item.setEditable(False)
        item.setCheckable(False)
        item.setSelectable(False)

    model.appendRow(header_row)

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

def addShellsToModel(parameters, model, index, row_num=None, view=None):
    """
    Find out multishell parameters and update the model with the requested number of them.
    Inserts them after the row at row_num, if not None; otherwise, appends to end.
    If view param is not None, supports fixed-choice params.
    Returns a list of lists of QStandardItem objects.
    """
    multishell_parameters = getIterParams(parameters)

    rows = []
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
                    item1_5 = QtGui.QStandardItem(str(p.units))
                    poly_item.appendRow([item1_1, item1_2, item1_3, item1_4, item1_5])
                    break
                item1.appendRow([poly_item])

            item2 = QtGui.QStandardItem(str(par.default))
            item3 = QtGui.QStandardItem(str(par.limits[0]))
            item4 = QtGui.QStandardItem(str(par.limits[1]))
            item5 = QtGui.QStandardItem(str(par.units))
            item5.setEditable(False)

            # Check if fixed-choice (returns combobox, if so, also makes some items uneditable)
            row = [item1, item2, item3, item4, item5]
            cbox = createFixedChoiceComboBox(par, row)

            # Apply combobox if required
            if None not in (view, cbox):
                # set the min/max cell to be empty
                item3.setText("")
                item4.setText("")

            # Always add to the model
            if row_num is None:
                model.appendRow(row)
            else:
                model.insertRow(row_num, row)
                row_num += 1

            if cbox is not None:
                view.setIndexWidget(item2.index(), cbox)

            rows.append(row)

    return rows

def calculateChi2(reference_data, current_data, weight):
    """
    Calculate Chi2 value between two sets of data
    """
    if reference_data is None or current_data is None:
        return None
    chisqr = None
    if reference_data is None:
        return chisqr

    # temporary default values for index and weight
    index = None

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

        if index is None:
            index = numpy.ones(len(current_data.y), dtype=bool)
        # if current_data.dy is None or not len(current_data.dy):
        if current_data.dy is None or current_data.dy.size == 0:
            dy = numpy.ones(len(current_data.y))
        else:
            dy = weight
            dy[dy == 0] = 1

        fn = current_data.y[index]
        gn = reference_data.y
        en = dy[index]

        x_current = current_data.x
        x_reference = reference_data.x

        if len(fn) > len(gn):
            fn = fn[0:len(gn)]
            en = en[0:len(gn)]
        else:
            try:
                y = numpy.zeros(len(current_data.y))
                begin = 0
                for i, x_value in enumerate(x_reference):
                    if x_value in x_current:
                        begin = i
                        break
                end = len(x_reference)
                endl = 0
                for i, x_value in enumerate(list(x_reference)[::-1]):
                    if x_value in x_current:
                        endl = i
                        break
                en = en[begin:end-endl]
                y = (fn - gn[begin:end-endl])/en
            except ValueError:
                # value errors may show up every once in a while for malformed columns,
                # just reuse what's there already
                pass

    # Calculate the residual
    try:
        res = (fn - gn) / en
    except ValueError:
        #print "Chi2 calculations: Unmatched lengths %s, %s, %s" % (len(fn), len(gn), len(en))
        return None

    residuals = res[numpy.isfinite(res)]
    chisqr = numpy.average(residuals * residuals)

    return chisqr

def residualsData1D(reference_data, current_data, weights):
    """
    Calculate the residuals for difference of two Data1D sets
    """
    # temporary default values for index and weight
    index = None

    # 1d theory from model_thread is only in the range of index
    if current_data.dy is None or not len(current_data.dy):
        dy = numpy.ones(len(current_data.y))
    else:
        #dy = weight if weight is not None else numpy.ones(len(current_data.y))
        if numpy.all(current_data.dy):
            dy = current_data.dy
        else:
            dy = weights
        dy[dy == 0] = 1

    fn = current_data.y[index][0]

    gn = reference_data.y
    en = dy[index][0]

    # x values
    x_current = current_data.x
    x_reference = reference_data.x

    # build residuals
    residuals = Data1D()
    if len(fn) == len(gn):
        y = (fn - gn)/en
        residuals.y = -y
    elif len(fn) > len(gn):
        residuals.y = -(fn - gn[1:len(fn)])/en
    else:
        try:
            y = numpy.zeros(len(current_data.y))
            begin = 0
            for i, x_value in enumerate(x_reference):
                if x_value in x_current:
                    begin = i
                    break
            end = len(x_reference)
            endl = 0
            for i, x_value in enumerate(list(x_reference)[::-1]):
                if x_value in x_current:
                    endl = i
                    break
            en = en[begin:end-endl]
            y = (fn - gn[begin:end-endl])/en
            residuals.y = -y
        except ValueError:
            # value errors may show up every once in a while for malformed columns,
            # just reuse what's there already
            pass

    residuals.x = current_data.x[index][0]
    residuals.dy = None
    residuals.dx = None
    residuals.dxl = None
    residuals.dxw = None
    residuals.ytransform = 'y'
    if reference_data.isSesans:
        residuals.xtransform = 'x'
        residuals.xaxis('\\delta ', 'A')
    # For latter scale changes
    else:
        residuals.xaxis('\\rm{Q} ', 'A^{-1}')
    residuals.yaxis('\\rm{Residuals} ', 'normalized')

    return residuals

def residualsData2D(reference_data, current_data, weight):
    """
    Calculate the residuals for difference of two Data2D sets
    """
    # build residuals
    residuals = Data2D()
    # Not for trunk the line below, instead use the line above
    current_data.clone_without_data(len(current_data.data), residuals)
    residuals.data = None
    fn = current_data.data
    gn = reference_data.data
    if weight is None:
        en = current_data.err_data
    else:
        en = weight
    residuals.data = (fn - gn) / en
    residuals.qx_data = current_data.qx_data
    residuals.qy_data = current_data.qy_data
    residuals.q_data = current_data.q_data
    residuals.err_data = None
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

def plotResiduals(reference_data, current_data, weights):
    """
    Create Data1D/Data2D with residuals, ready for plotting
    """
    data_copy = copy.deepcopy(current_data)
    # Get data: data I, theory I, and data dI in order
    method_name = current_data.__class__.__name__
    residuals_dict = {"Data1D": residualsData1D,
                      "Data2D": residualsData2D}

    try:
        residuals = residuals_dict[method_name](reference_data, data_copy, weights)
    except ValueError:
        return None

    theory_name = str(current_data.name.split()[0])
    res_name = reference_data.name if reference_data.name else reference_data.filename
    residuals.name = "Residuals for " + str(theory_name) + "[" + res_name + "]"
    residuals.title = residuals.name

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

def plotPolydispersities(model):
    plots = []
    if model is None:
        return plots
    # test for model being a sasmodels.sasview_model.SasviewModel?
    for name in model.dispersion.keys():
        xarr, yarr = model.get_weights(name)
        if len(xarr) <= 1: # param name not found or no polydisp.
            continue
        # create Data1D as in residualsData1D() and fill x/y members
        # similar to FittingLogic._create1DPlot() but different data/axes
        data1d = Data1D(x=xarr, y=yarr)
        xunit = model.details[name][0]
        data1d.xtransform = 'x'
        data1d.ytransform = 'y'
        data1d.xaxis(r'\rm{{{}}}'.format(name.replace('_', r'\_')), xunit)
        data1d.yaxis(r'\rm{probability}', 'normalized')
        data1d.scale = 'linear'
        data1d.symbol = 'Line'
        data1d.name = f"{name} polydispersity"
        data1d.id = data1d.name # placeholder, has to be completed later
        data1d.plot_role = DataRole.ROLE_POLYDISPERSITY
        plots.append(data1d)
    return plots

def binary_encode(i, digits):
    return [i >> d & 1 for d in range(digits)]


def getWeight(data, is2d, flag=None):
    """
    Received flag and compute error on data.
    :param flag: flag to transform error of data.
    """
    weight = None
    if data is None:
        return []
    if is2d:
        if not hasattr(data, 'err_data'):
            return []
        dy_data = data.err_data
        data = data.data
    else:
        if not hasattr(data, 'dy'):
            return []
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


def getRelativeError(data, is2d, flag=None):
    """
    Return dy/y.
    """
    weight = None
    if data is None:
        return []
    if is2d:
        if not hasattr(data, 'err_data'):
            return numpy.ones_like(data.y)
        dy_data = data.err_data
        data = data.data
    else:
        if not hasattr(data, 'dy'):
            return numpy.ones_like(data.y)
        dy_data = data.dy
        data = data.y

    if flag == 0:
        weight = numpy.ones_like(data)
    elif flag == 1:
        weight = dy_data / data
    elif flag == 2:
        weight = 1.0 / numpy.sqrt(numpy.abs(data))
    elif flag == 3:
        weight = 1.0 / numpy.abs(data)

    return weight

def calcWeightIncrease(weights, ratios, flag=False):
    """ Calculate the weights to be passed to bumps in order to ensure
        that each data set contributes to the total residual with a
        relative weight roughly proportional to the ratios defined by
        the user when the "Modify weighting" option is employed.

        The influence of each data set in the global fit is approximately
        proportional to the number of points and to (1/sigma^2), or
        probably better to (1/relative_error^2) = (intensity/sigma)^2.

        Therefore in order to try to give equal weights to each data set
        in the global fitting, we can compute the total relative weight
        of each data set as the sum (y_i/dy_i**2) over all the points in
        the data set and then renormalize them using:

        user_weight[dataset] * sqrt(min(relative_weights) /  relative_weights[dataset])

        If all user weights are one (the default), this will decrease the weight
        of the data sets initially contributing more to the global fit, while
        keeping the weight of the initially smaller contributor equal to one.

        These weights are stored for each data set (FitPage) in a dictionary that
        will be then used by bumps to modify the weights of each set.

        Warning: As bumps uses the data set weights to multiply the residuals
        calculated as (y-f(x))/sigma, it would probably make sense to include
        the value of user_weight[dataset] in the square root, but as in any
        case this is just a qualitative way of increasing/decreasing the weight
        of some datasets and there is not a real mathematical justification
        behind, this provides a more intuitive behaviour for the user, who will
        see that the final weights of the data sets vary proportionally to changes
        in the input user weights.

    :param weights: Dictionary of data for the statistical weight, typical the y axis error
    :type weights: dict of numpy.ndarray
    :param ratios: Desired relative statistical weight ratio between the different datasets.
    :type ratios: dict
    :param flag: Boolean indicating if the weight of the datasets should be modified or not,
                 which depends on the "Modify weighting" box in the Simultaneous Fit tab
                 being checked or not
    :type flag: bool
    :return: Weight multiplier for each dataset
    :rtype: dict
    """

    # If "Modify weighting" option not checked
    if not flag:
        return {k: 1.0 for k in weights}

    # Calc statistical weight for each dataset and maximum
    stat_weights = {k: numpy.sum(v**-2) for k, v in weights.items()}
    min_weight = min(stat_weights.values())
    weight_increase = {k: float(ratios[k]) * numpy.sqrt(min_weight / v) for k, v in stat_weights.items()}

    return weight_increase

def updateKernelWithResults(kernel, results):
    """
    Takes model kernel and applies results dict to its parameters,
    returning the modified (deep) copy of the kernel.
    """
    assert isinstance(results, dict)
    local_kernel = copy.deepcopy(kernel)

    for parameter in results.keys():
        # Update the parameter value - note: this supports +/-inf as well
        local_kernel.setParam(parameter, results[parameter][0])

    return local_kernel

def getStandardParam(model=None):
    """
    Returns a list with standard parameters for the current model
    """
    param = []
    num_rows = model.rowCount()
    if num_rows < 1:
        return param

    for row in range(num_rows):
        param_name = model.item(row, 0).text()
        checkbox_state = model.item(row, 0).checkState() == QtCore.Qt.Checked
        value = model.item(row, 1).text()
        column_shift = 0
        if model.columnCount() == 5: # no error column
            error_state = False
            error_value = 0.0
        else:
            error_state = True
            error_value = model.item(row, 2).text()
            column_shift = 1
        min_state = True
        max_state = True
        min_value = model.item(row, 2+column_shift).text()
        max_value = model.item(row, 3+column_shift).text()
        unit = ""
        if model.item(row, 4+column_shift) is not None:
            u = model.item(row, 4+column_shift).text()
            # This isn't a unit if it is a number (polyd./magn.)
            unit = "" if isNumber(u) else u
        param.append([checkbox_state, param_name, value, "",
                     [error_state, error_value],
                     [min_state, min_value],
                     [max_state, max_value], unit])

    return param

def isNumber(s):
    """
    Checks if string 's' is an int/float
    """
    if s.isdigit():
        # check int
        return True
    else:
        try:
            # check float
            _ = float(s)
        except ValueError:
            return False
    return True

def getOrientationParam(kernel_module=None):
    """
    Get the dictionary with orientation parameters
    """
    param = []
    if kernel_module is None:
        return None
    for param_name in list(kernel_module.params.keys()):
        name = param_name
        value = kernel_module.params[param_name]
        min_state = True
        max_state = True
        error_state = False
        error_value = 0.0
        checkbox_state = True #??
        details = kernel_module.details[param_name] #[unit, mix, max]
        param.append([checkbox_state, name, value, "",
                     [error_state, error_value],
                     [min_state, details[1]],
                     [max_state, details[2]], details[0]])

    return param

def formatParameters(parameters: list, entry_sep=',', line_sep=':'):
    """
    Prepare the parameter string in the standard SasView layout
    """

    parameter_strings = ["sasview_parameter_values"]
    for parameter in parameters:
        parameter_strings.append(entry_sep.join([str(component) for component in parameter]))

    return line_sep.join(parameter_strings)

def formatParametersExcel(parameters: list):
    """
    Prepare the parameter string in the Excel format (tab delimited)
    """
    crlf = chr(13) + chr(10)
    tab = chr(9)

    output_string = ""
    # names
    names = ""
    values = ""
    check = ""
    for parameter in parameters:
        names += parameter[0]+tab
        if len(parameter) > 3:
            # Add the error column if fitted
            if parameter[1] == "True" and parameter[3] is not None:
                names += parameter[0]+"_err"+tab

            values += parameter[2]+tab
            check += str(parameter[1])+tab
            if parameter[1] == "True" and parameter[3] is not None:
                values += parameter[3]+tab
            # add .npts and .nsigmas when necessary
            if parameter[0][-6:] == ".width":
                names += parameter[0].replace('.width', '.nsigmas') + tab
                names += parameter[0].replace('.width', '.npts') + tab
                values += parameter[5] + tab + parameter[4] + tab
        else:
            # Empty statement for debugging purposes
            pass

    output_string = names + crlf + values + crlf + check
    return output_string

def formatParametersLatex(parameters: list):
    """
    Prepare the parameter string in latex
    """

    output_string = r'\begin{table}'
    output_string += r'\begin{tabular}[h]'

    crlf = chr(13) + chr(10)
    output_string += '{|'
    output_string += 'l|l|'*len(parameters)
    output_string += r'}\hline'
    output_string += crlf

    names = ""
    values = ""

    for index, parameter in enumerate(parameters):
        name = parameter[0] # Parameter name
        names += name.replace('_', r'\_')  # Escape underscores
        if len(parameter) > 3:
            values += f" {parameter[2]}"
            # Add the error column if fitted
            if parameter[1] == "True" and parameter[3] is not None:
                names += f" & {parameter[0]} " + r'\_err'
                values += f' & {parameter[3]}'

            if index < len(parameters) - 1:
                names += ' & '
                values += ' & '

            # add .npts and .nsigmas when necessary
            if parameter[0][-6:] == ".width":
                names += parameter[0].replace('.width', '.nsigmas') + ' & '
                names += parameter[0].replace('.width', '.npts')
                values += parameter[5] + ' & '
                values += parameter[4]

                if index < len(parameters) - 1:
                    names += ' & '
                    values += ' & '
        elif len(parameter) > 2:
            values += f' & {parameter[2]} &'
        else:
            values += f' & {parameter[1]} &'

    output_string += names
    output_string += r'\\ \hline'
    output_string += crlf

    output_string += values
    output_string += r'\\ \hline'
    output_string += crlf
    output_string += r'\end{tabular}'
    output_string += r'\end{table}'

    return output_string

def isParamPolydisperse(param_name, kernel_params, is2D=False):
    """
    Simple lookup for polydispersity for the given param name
    """
    # First, check if this is a polydisperse parameter directly
    if '.width' in param_name:
        return True

    parameters = kernel_params.form_volume_parameters
    if is2D:
        parameters += kernel_params.orientation_parameters

    # Next, check if the parameter is included in para.polydisperse
    has_poly = False
    for param in parameters:
        if param.name==param_name and param.polydisperse:
            has_poly = True
            break
    return has_poly

def checkConstraints(symtab, constraints):
    # type: (Dict[str, float], Sequence[Tuple[str, str]]) -> str
    """
    Compile and evaluate the constraints in the context of the initial values
    and return the list of errors.

    Errors are returned as an html string where errors are tagged with <b>
    markups:
    Unknown symbol: tags unknown symbols in *constraints*
    Syntax error: tags the beginning of a syntax error in *constraints*
    Cyclic dependency: tags comma separated parameters that have
    cyclic dependency

    The errors are wrapped in a <div class = "error"> and a style header is
    added
    """
    # Note: dict(constraints) will choose the latest definition if
    # there are duplicates.
    errors = "<br>".join(check_constraints(symtab, dict(constraints),
                                           html=True))
    # wrap everything in <div class = "error">
    if errors:
        errors = "<div class = \"error\">" + errors + "</div>"
        header = "<style type=\"text/css\"> div.error b { "\
                 "font-weight: normal; color:red;}</style>"
        return header + errors
    else:
        return []

def setTableProperties(table):
    """
    Setting table properties
    """
    # Table properties
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    table.resizeColumnsToContents()

    # Header
    header = table.horizontalHeader()
    header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
    header.ResizeMode(QtWidgets.QHeaderView.Interactive)

    # Qt5: the following 2 lines crash - figure out why!
    # Resize column 0 and 7 to content
    # header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    # header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)


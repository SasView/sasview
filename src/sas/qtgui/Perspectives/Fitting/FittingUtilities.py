import copy

from PyQt5 import QtCore
from PyQt5 import QtGui

import numpy

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

from sas.qtgui.Perspectives.Fitting.AssociatedComboBox import AssociatedComboBox

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
            item1_1 = QtGui.QStandardItem("Distribution")
            item1_1.setEditable(False)

            # Find param in volume_params
            poly_pars = parameters.form_volume_parameters
            if is2D:
                poly_pars += parameters.orientation_parameters
            for p in poly_pars:
                if p.name != param.name:
                    continue
                width = kernel_module.getParam(p.name+'.width')
                ptype = kernel_module.getParam(p.name+'.type')
                item1_2 = QtGui.QStandardItem(str(width))
                item1_2.setEditable(False)
                item1_3 = QtGui.QStandardItem()
                item1_3.setEditable(False)
                item1_4 = QtGui.QStandardItem()
                item1_4.setEditable(False)
                item1_5 = QtGui.QStandardItem(ptype)
                item1_5.setEditable(False)
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

    parameters_original: list of parameters before any tagging on their IDs, e.g. for product model (so that those are
    the display names; see below)
    """
    if is2D:
        params = [p for p in parameters.kernel_parameters if p.type != 'magnetic']
    else:
        params = parameters.iq_parameters

    if parameters_original:
        # 'parameters_original' contains the parameters as they are to be DISPLAYED, while 'parameters'
        # contains the parameters as they were renamed; this is for handling name collisions in product model.
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
        item1.setCheckable(True)
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
                view.setIndexWidget(item2.index(), cbox)

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

            # Always add to the model
            if row_num is None:
                model.appendRow(row)
            else:
                model.insertRow(row_num, row)
                row_num += 1

            # Apply combobox if required
            if None not in (view, cbox):
                view.setIndexWidget(item2.index(), cbox)

            rows.append(row)

    return rows

def calculateChi2(reference_data, current_data):
    """
    Calculate Chi2 value between two sets of data
    """
    if reference_data is None or current_data is None:
        return None
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

    # x values
    x_current = current_data.x
    x_reference = reference_data.x

    # build residuals
    residuals = Data1D()
    if len(fn) == len(gn):
        y = (fn - gn)/en
        residuals.y = -y
    elif len(fn) > len(gn):
        residuals.y = (fn - gn[1:len(fn)])/en
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
            # make sure we have correct lengths
            assert len(x_current) == len(x_reference[begin:end-endl])

            y = (fn - gn[begin:end-endl])/en
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
    res_name = reference_data.filename if reference_data.filename else reference_data.name
    residuals.name = "Residuals for " + str(theory_name) + "[" + res_name + "]"
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
        return None

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
            unit = model.item(row, 4+column_shift).text()

        param.append([checkbox_state, param_name, value, "",
                        [error_state, error_value],
                        [min_state, min_value],
                        [max_state, max_value], unit])

    return param

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

def formatParameters(parameters):
    """
    Prepare the parameter string in the standard SasView layout
    """
    assert parameters is not None
    assert isinstance(parameters, list)
    output_string = "sasview_parameter_values:"
    for parameter in parameters:
        output_string += ",".join([p for p in parameter if p is not None])
        output_string += ":"
    return output_string

def formatParametersExcel(parameters):
    """
    Prepare the parameter string in the Excel format (tab delimited)
    """
    assert parameters is not None
    assert isinstance(parameters, list)
    crlf = chr(13) + chr(10)
    tab = chr(9)

    output_string = ""
    # names
    names = ""
    values = ""
    for parameter in parameters:
        names += parameter[0]+tab
        # Add the error column if fitted
        if parameter[1] == "True" and parameter[3] is not None:
            names += parameter[0]+"_err"+tab

        values += parameter[2]+tab
        if parameter[1] == "True" and parameter[3] is not None:
            values += parameter[3]+tab
        # add .npts and .nsigmas when necessary
        if parameter[0][-6:] == ".width":
            names += parameter[0].replace('.width', '.nsigmas') + tab
            names += parameter[0].replace('.width', '.npts') + tab
            values += parameter[5] + tab + parameter[4] + tab

    output_string = names + crlf + values
    return output_string

def formatParametersLatex(parameters):
    """
    Prepare the parameter string in latex
    """
    assert parameters is not None
    assert isinstance(parameters, list)
    output_string = r'\begin{table}'
    output_string += r'\begin{tabular}[h]'

    crlf = chr(13) + chr(10)
    output_string += '{|'
    output_string += 'l|l|'*len(parameters)
    output_string += r'}\hline'
    output_string += crlf

    for index, parameter in enumerate(parameters):
        name = parameter[0] # Parameter name
        output_string += name.replace('_', r'\_')  # Escape underscores
        # Add the error column if fitted
        if parameter[1] == "True" and parameter[3] is not None:
            output_string += ' & '
            output_string += parameter[0]+r'\_err'

        if index < len(parameters) - 1:
            output_string += ' & '

        # add .npts and .nsigmas when necessary
        if parameter[0][-6:] == ".width":
            output_string += parameter[0].replace('.width', '.nsigmas') + ' & '
            output_string += parameter[0].replace('.width', '.npts')

            if index < len(parameters) - 1:
                output_string += ' & '

    output_string += r'\\ \hline'
    output_string += crlf

    # Construct row of values and errors
    for index, parameter in enumerate(parameters):
        output_string += parameter[2]
        if parameter[1] == "True" and parameter[3] is not None:
            output_string += ' & '
            output_string += parameter[3]

        if index < len(parameters) - 1:
            output_string += ' & '

        # add .npts and .nsigmas when necessary
        if parameter[0][-6:] == ".width":
            output_string += parameter[5] + ' & '
            output_string += parameter[4]

            if index < len(parameters) - 1:
                output_string += ' & '

    output_string += r'\\ \hline'
    output_string += crlf
    output_string += r'\end{tabular}'
    output_string += r'\end{table}'

    return output_string

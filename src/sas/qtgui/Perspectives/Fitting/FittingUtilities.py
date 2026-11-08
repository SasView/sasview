import copy

import numpy
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting.model.kernel import (  # noqa: F401 (re-exported)
    fixed_choices,
    getIterParams,
    getMultiplicity,
    replaceShellName,
)
from sas.qtgui.Perspectives.Fitting.model.serializer import (  # noqa: F401 (re-exported)
    formatParameters,
    formatParametersExcel,
    formatParametersLatex,
)
from sas.qtgui.Perspectives.Fitting.services.constraints import (
    validate as checkConstraints,  # noqa: F401 (re-exported; the tests patch it)
)
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Utilities import GuiUtils

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

def parse_number(text) -> float | None:
    """A typed number in double precision (register R-12), the locale's spelling as a fallback;
    None if the text is not a number."""
    try:
        return float(text)
    except (TypeError, ValueError):
        pass
    try:
        return float(GuiUtils.toDouble(text))
    except TypeError:
        return None


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
    # Slicers expect residuals to have err_data, so add dummy error data of ones
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
        data1d.name = f"{name}"
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
    if kernel is None:
        return None
    assert isinstance(results, dict)
    local_kernel = copy.deepcopy(kernel)

    for parameter in results.keys():
        # Update the parameter value - note: this supports +/-inf as well
        local_kernel.setParam(parameter, results[parameter][0])

    return local_kernel

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


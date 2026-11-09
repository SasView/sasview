"""
Plot and dataset factories of the fit page (FW-MVC-DESIGN.md §3.4, Phase 7): they were
``FittingLogic``'s. Pure functions of their inputs: no page, no widgets, no Data Explorer
(``view/PlotPublisher.py`` does that).

- theory plots from a calculation's return data (1D, 2D, the P(Q)/S(Q) components);
- the scalar intermediate results (e.g. the computed effective radius);
- the theory-only grids of a page without data;
- the Q range of a dataset, and whether it carries intensity errors.
"""
from __future__ import annotations

import numpy as np

from sasdata.dataloader.data_info import Detector, Source

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole


def _plot_1d(tab_id, x, y, model, data, component: str | None = None) -> Data1D:
    """A theory curve; *component* names a part of the model, e.g. "P(Q)"."""
    plot = Data1D(x=x, y=y)
    plot.is_data = False
    plot.dy = np.zeros(len(y))
    yaxis, yunit = data.get_yaxis()
    xaxis, xunit = data.get_xaxis()
    plot.group_id = data.group_id
    plot.id = str(tab_id) + " " + ("[" + component + "] " if component else "") + model.id
    # use data.filename for data, use model.id for theory
    id_str = data.name if data.name else model.id
    plot.name = model.name + ((" " + component) if component else "") + " [" + id_str + "]"
    plot.title = plot.name
    plot.xaxis(xaxis, xunit)
    plot.yaxis(yaxis, yunit)
    if component is not None:
        plot.plot_role = DataRole.ROLE_DELETABLE
    return plot


def theory_1d(return_data: dict, tab_id) -> Data1D:
    plot = _plot_1d(tab_id, return_data['x'], return_data['y'], return_data['model'], return_data['data'])
    if return_data['data'].isSesans:
        # Fits of SESANS data are in real space
        plot.isSesans = True
        plot.xtransform = "x"
        plot.ytransform = "y"
    return plot


def theory_2d(return_data: dict) -> Data2D:
    image, data, model = return_data['image'], return_data['data'], return_data['model']
    plot = Data2D(image=image, err_image=data.err_data)
    plot.name = model.name + '2d'
    plot.title = "Analytical model 2D "
    plot.id = str(return_data['page_id']) + " " + data.name
    plot.group_id = str(return_data['page_id']) + " Model2D"
    plot.detector = data.detector
    plot.source = data.source
    plot.is_data = False
    plot.qx_data = data.qx_data
    plot.qy_data = data.qy_data
    plot.q_data = data.q_data
    plot.mask = data.mask
    plot.ymin, plot.ymax, plot.xmin, plot.xmax = data.ymin, data.ymax, data.xmin, data.xmax
    data_name = str(data.name) if data.is_data else str(model.__class__.__name__) + '2d'
    if len(data.title) > 1:
        plot.title = "Model2D for %s " % model.name + data_name
    plot.name = model.name + " [" + data_name + "]"
    return plot


def product_plots(return_data: dict, tab_id) -> list[Data1D]:
    """The curves of the intermediate results that are arrays (P(Q), S(Q), beta(Q), ...)."""
    plots = []
    for name, result in return_data['intermediate_results'].items():
        if isinstance(result, tuple) and len(result) > 1:
            result = result[1]
        if not isinstance(result, np.ndarray):
            continue
        plots.append(_plot_1d(tab_id, return_data['x'], result, return_data['model'], return_data['data'],
                              component=name))
    return plots


def scalar_results(return_data: dict) -> dict:
    """The intermediate results that are not arrays, e.g. the computed effective radius."""
    return {name: value for name, value in return_data.get("intermediate_results", {}).items()
            if not isinstance(value, np.ndarray)}


def default_1d(interval, tab_id=0) -> Data1D:
    """The theory grid of a 1D page without data."""
    data = Data1D(x=interval)
    data.xaxis('\\rm{Q}', "A^{-1}")
    data.yaxis('\\rm{Intensity}', "cm^{-1}")
    data.is_data = False
    data.id = str(tab_id) + " data"
    data.group_id = str(tab_id) + " Model1D"
    return data


def default_2d(qmax: float, qstep: int, tab_id=0) -> Data2D:
    """The theory grid of a 2D page without data: a square detector centred on the beam."""
    data = Data2D()
    data.xaxis('\\rm{Q_{x}}', 'A^{-1}')
    data.yaxis('\\rm{Q_{y}}', 'A^{-1}')
    data.is_data = False
    data.id = str(tab_id) + " data"
    data.group_id = str(tab_id) + " Model2D"
    detector = Detector()
    detector.distance = 8000   # mm
    detector.pixel_size.x = 5  # mm
    detector.pixel_size.y = 5  # mm
    detector.beam_center.x = qmax
    detector.beam_center.y = qmax
    data.detector.append(detector)
    x = np.linspace(start=-qmax, stop=qmax, num=qstep, endpoint=True)
    y = np.linspace(start=-qmax, stop=qmax, num=qstep, endpoint=True)
    qx_data = np.tile(x, (len(y), 1)).flatten()
    qy_data = np.tile(y, (len(x), 1)).swapaxes(0, 1).flatten()
    mask = np.ones(len(qx_data), dtype=bool)
    data.source = Source()
    data.data = np.ones(len(mask))
    data.err_data = np.ones(len(mask))
    data.qx_data = qx_data
    data.qy_data = qy_data
    data.q_data = np.sqrt(qx_data * qx_data + qy_data * qy_data)
    data.mask = mask
    data.x_bins = x
    data.y_bins = y
    data.xmin, data.xmax, data.ymin, data.ymax = -qmax, qmax, -qmax, qmax
    return data


def default_dataset(options, is2d: bool, tab_id):
    """The theory grid for the page's options (createDefaultDataset)."""
    if is2d:
        return default_2d(options.qmax / np.sqrt(2), options.npts, tab_id)
    if options.log_points:
        qmin = -10.0 if options.qmin < 1.e-10 else np.log10(options.qmin)
        qmax = 10.0 if options.qmax > 1.e10 else np.log10(options.qmax)
        interval = np.logspace(start=qmin, stop=qmax, num=options.npts, endpoint=True, base=10.0)
    else:
        interval = np.linspace(start=options.qmin, stop=options.qmax, num=int(options.npts), endpoint=True)
    return default_1d(interval, tab_id)


def data_range(data) -> tuple[float, float, int]:
    """(qmin, qmax, npts) of a dataset (computeRangeFromData)."""
    if isinstance(data, Data1D):
        try:
            return min(data.x), max(data.x), len(data.x)
        except (ValueError, TypeError):
            raise ValueError("Unable to find min/max/length of \n data named %s" % data.filename)
    try:
        x = max(np.fabs(data.xmin), np.fabs(data.xmax))
        y = max(np.fabs(data.ymin), np.fabs(data.ymax))
    except (ValueError, TypeError):
        raise ValueError("Unable to find min/max of \n data named %s" % data.filename)
    return 0, np.sqrt(x * x + y * y), len(data.data)


def has_errors(data) -> bool:
    """The dataset carries intensity errors (dI), so it can be weighted by them (FittingLogic.di_flag)."""
    errors = data.err_data if isinstance(data, Data2D) else data.dy
    return errors is not None and bool(np.any(errors))

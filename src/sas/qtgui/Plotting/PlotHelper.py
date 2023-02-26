"""
`Singleton` plot helper module
All its variables are bound to the module,
which can not be instantiated repeatedly so IDs are session-specific.
"""
import sys
import weakref

# TODO Refactor to allow typing without circular import
#from sas.qtgui.Plotting.PlotterBase import PlotterBase

this = sys.modules[__name__]

this._plots = weakref.WeakValueDictionary()
this._plot_id = 0

def clear():
    """
    Reset the plot dictionary
    """
    this._plots = weakref.WeakValueDictionary()

#def addPlot(plot: PlotterBase):
def addPlot(plot):
    """
    Adds a new plot to the current dictionary of plots
    """
    this._plot_id += 1
    this._plots["Graph%s"%str(this._plot_id)] = plot # TODO: Why???

def deletePlot(plot_id):
    """
    Deletes an existing plot from the dictionary
    """
    if plot_id in this._plots:
        del this._plots[plot_id]

def currentPlotIds():
    """
    Returns a list of IDs for all currently active plots
    """
    return list(this._plots.keys())

def plotById(plot_id):
    """
    Returns the plot referenced by the ID
    """
    return this._plots[plot_id] if plot_id in this._plots else None

def idOfPlot(plot):
    """
    Returns the ID of the plot
    """
    plot_id = None
    for key in list(this._plots.keys()):
        if this._plots[key] == plot:
            plot_id = key
            break

    return plot_id

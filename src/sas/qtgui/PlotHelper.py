"""
`Singleton` plot helper module
All its variables are bound to the module,
which can not be instantiated repeatedly so IDs are session-specific.
"""
import sys

this = sys.modules[__name__]

this._plots = {}
this._plot_id = 0

def clear():
    """
    Reset the plot dictionary
    """
    this._plots = {}

def addPlot(plot):
    """
    Adds a new plot to the current dictionary of plots
    """
    this._plot_id += 1
    this._plots[this._plot_id] = plot

def deletePlot(plot_id):
    """
    Deletes an existing plot from the dictionary
    """
    assert plot_id in this._plots
    del this._plots[plot_id]

def currentPlots():
    """
    Returns a list of IDs for all currently active plots
    """
    return this._plots.keys()

def plotById(plot_id):
    """
    Returns the plot referenced by the ID
    """
    assert plot_id in this._plots

    return this._plots[plot_id]

def idOfPlot(plot):
    """
    Returns the ID of the plot
    """
    plot_id = None
    for key in this._plots.keys():
        if this._plots[key] == plot:
            plot_id = key
            break

    return plot_id

import numpy as np

# a new plottable_hist that can be integrated into Data1D object in the future
class plottable_hist(object):
    """
    A class storing all the info needed to plot a bar graph
    Designed to be used in plt.bar instead of plt.hist
    """
    x = None # center of bins
    y = None # height of bins
    dy = None # errorbar of bins
    binWidth = None # width of bins
    
    # Units
    _xaxis = ''
    _xunit = ''
    _logx = False
    _yaxis = ''
    _yunit = ''
    
    def __init__(self, x, y, dy=None, binWidth=None):
        self.x = np.asarray(x)
        self.y = np.asarray(y)
        if dy is not None:
            self.dy = np.asarray(dy)
        if binWidth is not None:
            if len(binWidth) > 1:
                self.binWidth = np.asarray(binWidth)
            else:
                self.binWidth = binWidth

    def xaxis(self, label, unit, islog):
        """
        set the x axis label and unit
        """
        self._xaxis = label
        self._xunit = unit
        self._logx = islog

    def yaxis(self, label, unit):
        """
        set the y axis label and unit
        """
        self._yaxis = label
        self._yunit = unit
"""
Adapters for fitting module
"""
import copy
import numpy
import math
from data_util.uncertainty import Uncertainty
from danse.common.plottools.plottables import Data1D as PlotData1D
from danse.common.plottools.plottables import Data2D as PlotData2D
from danse.common.plottools.plottables import Theory1D as PlotTheory1D

from DataLoader.data_info import Data1D as LoadData1D
from DataLoader.data_info import Data2D as LoadData2D


class Data1D(PlotData1D, LoadData1D):
    """
    """
    def __init__(self, x=None, y=None, dx=None, dy=None):
        """
        """
        if x is None:
            x = []
        if y is None:
            y = []
        PlotData1D.__init__(self, x, y, dx, dy)
        LoadData1D.__init__(self, x, y, dx, dy)
        self.id = None
        self.group_id = None
        self.is_data = True
        self.path = None
        self.title = ""
    
    def copy_from_datainfo(self, data1d):
        """
        copy values of Data1D of type DataLaoder.Data_info
        """
        self.x  = copy.deepcopy(data1d.x)
        self.y  = copy.deepcopy(data1d.y)
        self.dy = copy.deepcopy(data1d.dy)
        
        if hasattr(data1d, "dx"):
            self.dx = copy.deepcopy(data1d.dx)    
        if hasattr(data1d, "dxl"):
            self.dxl = copy.deepcopy(data1d.dxl)
        if hasattr(data1d, "dxw"):
            self.dxw = copy.deepcopy(data1d.dxw)
    
        self.xaxis(data1d._xaxis, data1d._xunit)
        self.yaxis(data1d._yaxis, data1d._yunit)
        self.title = data1d.title
        
    def __str__(self):
        """
        print data
        """
        _str = "%s\n" % LoadData1D.__str__(self)
      
        return _str 
    
    def _perform_operation(self, other, operation):
        """
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
        result = Data1D(x=[], y=[], dx=None, dy=None)
        result.clone_without_data(clone=self)
        result.copy_from_datainfo(data1d=self)
        for i in range(len(self.x)):
            result.x[i] = self.x[i]
            if self.dx is not None and len(self.x) == len(self.dx):
                result.dx[i] = self.dx[i]
            
            a = Uncertainty(self.y[i], dy[i]**2)
            if isinstance(other, Data1D):
                b = Uncertainty(other.y[i], dy_other[i]**2)
            else:
                b = other
            
            output = operation(a, b)
            result.y[i] = output.x
            if result.dy is None: result.dy = numpy.zeros(len(self.x))
            result.dy[i] = math.sqrt(math.fabs(output.variance))
        return result
    
  
    
class Theory1D(PlotTheory1D, LoadData1D):
    """
    """
    def __init__(self, x=None, y=None, dy=None):
        """
        """
        if x is None:
            x = []
        if y is None:
            y = []
        PlotTheory1D.__init__(self, x, y, dy)
        LoadData1D.__init__(self, x, y, dy)
        self.id = None
        self.group_id = None
        self.is_data = True
        self.path = None
        self.title = ""
    
    def copy_from_datainfo(self, data1d):
        """
        copy values of Data1D of type DataLaoder.Data_info
        """
        self.x  = copy.deepcopy(data1d.x)
        self.y  = copy.deepcopy(data1d.y)
        self.dy = copy.deepcopy(data1d.dy)
        if hasattr(data1d, "dx"):
            self.dx = copy.deepcopy(data1d.dx) 
        if hasattr(data1d, "dxl"):
            self.dxl = copy.deepcopy(data1d.dxl)
        if hasattr(data1d, "dxw"):
            self.dxw = copy.deepcopy(data1d.dxw)    
        self.xaxis(data1d._xaxis, data1d._xunit)
        self.yaxis(data1d._yaxis, data1d._yunit)
        self.title = data1d.title
        
    def __str__(self):
        """
        print data
        """
        _str = "%s\n" % LoadData1D.__str__(self)
      
        return _str 
    
    def _perform_operation(self, other, operation):
        """
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
        result = Theory1D(x=[], y=[], dy=None)
        result.clone_without_data(clone=self)
        result.copy_from_datainfo(data1d=self)
        for i in range(len(self.x)):
            result.x[i] = self.x[i]
           
            a = Uncertainty(self.y[i], dy[i]**2)
            if isinstance(other, Data1D):
                b = Uncertainty(other.y[i], dy_other[i]**2)
            else:
                b = other
            output = operation(a, b)
            result.y[i] = output.x
            if result.dy is None:
                result.dy = numpy.zeros(len(self.x))
            result.dy[i] = math.sqrt(math.fabs(output.variance))
        return result
    
      
class Data2D(PlotData2D, LoadData2D):
    """
    """
    def __init__(self, image=None, err_image=None,
                 xmin=None, xmax=None, ymin=None, ymax=None,
                 zmin=None, zmax=None, qx_data=None, qy_data=None,
                 q_data=None, mask=None, dqx_data=None, dqy_data=None):
        """
        """
        PlotData2D.__init__(self, image=image, err_image=err_image,
                            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                            zmin=zmin, zmax=zmax, qx_data=qx_data, 
                            qy_data=qy_data)
        
        LoadData2D.__init__(self, data=image, err_data=err_image,
                            qx_data=qx_data, qy_data=qy_data,
                            dqx_data=dqx_data, dqy_data=dqy_data,
                            q_data=q_data, mask=mask)
        self.id = None
        self.path = None
        self.title = ""
      
        
    def copy_from_datainfo(self, data2d):
        """
        copy value of Data2D of type DataLoader.data_info
        """
        self.data = copy.deepcopy(data2d.data)
        self.qx_data = copy.deepcopy(data2d.qx_data)
        self.qy_data = copy.deepcopy(data2d.qy_data)
        self.q_data = copy.deepcopy(data2d.q_data)
        self.mask = copy.deepcopy(data2d.mask)
        self.err_data = copy.deepcopy(data2d.err_data)
        self.x_bins = copy.deepcopy(data2d.x_bins)
        self.y_bins = copy.deepcopy(data2d.y_bins)
        if data2d.dqx_data is not None:
            self.dqx_data = copy.deepcopy(data2d.dqx_data)
        if data2d.dqy_data is not None:
            self.dqy_data = copy.deepcopy(data2d.dqy_data)
        self.xmin = data2d.xmin
        self.xmax = data2d.xmax
        self.ymin = data2d.ymin
        self.ymax = data2d.ymax
        if hasattr(data2d, "zmin"):
            self.zmin = data2d.zmin
        if hasattr(data2d, "zmax"):
            self.zmax = data2d.zmax
        self.xaxis(data2d._xaxis, data2d._xunit)
        self.yaxis(data2d._yaxis, data2d._yunit)
        self.title = data2d.title
        
    def __str__(self):
        """
        print data
        """
        _str = "%s\n" % LoadData2D.__str__(self)
        return _str 
    
    def _perform_operation(self, other, operation):
        """
        Perform 2D operations between data sets
        
        :param other: other data set
        :param operation: function defining the operation
        
        """
        # First, check the data compatibility
        dy, dy_other = self._validity_check(other)
    
        result = Data2D(image=None, qx_data=None, qy_data=None,
                         err_image=None, xmin=None, xmax=None,
                         ymin=None, ymax=None, zmin=None, zmax=None)
        
        result.clone_without_data(clone=self)
        result.copy_from_datainfo(data2d=self)
        
        for i in range(numpy.size(self.data, 0)):
            for j in range(numpy.size(self.data, 1)):
                result.data[i][j] = self.data[i][j]
                if self.err_data is not None and \
                        numpy.size(self.data) == numpy.size(self.err_data):
                    result.err_data[i][j] = self.err_data[i][j]
                
                a = Uncertainty(self.data[i][j], dy[i][j]**2)
                if isinstance(other, Data2D):
                    b = Uncertainty(other.data[i][j], dy_other[i][j]**2)
                else:
                    b = other
                output = operation(a, b)
                result.data[i][j] = output.x
                result.err_data[i][j] = math.sqrt(math.fabs(output.variance))
        return result
        
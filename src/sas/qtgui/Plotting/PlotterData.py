"""
Adapters for fitting module
"""
import copy
import numpy
import math
from sas.sascalc.data_util.uncertainty import Uncertainty

from sas.qtgui.Plotting.Plottables import PlottableData1D
from sas.qtgui.Plotting.Plottables import PlottableData2D

from sas.sascalc.dataloader.data_info import Data1D as LoadData1D
from sas.sascalc.dataloader.data_info import Data2D as LoadData2D


class Data1D(PlottableData1D, LoadData1D):
    """
    """
    def __init__(self, x=None, y=None, dx=None, dy=None):
        """
        """
        if x is None:
            x = []
        if y is None:
            y = []
        PlottableData1D.__init__(self, x, y, dx, dy)
        LoadData1D.__init__(self, x, y, dx, dy)
        self.id = None
        self.list_group_id = []
        self.group_id = None
        self.is_data = True
        self.path = None
        self.xtransform = None
        self.ytransform = None
        self.title = ""
        self.scale = None
        
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
        self.isSesans = data1d.isSesans
        
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
        result.clone_without_data(length=len(self.x), clone=self)
        result.copy_from_datainfo(data1d=self)
        if self.dxw is None:
            result.dxw = None
        else:
            result.dxw = numpy.zeros(len(self.x))
        if self.dxl is None:
            result.dxl = None
        else:
            result.dxl = numpy.zeros(len(self.x))

        for i in range(len(self.x)):
            result.x[i] = self.x[i]
            if self.dx is not None and len(self.x) == len(self.dx):
                result.dx[i] = self.dx[i]
            if self.dxw is not None and len(self.x) == len(self.dxw):
                result.dxw[i] = self.dxw[i]
            if self.dxl is not None and len(self.x) == len(self.dxl):
                result.dxl[i] = self.dxl[i]
            
            a = Uncertainty(self.y[i], dy[i]**2)
            if isinstance(other, Data1D):
                b = Uncertainty(other.y[i], dy_other[i]**2)
                if other.dx is not None:
                    result.dx[i] *= self.dx[i]
                    result.dx[i] += (other.dx[i]**2)
                    result.dx[i] /= 2
                    result.dx[i] = math.sqrt(result.dx[i])
                if result.dxl is not None and other.dxl is not None:
                    result.dxl[i] *= self.dxl[i]
                    result.dxl[i] += (other.dxl[i]**2)
                    result.dxl[i] /= 2
                    result.dxl[i] = math.sqrt(result.dxl[i])
            else:
                b = other
            
            output = operation(a, b)
            result.y[i] = output.x
            result.dy[i] = math.sqrt(math.fabs(output.variance))
        return result
    
    def _perform_union(self, other):
        """
        """
        # First, check the data compatibility
        self._validity_check_union(other)
        result = Data1D(x=[], y=[], dx=None, dy=None)
        tot_length = len(self.x) + len(other.x)
        result = self.clone_without_data(length=tot_length, clone=result)
        if self.dy is None or other.dy is None:
            result.dy = None
        else:
            result.dy = numpy.zeros(tot_length)
        if self.dx is None or other.dx is None:
            result.dx = None
        else:
            result.dx = numpy.zeros(tot_length)
        if self.dxw is None or other.dxw is None:
            result.dxw = None
        else:
            result.dxw = numpy.zeros(tot_length)
        if self.dxl is None or other.dxl is None:
            result.dxl = None
        else:
            result.dxl = numpy.zeros(tot_length)

        result.x = numpy.append(self.x, other.x)
        #argsorting
        ind = numpy.argsort(result.x)
        result.x = result.x[ind]
        result.y = numpy.append(self.y, other.y)
        result.y = result.y[ind]
        if result.dy is not None:
            result.dy = numpy.append(self.dy, other.dy)
            result.dy = result.dy[ind]
        if result.dx is not None:
            result.dx = numpy.append(self.dx, other.dx)
            result.dx = result.dx[ind]
        if result.dxw is not None:
            result.dxw = numpy.append(self.dxw, other.dxw)
            result.dxw = result.dxw[ind]
        if result.dxl is not None:
            result.dxl = numpy.append(self.dxl, other.dxl)
            result.dxl = result.dxl[ind]
        return result

class Data2D(PlottableData2D, LoadData2D):
    """
    """
    def __init__(self, image=None, err_image=None,
                 qx_data=None, qy_data=None, q_data=None, 
                 mask=None, dqx_data=None, dqy_data=None, 
                 xmin=None, xmax=None, ymin=None, ymax=None,
                 zmin=None, zmax=None):
        """
        """
        PlottableData2D.__init__(self, image=image, err_image=err_image,
                            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                            zmin=zmin, zmax=zmax, qx_data=qx_data, 
                            qy_data=qy_data)
        
        LoadData2D.__init__(self, data=image, err_data=err_image,
                            qx_data=qx_data, qy_data=qy_data,
                            dqx_data=dqx_data, dqy_data=dqy_data,
                            q_data=q_data, mask=mask)
        self.id = None
        self.list_group_id = []
        self.group_id = None
        self.is_data = True
        self.path = None
        self.xtransform = None
        self.ytransform = None
        self.title = ""
        self.scale = None
        
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
                         q_data=None, err_image=None, xmin=None, xmax=None,
                         ymin=None, ymax=None, zmin=None, zmax=None)
        result.clone_without_data(len(self.data))
        result.copy_from_datainfo(data2d=self)
        result.xmin = self.xmin
        result.xmax = self.xmax
        result.ymin = self.ymin
        result.ymax = self.ymax
        if self.dqx_data is None or self.dqy_data is None:
            result.dqx_data = None
            result.dqy_data = None
        else:
            result.dqx_data = numpy.zeros(len(self.data))
            result.dqy_data = numpy.zeros(len(self.data))
        for i in range(numpy.size(self.data)):
            result.data[i] = self.data[i]
            if self.err_data is not None and \
                numpy.size(self.data) == numpy.size(self.err_data):
                result.err_data[i] = self.err_data[i]    
            if self.dqx_data is not None:
                result.dqx_data[i] = self.dqx_data[i]
            if self.dqy_data is not None:
                result.dqy_data[i] = self.dqy_data[i]
            result.qx_data[i] = self.qx_data[i]
            result.qy_data[i] = self.qy_data[i]
            result.q_data[i] = self.q_data[i]
            result.mask[i] = self.mask[i]
            
            a = Uncertainty(self.data[i], dy[i]**2)
            if isinstance(other, Data2D):
                b = Uncertainty(other.data[i], dy_other[i]**2)
                if other.dqx_data is not None and \
                        result.dqx_data is not None:
                    result.dqx_data[i] *= self.dqx_data[i]
                    result.dqx_data[i] += (other.dqx_data[i]**2)
                    result.dqx_data[i] /= 2
                    result.dqx_data[i] = math.sqrt(result.dqx_data[i])     
                if other.dqy_data is not None and \
                        result.dqy_data is not None:
                    result.dqy_data[i] *= self.dqy_data[i]
                    result.dqy_data[i] += (other.dqy_data[i]**2)
                    result.dqy_data[i] /= 2
                    result.dqy_data[i] = math.sqrt(result.dqy_data[i])
            else:
                b = other
            
            output = operation(a, b)
            result.data[i] = output.x
            result.err_data[i] = math.sqrt(math.fabs(output.variance))
        return result
    
    def _perform_union(self, other):
        """
        Perform 2D operations between data sets
        
        :param other: other data set
        :param operation: function defining the operation
        
        """
        # First, check the data compatibility
        self._validity_check_union(other)
        result = Data2D(image=None, qx_data=None, qy_data=None,
                         q_data=None, err_image=None, xmin=None, xmax=None,
                         ymin=None, ymax=None, zmin=None, zmax=None)
        length = len(self.data)
        tot_length = length + len(other.data)
        result.clone_without_data(tot_length)
        result.xmin = self.xmin
        result.xmax = self.xmax
        result.ymin = self.ymin
        result.ymax = self.ymax
        if self.dqx_data is None or self.dqy_data is None or \
                other.dqx_data is None or other.dqy_data is None :
            result.dqx_data = None
            result.dqy_data = None
        else:
            result.dqx_data = numpy.zeros(len(self.data) + \
                                         numpy.size(other.data))
            result.dqy_data = numpy.zeros(len(self.data) + \
                                         numpy.size(other.data))
        
        result.data = numpy.append(self.data, other.data)
        result.qx_data = numpy.append(self.qx_data, other.qx_data)
        result.qy_data = numpy.append(self.qy_data, other.qy_data)
        result.q_data = numpy.append(self.q_data, other.q_data)
        result.mask = numpy.append(self.mask, other.mask)
        if result.err_data is not None:
            result.err_data = numpy.append(self.err_data, other.err_data) 
        if self.dqx_data is not None:
            result.dqx_data = numpy.append(self.dqx_data, other.dqx_data)
        if self.dqy_data is not None:
            result.dqy_data = numpy.append(self.dqy_data, other.dqy_data)

        return result

def check_data_validity(data):
    """
    Return True is data is valid enough to compute chisqr, else False
    """
    flag = True
    if data is not None:
        if issubclass(data.__class__, Data2D):
            if (data.data is None) or (len(data.data) == 0)\
            or (len(data.err_data) == 0):
                flag = False
        else:
            if (data.y is None) or (len(data.y) == 0): 
                flag = False
        if not data.is_data:
            flag = False
    else:
        flag = False
    return flag

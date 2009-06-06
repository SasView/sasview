"""
    A Data1D class compatible with guiframe from the output of DataLoader. 
"""
from danse.common.plottools.plottables import Data1D as plotData1D
from danse.common.plottools.plottables import Theory1D as plotTheory1D

from DataLoader.data_info import Data1D as loader_data_1D

class Data1D(plotData1D, loader_data_1D):
    """
        A Data1D class compatible with guiframe from 
        the output of DataLoader. The new class inherits 
        from DataLoader.data_info.Data1D
    """
    def __init__(self,x=[],y=[],dx=None,dy=None,dxl=None, dxw=None):
        plotData1D.__init__(self, x, y, dx, dy)
        loader_data_1D.__init__(self, x=x, y=y, dx=dx, dy=dy)
        self.smearer=None
       
        self.dxl = dxl
        self.dxw = dxw
 
class Theory1D(plotTheory1D, loader_data_1D):
    """
        A Theory1D class compatible with guiframe from 
        the output of DataLoader. The new class inherits 
        from DataLoader.data_info.Data1D
    """
    def __init__(self,x=[],y=[],dy=None,dxl=None, dxw=None):
        plotTheory1D.__init__(self, x, y)
        loader_data_1D.__init__(self, x=x, y=y, dx=dx, dy=dy)
        self.smearer=None
        
        self.dxl = dxl
        self.dxw = dxw
 
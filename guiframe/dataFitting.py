"""
    Adapters for fitting module
"""
from danse.common.plottools.plottables import Data1D as plotData1D
from danse.common.plottools.plottables import Theory1D as plotTheory1D

from DataLoader.data_info import DataInfo

class Data1D(plotData1D,DataInfo):
    
    def __init__(self,x=[],y=[],dx=None,dy=None,dxl=None, dxw=None):
        plotData1D.__init__(self, x, y, dx, dy)
        self.smearer=None
       
        self.dxl = dxl
        self.dxw = dxw
 
class Theory1D(plotTheory1D,DataInfo):
    def __init__(self,x=[],y=[],dy=None,dxl=None, dxw=None):
        plotTheory1D.__init__(self, x, y)
        self.smearer=None
        
        self.dxl = dxl
        self.dxw = dxw
 
"""
    Class that manages what is being displayed on the 1D plot
    of a SANS modeling application
    
    TODO: Eliminate the code to re-read the data in menu_Simple and Menu_Guinier.
          Modify the way you store and handle the data in Data1D
          
    TODO: use only one menu entry for "Toggle between Q and Q**2 scale" instead
          of have one menu entry for Q and one menu entry for Q**2.
          You want to be consistent in the way you present options for the x-axis
          and y-axis.
            
"""

import wx
import wx.lib.newevent

(FunctionParamEvent, EVT_FUNC_PARS) = wx.lib.newevent.NewEvent()

from PlotPanel import PlotPanel
import numpy, pylab
from plottables import Plottable, Graph
import os
import math
from scipy import optimize



DEFAULT_QMIN = 0
DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001


class Data1D(Plottable):
    """Data plottable: scatter plot of x,y with errors in x and y.
    """
    
    def __init__(self,x,y,dx=None,dy=None):
        """Draw points specified by x[i],y[i] in the current color/symbol.
        Uncertainty in x is given by dx[i], or by (xlo[i],xhi[i]) if the
        uncertainty is asymmetric.  Similarly for y uncertainty.

        The title appears on the legend.
        The label, if it is different, appears on the status bar.
        """
        self.name = "DATA"
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.hidden = False
        
        

    def render(self,plot,**kw):
        plot.curve(self.x,self.y,dy=self.dy,**kw)

    def changed(self):
        return False

    @classmethod
    def labels(cls, collection):
        """Build a label mostly unique within a collection"""
        map = {}
        for item in collection:
            map[item] = r"$\rm{%s}$" % item.name
        return map


class ModelPanel1D(PlotPanel):
    def __init__(self, parent, id = -1, color = None,\
        dpi = None, style = wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        PlotPanel.__init__(self, parent, id = id, style = style, **kwargs)

        self.parent = parent
        self.qmin = DEFAULT_QMIN
        self.qmax = DEFAULT_QMAX
        self.qstep = DEFAULT_QSTEP
        
        self.figure.subplots_adjust(bottom=.25)

        self.set_yscale('log')
        self.set_xscale('linear')
        self.x = pylab.arange(self.qmin, self.qmax+self.qstep*0.01, self.qstep)
        # Error on x 
        self.dx = numpy.zeros(len(self.x))
        # Intensity values
        y  = numpy.ones(len(self.x))
        # Error on y
        self.dy = numpy.zeros(len(self.x))
 
        # Plottables
        self.file_data = Data1D(x=[], y=[], dx=[], dy=[])
        self.file_data.name = "Loaded 1D data"
        
        self.t = pylab.arange(0.0, 10, 1)
        self.r = [0,3,2,4.5,6,1,2,4,7,9]
        self.file_data1 = Data1D(x=self.t, y=[], dx=self.r, dy=self.r)
        
        # Graph        
        self.graph = Graph()
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.add(self.file_data)
        #self.graph.add(self.file_data1)
        self.graph.render(self)
        
        
        # Bind events
        self.parent.Bind(EVT_FUNC_PARS, self._onEVT_FUNC_PARS)

    def onSave1DData(self, evt):
        """
            Saves the date in a file
            @param evt: wx event
        """
        path = None
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.txt", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            print path
        dlg.Destroy()
        if not path == None:
        
            out = open(path, 'w')
            out.write("<q>   <I_1D>\n")
            for i in range(len(self.file_data.x)):
                out.write("%g  %g\n" % (self.file_data.x[i], self.file_data.y[i]))
            out.close()
            
    def onContextMenu(self, event):
        """
            Pop up a context menu
        """
        # Slicer plot popup menu
        slicerpop = wx.Menu()
        slicerpop.Append(314, "&Save 1D model points (%s)" % self.file_data.name,
                              'Save randomly oriented data currently displayed')
        
        slicerpop.Append(316, '&Load 1D data file')
        slicerpop.Append(321, '&Display Error')
        slicerpop.AppendSeparator()
        # Those labels were wrong. The way you coded it, it's note necessarily log(I)!
        slicerpop.Append(315, '&Toggle Linear/Log intensity scale Y-axis')
        slicerpop.Append(319, '&Plot Q')
        slicerpop.Append(317, '&Plot Q**2')
        slicerpop.Append(320, '&Plot log(Q)')
       
        wx.EVT_MENU(self, 314, self.onSave1DData)
        wx.EVT_MENU(self, 315, self._onToggleScale)
        wx.EVT_MENU(self, 316, self._onLoad1DData)
        
        wx.EVT_MENU(self, 319, self._onLinearQ)
        wx.EVT_MENU(self, 317, self._onSquaredQ)
        wx.EVT_MENU(self, 320, self._onLogQ)
        wx.EVT_MENU(self, 321, self._onError)
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
        
    def _onError(self, event):
        print self.file_data1.dx
        a,b,c=self.points(x=self.file_data1.x, y=self.file_data1.y, \
                    dx=self.file_data1.dx , dy=self.file_data1.dy)
       
        self.graph.add(b)
        #self.graph.add(c)
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
    def _onFit(self,event):
        print "the SansFit goes here"
        
    def _onEVT_FUNC_PARS(self, event):
        """
            Plot x * cstA + cstB
        """
        a=event.cstA
        b=event.cstB
        temp=[]
        
        if self.file_data.x:
            for x_i in self.file_data.x:
                temp.append(Line_function(x_i,a,b))
            self.file_data1.y =temp
            self.file_data1.x= self.file_data.x 
        else:  
        
            for x_i in self.file_data1.x:
                temp.append(Line_function(x_i,a,b))
        self.file_data1.y =temp
     
        self.file_data1.name = "Loaded 1D data"     
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.add(self.file_data1)
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        
    def _onLoad1DData(self, event):
        """
            Load a data file
        """
        path = None
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.txt", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
        dlg.Destroy()

        file_x = []
        file_y = []
        if not path == None:
            self.path =path
            input_f = open(path,'r')
            buff = input_f.read()
            lines = buff.split('\n')
            for line in lines:
                try:
                    toks = line.split()
                    x = float(toks[0])
                    y = float(toks[1])
                    file_x.append(x)
                    file_y.append(y)
                except:
                    print "READ ERROR", line
            
        self.file_data.x = file_x 
        self.file_data.y = file_y
        
        self.file_data.name = "Loaded 1D data"     
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        
        self.graph.add(self.file_data)
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def onMenuGuinier(self, event):
        """
            This method plot I vs Q**2    
        """ 
        file_x =[]
        for entry in self.file_data.x:
            file_x.append(entry * entry)
        self.file_data.x = file_x
        self.graph.xaxis('\\rm{q**2  } ', 'A^{-2}')
             
    def _onSquaredQ(self, event):
        """
            This method plots Q**2 
        """
        self.graph.xaxis('\\rm{q}^2 ', 'A^{-2}')
        self.set_xscale('squared')

        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def _onLinearQ(self, event):
        """
            This method plots Q    
        """
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')     
        self.set_xscale('linear')
      
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def _onToggleScale(self, event):
        """
            Toggle the scale of the y-axis
        """
        if self.get_yscale() == 'log':
            self.set_yscale('linear')
        else:
            self.set_yscale('log')
        self.subplot.figure.canvas.draw_idle()

    def _onLogQ(self, event):
        """
            Plot log(q)
        """
        self.set_xscale('log')
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        
        
def Line_function(x, paramA, paramB):
    """
       linear function
    """
    return x * paramA + paramB

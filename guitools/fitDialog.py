#!/usr/bin/python

# fitDialog.py

import wx
from PlotPanel import PlotPanel
from plottables import Theory1D
import math,pylab,fittings
class LinearFit(wx.Dialog):
    #def __init__(self, parent, id, title):
    def __init__(self, parent, plottable, push_data, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(500, 300))
        """
            for the fit window
        """
        self.parent = parent
        #dialog panel self call function to plot the fitting function
        self.push_data = push_data
        #dialog self plottable
        self.plottable = plottable
        
        #Dialog interface
        panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)   
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5,0)
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
 
        self.tcA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcChi = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcXmin = wx.TextCtrl(panel,-1,style=wx.SIMPLE_BORDER)
        self.tcXmax = wx.TextCtrl(panel,-1,style=wx.SIMPLE_BORDER)
        self.btFit =wx.Button(panel,-1,'Fit' )
        btClose =wx.Button(panel, wx.ID_CANCEL,'Close' )
        
        ix = 1
        iy = 1
        sizer.Add(wx.StaticText(panel, -1, 'y = Ax +B'),(iy, ix))
        ix = 1
        iy += 2
        sizer.Add(wx.StaticText(panel, -1, 'Param A'),(iy, ix))
        ix += 1
        sizer.Add(self.tcA, (iy, ix))
        ix += 1
        sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix))
        ix += 1
        sizer.Add(self.tcErrA, (iy, ix))
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Param B'),(iy, ix))
        ix += 1
        sizer.Add(self.tcB, (iy, ix))
        ix += 1
        sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix))
        ix += 1
        sizer.Add(self.tcErrB, (iy, ix))
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Chi ^{2}'),(iy, ix))
        ix += 1
        sizer.Add(self.tcChi, (iy, ix))
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Xmin'),(iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(panel, -1, 'Xmax'),(iy, ix))
        iy += 1
        ix = 1
        sizer.Add(self.tcXmin, (iy, ix))
        ix += 2
        sizer.Add(self.tcXmax, (iy, ix))
        iy += 1
        ix = 1
        sizer.Add(self.btFit, (iy, ix))
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit)
        ix += 2
        sizer.Add(btClose, (iy, ix))
       
        panel.SetSizer(sizer)
        self.SetSizer(vbox)
        self.Centre()
        # Receives the type of model for the fitting
        from LineModel import LineModel
        self.model  = LineModel()
        # new data for the fit 
        self.file_data1 = Theory1D(x=[], y=[], dy=None)
        self.file_data1.name = "y= exp(A + bx**2)"
        
    def _onFit(self ,event):
       
        print "we are on fit"
        temp =[]
        tempdx =[]
        tempdy =[]
        xmin = self._checkVal(self.tcXmin.GetValue())
        xmax = self._checkVal(self.tcXmax.GetValue())
        #x= self.plottable.view.x
        x=self.plottable.returnXvalueOfView()
        print "x value :" ,x
        if x != []:
            if xmin !=None  and xmax != None:
                for j in range(len(x)):
                    if x[j]>xmin and x[j]<xmax:
                        temp.append(self.model.run(x[j]))
                        #tempdx.append(math.sqrt(x[j]))
                        for y_i in temp:
                            tempdy.append(math.sqrt(y_i)) 
            else:
                # x has a default value in case the user doesn't load data
                for x_i in x:
                    temp.append(self.model.run(x_i))
                    tempdx.append(math.sqrt(x_i))
                for y_i in temp:
                    tempdy.append(math.sqrt(y_i))
                    self.tcXmin.SetValue(str(min(x)))
                    self.tcXmax.SetValue(str(max(x)))
                    xmin = self._checkVal(self.tcXmin.GetValue())
                    xmax = self._checkVal(self.tcXmax.GetValue())
                
            self.file_data1.x =x
            self.file_data1.y =temp
            #self.file_data1.dx=tempdx
            self.file_data1.dx=None
            #self.file_data1.dy=tempdy
            self.file_data1.dy=None
            
        
            # Display the fittings values
            default_A = self.model.getParam('A') 
            default_B = self.model.getParam('B') 
            cstA = fittings.Parameter(self.model, 'A', default_A)
            cstB  = fittings.Parameter(self.model, 'B', default_B)        
            chisqr, out, cov = fittings.sansfit(self.model, 
                [cstA, cstB], self.plottable.view.x, 
                self.plottable.view.y, self.plottable.view.dy,xmin,xmax)
            # Create new data plottable with result
            
            self.file_data1.y = []
            #for x_i in self.file_data1.x:
            for x_i in self.file_data1.x:
                self.file_data1.y.append(self.model.run(x_i))
                
            self.push_data(self.file_data1)
            if cov ==None:
                errA =str(0.0)
                errB =str(0.0)
            else:
                errA= str(math.sqrt(cov[0][0]))
                errB= str(math.sqrt(cov[1][1]))
            if out==None:
                cstA=str(0.0)
                cstB=str(0.0)
            else:
                cstA=str(out[0])
                cstB=str(out[1])
            self._onsetValues(cstA, cstB, errA,errB,str(chisqr))
       
    def _onsetValues(self,cstA,cstB,errA,errB,Chi):
        
         self.tcA.SetValue(cstA)
         self.tcB.SetValue(cstB)
         self.tcErrA.SetValue(errA)
         self.tcErrB.SetValue(errB)
         self.tcChi.SetValue(Chi)
         
    def _returnPlottable(self):
        return self.file_data1
    
    def _checkVal(self,value):
        """
                Ensure that fields parameter contains a value 
                before sending to fit in Plotter1D
        """
        try:
            param = float(value)
        except:
            param = None
        return param
if __name__ == "__main__": 
    app = wx.App()
    dialog=LinearFit(None, -1, 'Fitting')
    dialog.ShowModal()
    app.MainLoop()



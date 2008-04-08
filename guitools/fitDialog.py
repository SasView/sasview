#!/usr/bin/python

# fitDialog.py

import wx
from PlotPanel import PlotPanel
from plottables import Theory1D
import math,pylab,fittings
class LinearFit(wx.Dialog):
    #def __init__(self, parent, id, title):
    def __init__(self, parent, plottable, push_data,transform, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(550, 300))
        """
            for the fit window
        """
        self.parent = parent
        self.transform = transform
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
        self.tcXmin = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcXmax = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
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
        ix = 3
        sizer.Add(self.btFit, (iy, ix))
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit)
        iy +=1
        ix = 3
        sizer.Add(btClose, (iy, ix))
       
        panel.SetSizer(sizer)
        self.SetSizer(vbox)
        self.Centre()
        # Receives the type of model for the fitting
        from LineModel import LineModel
        self.model  = LineModel()
        # new data for the fit 
        self.file_data1 = Theory1D(x=[], y=[], dy=None)
        self.file_data1.name = "Fit"
        
    def _onFit(self ,event):
        """
            Performs the fit. Receive an event when clicking on the button Fit.Computes chisqr ,
            A and B parameters of the best linear fit y=Ax +B
            Push a plottable to 
        """
       
        temp =[]
        tempx=[]
        tempy=[]
        xmin = self._checkVal(self.tcXmin.GetValue())
        xmax = self._checkVal(self.tcXmax.GetValue())
        
        #store the values of View in x,y, dx,dy
        x,y,dx,dy=self.plottable.returnValuesOfView()
        self.xtrans,self.ytrans= self.transform()
        #Display the fittings values
        default_A = self.model.getParam('A') 
        default_B = self.model.getParam('B') 
        cstA = fittings.Parameter(self.model, 'A', default_A)
        cstB  = fittings.Parameter(self.model, 'B', default_B)
        if  self.ytrans == "Log(y)":
            for y_i in y:
                tempy.append(log(y_i))       
            chisqr, out, cov = fittings.sansfit(self.model, 
                            [cstA, cstB],x, tempy,dy,min(x),max(x))
        else :
            chisqr, out, cov = fittings.sansfit(self.model, 
                            [cstA, cstB],x, y,dy,min(x),max(x))
        #Check that cov and out are iterable before displaying them
        if cov ==None:
            errA =0.0
            errB =0.0
        else:
            errA= math.sqrt(cov[0][0])
            errB= math.sqrt(cov[1][1])
        if out==None:
            cstA=0.0
            cstB=0.0
        else:
            cstA=out[0]
            cstB=out[1]
        self.model.setParam('A', float(cstA))
        self.model.setParam('B', float(cstB))
        
        if x != []:
            if xmin !=None  and xmax != None:
                for j in range(len(x)):
                    if x[j] > xmin and x[j] < xmax:
                        temp.append(self.model.run(x[j]))
            else:
                # x has a default value in case the user doesn't load data
                for x_i in x:
                    temp.append(self.model.run(x_i))
                self.tcXmin.SetValue(str(min(x)))
                self.tcXmax.SetValue(str(max(x)))
                xmin = self._checkVal(self.tcXmin.GetValue())
                xmax = self._checkVal(self.tcXmax.GetValue())
                
            self.file_data1.x =x
            # Create new data plottable with result
            self.file_data1.y =[]
            self.xtrans, self.ytrans= self.transform()
            
            if self.ytrans == "Log(y)":
                for x_i in x:
                    self.file_data1.y.append(exp(self.model.run(x_i)))
            else:
                self.file_data1.y =temp     
            self.file_data1.dx=None
            self.file_data1.dy=None
            
            self.file_data1.reset_view()
            
            #Send the data to display to the PlotPanel
            #
            self.push_data(self.file_data1)
            # Display the fitting value on the Fit Dialog
            self._onsetValues(cstA, cstB, errA,errB,chisqr)
       
    def _onsetValues(self,cstA,cstB,errA,errB,Chi):
         """
              Display  the value on fit Dialog 
         """
         self.tcA.SetValue(str(cstA))
         self.tcB.SetValue(str(cstB))
         self.tcErrA.SetValue(str(errA))
         self.tcErrB.SetValue(str(errB))
         self.tcChi.SetValue(str(Chi))
         
    def _returnPlottable(self):
        return self.file_data1
    
    def _checkVal(self,value):
        """
                Ensure that field parameter contains a value 
                before sending to fit 
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



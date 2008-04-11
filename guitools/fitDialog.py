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
          
          
        #Display the fittings values
        self.default_A = self.model.getParam('A') 
        self.default_B = self.model.getParam('B') 
        self.cstA = fittings.Parameter(self.model, 'A', self.default_A)
        self.cstB  = fittings.Parameter(self.model, 'B', self.default_B)
        
        # Set default value of parameter in fit dialog
        self.tcA.SetLabel(str(self.default_A))
        self.tcB.SetLabel(str(self.default_B))
        self.tcErrA.SetLabel(str(0.0))
        self.tcErrB.SetLabel(str(0.0))
        self.tcChi.SetLabel(str(0.0))
        self.tcXmin.SetLabel(str(0.0))
        self.tcXmax.SetLabel(str(0.0))
        
        # new data for the fit 
        self.file_data1 = Theory1D(x=[], y=[], dy=None)
        self.file_data1.name = "Fit"
        
    def _onFit(self ,event):
        """
            Performs the fit. Receive an event when clicking on the button Fit.Computes chisqr ,
            A and B parameters of the best linear fit y=Ax +B
            Push a plottable to 
        """
        
        tempx=[]
        tempy=[]
        tempdy = []
        
        #Check if the field of Fit Dialog contain values and use the x max and min of the user
        xmin = self._checkVal(self.tcXmin.GetValue())
        xmax = self._checkVal(self.tcXmax.GetValue())
        
        #store the values of View in x,y, dx,dy
        x,y,dx,dy=self.plottable.returnValuesOfView()
        # Receive transformations of x and y
        self.xtrans,self.ytrans= self.transform()
        
                        
        if (xmin ==None)and (xmax == None):
            #Display the min and the max of x on fit dialog fields
            self.tcXmin.SetValue(str(min(x)))
            self.tcXmax.SetValue(str(max(x)))
      
        
        # Store the transformed values of view x, y,dy in variables  before the fit
        if  self.ytrans == "Log(y)":
            for y_i in y:
                tempy.append(math.log(y_i)) 
                dy = 1/y_i
                if dy >= y_i:
                    dy = 0.9*y_i
                tempdy.append(dy)
        else:
            tempy = y
        if  self.xtrans == "Log(x)":
            for x_i in x:
                tempx.append(math.log(x_i)) 
        else:
            tempx = x
            
        #Find the fitting parameters
        if (xmin !=None and xmin >= min(tempx) ) and (xmax != None and xmax <= max(tempx)):   
            chisqr, out, cov = fittings.sansfit(self.model, 
                        [self.cstA, self.cstB],tempx, tempy,tempdy,xmin,xmax)
        else:
            chisqr, out, cov = fittings.sansfit(self.model, 
                        [self.cstA, self.cstB],tempx, tempy,tempdy,min(tempx),max(tempx))
       
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
        # Reset model with the right values of A and B 
        self.model.setParam('A', float(cstA))
        self.model.setParam('B', float(cstB))
        tempy = []
        # Check if View contains a x array .we online fit when x exits
        # makes transformation for y as a line to fit
        if x != []:
            for j in range(len(x)): 
                    if (xmin !=None)and (xmax != None):
                        if (x[j] > xmin and x[j] < xmax):
                            y_model = self.model.run(x[j])
                    else:
                        # x has a default value in case the user doesn't load data
                        if self.xtrans == "Log(x)":
                            y_model = self.model.run(math.log(x[j]))
                        else:
                            y_model = self.model.run(x[j])
                    
                    if self.ytrans == "Log(y)":
                        tempy.append(math.exp(y_model))
                    else:
                        tempy.append(y_model)
                        
            # Create new data plottable with result
            self.file_data1.x =x 
            self.file_data1.y =[]  
            self.file_data1.y =tempy     
            self.file_data1.dx=None
            self.file_data1.dy=None
           
            #Load the view with the new values
            self.file_data1.reset_view()
            
            #Send the data to display to the PlotPanel
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



#!/usr/bin/python

# fitDialog.py

import wx
from PlotPanel import PlotPanel
from plottables import Theory1D
import math,pylab,fittings
import transform


class LinearFit(wx.Dialog):
    def __init__(self, parent, plottable, push_data,transform, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(450, 400))
        """
            Dialog window pops- up when select Linear fit on Context menu
            Displays fitting parameters
        """
        self.parent = parent
        self.transform = transform
        #dialog panel self call function to plot the fitting function
        self.push_data = push_data
        #dialog self plottable
        
        self.plottable = plottable
        # Receive transformations of x and y
        self.xLabel,self.yLabel,self.Avalue,self.Bvalue,\
        self.ErrAvalue,self.ErrBvalue,self.Chivalue= self.transform()
        #Dialog interface
        panel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)   
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5,5)
       
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
 
        self.tcA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcChi = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.xminFit = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.xmaxFit = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.xminTransFit = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.xmaxTransFit = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.initXmin = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.initXmax = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.btFit =wx.Button(panel,-1,'Fit',size=(120, 30))
        self.btClose =wx.Button(panel, wx.ID_CANCEL,'Close',size=(90, 30) )
        self.static_line_1 = wx.StaticLine(panel, -1)
        
        ix = 0
        iy = 1
        sizer.Add(wx.StaticText(panel, -1, 'y = Ax +B'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy+=1
        sizer.Add(wx.StaticText(panel, -1, 'Param A'),(iy, ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcA,(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrA, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Param B'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcB, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(panel, -1, '+/-'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrB, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Chi ^{2}'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcChi, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 1
        sizer.Add(wx.StaticText(panel, -1, 'Xmin'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(wx.StaticText(panel, -1, 'Xmax'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Plotted Range'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer.Add(self.initXmin, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.initXmax, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
       
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Fit Range of '+self.xLabel),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.xminTransFit, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.xmaxTransFit, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
      
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Fit Range of x'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.xminFit, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.xmaxFit, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 1
        
        sizer.Add(self.btFit, (iy, ix),(1,1), wx.LEFT|wx.ADJUST_MINSIZE, 0)
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit)
        ix += 2
        sizer.Add(self.btClose, (iy, ix),(1,1),\
                  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
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
        
        if self.Avalue==None:
            self.tcA.SetLabel(str(self.default_A))
        else :
            self.tcA.SetLabel(str(self.Avalue))
        if self.Bvalue==None:
            self.tcB.SetLabel(str(self.default_B))
        else:
            self.tcB.SetLabel(str(self.Bvalue))
        if self.ErrAvalue==None:
            self.tcErrA.SetLabel(str(0.0))
        else:
            self.tcErrA.SetLabel(str(self.ErrAvalue))
        if self.ErrBvalue==None:
            self.tcErrB.SetLabel(str(0.0))
        else:
            self.tcErrB.SetLabel(str(self.ErrBvalue))
        if self.Chivalue==None:
            self.tcChi.SetLabel(str(0.0))
        else:
            self.tcChi.SetLabel(str(self.Chivalue))
        if self.plottable.x !=[]:
            self.mini =min(self.plottable.x)
            self.maxi =max(self.plottable.x)
            #store the values of View in self.x,self.y,self.dx,self.dy
            self.x,self.y,self.dx,self.dy= self.plottable.returnValuesOfView()
            
            self.xminTransFit.SetLabel(str(min(self.x)))
            self.xmaxTransFit.SetLabel(str(max(self.x)))
            self.xminTransFit.Disable()
            self.xmaxTransFit.Disable()
            
            self.initXmin.SetValue(str(self.mini))
            self.initXmax.SetValue(str(self.maxi))
            self.initXmin.Disable()
            self.initXmax.Disable()
            
            self.xminFit.SetLabel(str(self.mini))
            self.xmaxFit.SetLabel(str(self.maxi))
        
      
    def _onFit(self ,event):
        """
            Performs the fit. Receive an event when clicking on the button Fit.Computes chisqr ,
            A and B parameters of the best linear fit y=Ax +B
            Push a plottable to 
        """
        tempx=[]
        tempy=[]
        tempdy = []
       
       
        
        
        # Check if View contains a x array .we online fit when x exits
        # makes transformation for y as a line to fit
        if self.x != []: 
            
                
            if(self.checkFitValues(self.xminFit) == True):
                #Check if the field of Fit Dialog contain values and use the x max and min of the user
                xmin,xmax = self._checkVal(self.xminFit.GetValue(),self.xmaxFit.GetValue())
                
                xminView=self.floatTransform(xmin)
                xmaxView=self.floatTransform(xmax)
                if (self.xLabel=="log10(x)"):
                    self.xminTransFit.SetValue(str(math.log10(xminView)))
                    self.xmaxTransFit.SetValue(str(math.log10(xmaxView)))
                else:
                    self.xminTransFit.SetValue(str(xminView))
                    self.xmaxTransFit.SetValue(str(xmaxView))
                self.xminTransFit.Disable()
                self.xmaxTransFit.Disable()
                # Store the transformed values of view x, y,dy in variables  before the fit
                if  self.yLabel.lower() == "log10(y)":
                    if (self.xLabel.lower() == "log10(x)"):
                        for i in range(len(self.x)):
                            if self.x[i]>= math.log10(xmin):
                                tempy.append(math.log10(self.y[i])) 
                                tempdy.append(transform.errToLogX(self.y[i],0,self.dy[i],0))
                    else:
                        for i in range(len(self.y)):
                            tempy.append(math.log10(self.y[i])) 
                            tempdy.append(transform.errToLogX(self.y[i],0,self.dy[i],0))
                else:
                    tempy = self.y
                    tempdy = self.dy
               
                if (self.xLabel.lower() == "log10(x)"):
                    for x_i in self.x:
                        if x_i >= math.log10(xmin):
                            tempx.append(math.log10(x_i)) 
                else:
                    tempx = self.x
              
                #Find the fitting parameters
                
                if (self.xLabel.lower() == "log10(x)"):
                    chisqr, out, cov = fittings.sansfit(self.model, [self.cstA, self.cstB],
                    tempx, tempy,tempdy,math.log10(xmin),math.log10(xmax))
                else:
                    chisqr, out, cov = fittings.sansfit(self.model, 
                                [self.cstA, self.cstB],tempx, tempy,tempdy,xminView,xmaxView)
                #print "this out",out
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
                
                tempx = []
                tempy = []
                y_model = 0.0
                # load tempy with the minimum transformation
               
                if self.xLabel == "log10(x)":
                    y_model = self.model.run(math.log10(xmin))
                    tempx.append(xmin)
                else:
                    y_model = self.model.run(xminView)
                    tempx.append(xminView)
                    
                if self.yLabel == "log10(y)":
                    tempy.append(math.pow(10,y_model))
                    print "tempy",tempy
                else:
                    tempy.append(y_model)
                    
                # load tempy with the maximum transformation
                if self.xLabel == "log10(x)":
                    y_model = self.model.run(math.log10(xmax))
                    tempx.append(xmax)
                else:
                    y_model = self.model.run(xmaxView)
                    tempx.append(xmaxView)
                    
                if self.yLabel == "log10(y)":
                    tempy.append(math.pow(10,y_model))
                else: 
                    tempy.append(y_model)
                #Set the fit parameter display when  FitDialog is opened again
                self.Avalue=cstA
                self.Bvalue=cstB
                self.ErrAvalue=errA
                self.ErrBvalue=errB
                self.Chivalue=chisqr
                self.push_data(tempx,tempy,xminView,xmaxView,xmin,xmax,self._ongetValues())
                
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
        
    def _ongetValues(self):
         """
              Display  the value on fit Dialog 
         """
         return self.Avalue, self.Bvalue,self.ErrAvalue,self.ErrBvalue,self.Chivalue
         
    
    def _checkVal(self,usermin, usermax):
        """
                Ensure that fields parameter contains a min and a max value 
                within x min and x max range
        """
        if float(usermin) < float(usermax):
            if float(usermin) >= float(self.mini) and float(usermin) < float(self.maxi):
                self.xminFit.SetValue(str(usermin))
            else:
                self.xminFit.SetValue(str(self.mini))
                
            if float(usermax) > float(self.mini) and float(usermax) <= float(self.maxi):
                self.xmaxFit.SetLabel(str(usermax))
            else:
                self.xmaxFit.SetLabel(str(self.maxi))
                
            mini =float(self.xminFit.GetValue())
            maxi =float(self.xmaxFit.GetValue())
            
            return mini, maxi
    def floatTransform(self,x):
        """
             transform a float.It is use to determine the x.View min and x.View max for values
             not in x
        """
        if ( self.xLabel=="x" ):
            return transform.toX(x)
        
        if ( self.xLabel=="x^(2)" ): 
            return transform.toX2(x)
        
        if (self.xLabel=="log10(x)" ):
            if x >0:
                return x
            else:
                raise ValueError,"cannot compute log of a negative number"
            
    def checkFitValues(self,item):
        """
            Check the validity of input values
        """
        flag = True
        value = item.GetValue()
        # Check for possible values entered
        if (self.xLabel=="log10(x)"):
            if (float(value) > 0):
                item.SetBackgroundColour(wx.WHITE)
                item.Refresh()
            else:
                flag = False
                item.SetBackgroundColour("pink")
                item.Refresh()
      
        return flag
       
    def setFitRange(self,xmin,xmax,xminTrans,xmaxTrans):
        """
            Set fit parameters
        """
        self.xminFit.SetValue(str(xmin))
        self.xmaxFit.SetValue(str(xmax))
        self.xminTransFit.SetValue(str(xminTrans))
        self.xmaxTransFit.SetValue(str(xmaxTrans))
        
   
if __name__ == "__main__": 
    app = wx.App()
    dialog=LinearFit(None, -1, 'Fitting')
    dialog.ShowModal()
    app.MainLoop()



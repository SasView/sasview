#!/usr/bin/python

# fitDialog.py

import wx
from PlotPanel import PlotPanel
from plottables import Theory1D
import math,pylab,fittings
import transform

def format_number(value, high=False):
    """
        Return a float in a standardized, human-readable formatted string 
    """
    try: 
        value = float(value)
    except:
        print "returning 0"
        return "0"
    
    if high:
        return "%-6.4g" % value
    else:
        return "%-5.3g" % value


class LinearFit(wx.Dialog):
    def __init__(self, parent, plottable, push_data,transform, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(400, 380))

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
        vbox  = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5,5)
       
        _BOX_WIDTH = 100
 
        self.tcA      = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcA.SetToolTipString("Fit value for the slope parameter.")
        self.tcErrA   = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcErrA.SetToolTipString("Error on the slope parameter.")
        self.tcB      = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcA.SetToolTipString("Fit value for the constant parameter.")
        self.tcErrB   = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcErrB.SetToolTipString("Error on the constant parameter.")
        self.tcChi    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.tcChi.SetToolTipString("Chi^2 over degrees of freedom.")
        self.xminFit  = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.xminFit.SetToolTipString("Enter the minimum value on the x-axis to be included in the fit.")
        self.xmaxFit  = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.xmaxFit.SetToolTipString("Enter the maximum value on the x-axis to be included in the fit.")
        self.xminTransFit = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.xminTransFit.SetToolTipString("Minimum value on the x-axis for the plotted data.")
        self.xmaxTransFit = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.xmaxTransFit.SetToolTipString("Maximum value on the x-axis for the plotted data.")
        self.initXmin = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.initXmin.SetToolTipString("Minimum value available on the x-axis for the plotted data.")
        self.initXmax = wx.TextCtrl(self,-1,size=(_BOX_WIDTH,20))
        self.initXmax.SetToolTipString("Maximum value available on the x-axis for the plotted data.")

        # Make the info box not editable
        #_BACKGROUND_COLOR = '#ffdf85'
        _BACKGROUND_COLOR = self.GetBackgroundColour()
        self.xminTransFit.SetEditable(False)
        self.xminTransFit.SetBackgroundColour(_BACKGROUND_COLOR)
        self.xmaxTransFit.SetEditable(False)
        self.xmaxTransFit.SetBackgroundColour(_BACKGROUND_COLOR)
        self.initXmin.SetEditable(False)
        self.initXmin.SetBackgroundColour(_BACKGROUND_COLOR)
        self.initXmax.SetEditable(False)
        self.initXmax.SetBackgroundColour(_BACKGROUND_COLOR)
        
        
        # Buttons on the bottom
        self.static_line_1 = wx.StaticLine(self, -1)
        self.btFit =wx.Button(self,-1,'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit)
        self.btFit.SetToolTipString("Perform fit.")
        self.btClose =wx.Button(self, wx.ID_CANCEL,'Close')
        
        # Intro
        explanation  = "Perform fit for y(x) = Ax + B"
        
        vbox.Add(sizer)
        
        ix = 0
        iy = 1
        sizer.Add(wx.StaticText(self, -1, explanation),(iy, ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 2
        sizer.Add(wx.StaticText(self, -1, 'Parameter A'),(iy, ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcA,(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(self, -1, '+/-'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrA, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Parameter B'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcB, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(wx.StaticText(self, -1, '+/-'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer.Add(self.tcErrB, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Chi2/dof'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.tcChi, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 2
        ix = 1
        sizer.Add(wx.StaticText(self, -1, 'Min'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(wx.StaticText(self, -1, 'Max'),(iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Maximum range'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        sizer.Add(self.initXmin, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.initXmax, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
       
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Fit range of '+self.xLabel),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.xminTransFit, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.xmaxTransFit, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
      
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(self, -1, 'Fit range of x'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.xminFit, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.xmaxFit, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 1
        
        vbox.Add(self.static_line_1, 0, wx.EXPAND, 0)
        
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.btFit, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btClose, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)        
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        
        
        
        sizer.Add(self.btFit, (iy, ix),(1,1), wx.LEFT|wx.ADJUST_MINSIZE, 0)
        
        
        #panel.SetSizer(sizer)
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
            self.tcA.SetLabel(format_number(self.default_A))
        else :
            self.tcA.SetLabel(format_number(self.Avalue))
        if self.Bvalue==None:
            self.tcB.SetLabel(format_number(self.default_B))
        else:
            self.tcB.SetLabel(format_number(self.Bvalue))
        if self.ErrAvalue==None:
            self.tcErrA.SetLabel(format_number(0.0))
        else:
            self.tcErrA.SetLabel(format_number(self.ErrAvalue))
        if self.ErrBvalue==None:
            self.tcErrB.SetLabel(format_number(0.0))
        else:
            self.tcErrB.SetLabel(format_number(self.ErrBvalue))
        if self.Chivalue==None:
            self.tcChi.SetLabel(format_number(0.0))
        else:
            self.tcChi.SetLabel(format_number(self.Chivalue))
        if self.plottable.x !=[]:
            self.mini =min(self.plottable.x)
            self.maxi =max(self.plottable.x)
            #store the values of View in self.x,self.y,self.dx,self.dy
            self.x,self.y,self.dx,self.dy= self.plottable.returnValuesOfView()
            
            
            self.xminTransFit.SetLabel(format_number(min(self.x)))
            self.xmaxTransFit.SetLabel(format_number(max(self.x)))
            
            self.initXmin.SetValue(format_number(self.mini))
            self.initXmax.SetValue(format_number(self.maxi))
            
            self.xminFit.SetLabel(format_number(self.mini))
            self.xmaxFit.SetLabel(format_number(self.maxi))
        
      
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
                    self.xminTransFit.SetValue(format_number(math.log10(xminView)))
                    self.xmaxTransFit.SetValue(format_number(math.log10(xmaxView)))
                else:
                    self.xminTransFit.SetValue(format_number(xminView))
                    self.xmaxTransFit.SetValue(format_number(xmaxView))
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
                
                # Use chi2/dof
                if len(tempx)>0:
                    chisqr = chisqr/len(tempx)
                
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
                self.Avalue=cstB
                self.Bvalue=cstA
                self.ErrAvalue=errA
                self.ErrBvalue=errB
                self.Chivalue=chisqr
                self.push_data(tempx,tempy,xminView,xmaxView,xmin,xmax,self._ongetValues())
                
                # Display the fitting value on the Fit Dialog
                self._onsetValues(cstB, cstA, errA,errB,chisqr)
               
               
            
    def _onsetValues(self,cstA,cstB,errA,errB,Chi):
         """
              Display  the value on fit Dialog 
         """
         self.tcA.SetValue(format_number(cstA))
         self.tcB.SetValue(format_number(cstB))
         self.tcErrA.SetValue(format_number(errA))
         self.tcErrB.SetValue(format_number(errB))
         self.tcChi.SetValue(format_number(Chi))
        
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
                self.xminFit.SetValue(format_number(float(usermin)))
            else:
                self.xminFit.SetValue(format_number(float(self.mini)))
                
            if float(usermax) > float(self.mini) and float(usermax) <= float(self.maxi):
                self.xmaxFit.SetLabel(format_number(float(usermax)))
            else:
                self.xmaxFit.SetLabel(format_number(float(self.maxi)))
                
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
        self.xminFit.SetValue(format_number(xmin))
        self.xmaxFit.SetValue(format_number(xmax))
        self.xminTransFit.SetValue(format_number(xminTrans))
        self.xmaxTransFit.SetValue(format_number(xmaxTrans))
        
  
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        plot = Theory1D([],[])
        dialog = LinearFit(None, plot, self.onFitDisplay,self.returnTrans, -1, 'Linear Fit')
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
        return 1
    
    def onFitDisplay(self, tempx,tempy,xminView,xmaxView,xmin,xmax,func):
        pass
        
    def returnTrans(self):
        return '','',0,0,0,0,0

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()

#!/usr/bin/python

# fitDialog.py

import wx
from PlotPanel import PlotPanel
from plottables import Theory1D
import math,pylab,fittings
import transform


class LinearFit(wx.Dialog):
    #def __init__(self, parent, id, title):
    def __init__(self, parent, plottable, push_data,transform, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(450, 300))
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
        sizer = wx.GridBagSizer(5,5)
       
        vbox.Add(panel, 1, wx.EXPAND | wx.ALL)
 
        self.tcA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrA = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcErrB = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.tcChi = wx.TextCtrl(panel, -1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.FXmin = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.FXmax = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.PXmin = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
        self.PXmax = wx.TextCtrl(panel,-1,size=(120,20),style=wx.SIMPLE_BORDER)
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
        sizer.Add(self.PXmin, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.PXmax, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer.Add(wx.StaticText(panel, -1, 'Fit Range'),(iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer.Add(self.FXmin, (iy, ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer.Add(self.FXmax, (iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
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
        self.tcA.SetLabel(str(self.default_A))
        self.tcB.SetLabel(str(self.default_B))
        self.tcErrA.SetLabel(str(0.0))
        self.tcErrB.SetLabel(str(0.0))
        self.tcChi.SetLabel(str(0.0))
        if self.plottable.x !=[]:
            self.mini =min(self.plottable.x)
            self.maxi =max(self.plottable.x)
            self.FXmin.SetLabel(str(self.mini))
            self.FXmax.SetLabel(str(self.maxi))
            
            self.PXmin.SetValue(str(self.mini))
            self.PXmax.SetValue(str(self.maxi))
            self.PXmin.Disable()
            self.PXmax.Disable()
       
        
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
        xmin,xmax = self._checkVal(self.FXmin.GetValue(),self.FXmax.GetValue())
       
        #store the values of View in x,y, dx,dy
        x,y,dx,dy=self.plottable.returnValuesOfView()
        # Receive transformations of x and y
        self.xtrans,self.ytrans= self.transform()
        
        # Check if View contains a x array .we online fit when x exits
        # makes transformation for y as a line to fit
        if x != []: 
            
            xminView=self.floatTransform(xmin)
            xmaxView=self.floatTransform(xmax)
        
            # Store the transformed values of view x, y,dy in variables  before the fit
            if  self.ytrans.lower() == "log10(y)":
                for y_i in y:
                    tempy.append(math.log10(y_i)) 
            else:
                tempy = y
            if  self.xtrans.lower() == "log10(x)":
                for x_i in x:
                    tempx.append(math.log10(x_i)) 
            else:
                tempx = x
                   
            for y_i in y:
                dy = 1/y_i
                if dy >= y_i:
                    dy = 0.9*y_i
                tempdy.append(dy)
                   
            #Find the fitting parameters
            print "X", tempx
            print "Y", tempy
            chisqr, out, cov = fittings.sansfit(self.model, 
                            [self.cstA, self.cstB],tempx, tempy,tempdy,xminView,xmaxView)
            
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
            print "this is constant A:",float(cstA)
            tempx = []
            tempy = []
            y_model = 0.0
            # load tempy with the minimum transformation
           
            if self.xtrans == "log10(x)":
                y_model = self.model.run(math.log10(xmin))
                tempx.append(xmin)
            else:
                y_model = self.model.run(xminView)
                tempx.append(xminView)
                
            if self.ytrans == "log10(y)":
                tempy.append(math.pow(10,y_model))
            else:
                tempy.append(y_model)
                
            # load tempy with the maximum transformation
            if self.xtrans == "log10(x)":
                y_model = self.model.run(math.log10(xmax))
                tempx.append(xmax)
            else:
                y_model = self.model.run(xmaxView)
                tempx.append(xmaxView)
                
            if self.ytrans == "log10(y)":
                tempy.append(math.pow(10,y_model))
            else: 
                tempy.append(y_model)
                
            
            print "this max",xmax
            print "this view xmax", xmaxView
            # Create new data plottable with result
            self.file_data1.x =[] 
            self.file_data1.y =[] 
            self.file_data1.x =tempx  
            self.file_data1.y =tempy     
            self.file_data1.dx=None
            self.file_data1.dy=None
            print "this is the min of data1",min(self.file_data1.x )
            print "this is the max of data1",max(self.file_data1.x )
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
    
    def _checkVal(self,usermin, usermax):
        """
                Ensure that fields parameter contains a min and a max value 
                within x min and x max range
        """
        if float(usermin) < float(usermax):
            if float(usermin) >= float(self.mini) and float(usermin) < float(self.maxi):
                self.FXmin.SetValue(str(usermin))
            else:
                self.FXmin.SetValue(str(self.mini))
                
            if float(usermax) > float(self.mini) and float(usermax) <= float(self.maxi):
                self.FXmax.SetLabel(str(usermax))
            else:
                self.FXmax.SetLabel(str(self.maxi))
                
            mini =float(self.FXmin.GetValue())
            maxi =float(self.FXmax.GetValue())
            
            return mini, maxi
    def floatTransform(self,x):
        """
             transform a float.It is use to determine the x.View min and x.View max for values
             not in x
        """
        if ( self.xtrans=="x" ):
            return transform.toX(x)
        
        if ( self.xtrans=="x^(2)" ):
            return transform.toX2(x)
        
        if (self.xtrans=="log10(x)" ):
            if x >0:
                return math.log10(x)
            else:
                raise ValueError,"cannot compute log of a negative number"
       
                
   
if __name__ == "__main__": 
    app = wx.App()
    dialog=LinearFit(None, -1, 'Fitting')
    dialog.ShowModal()
    app.MainLoop()



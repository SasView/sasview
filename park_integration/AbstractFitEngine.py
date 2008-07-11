
class FitEngine:
    
    def _concatenateData(self, listdata=[]):
        """  
            _concatenateData method concatenates each fields of all data contains ins listdata.
            @param listdata: list of data 
            
            @return xtemp, ytemp,dytemp:  x,y,dy respectively of data all combined
                if xi,yi,dyi of two or more data are the same the second appearance of xi,yi,
                dyi is ignored in the concatenation.
                
            @raise: if listdata is empty  will return None
            @raise: if data in listdata don't contain dy field ,will create an error
            during fitting
        """
        if listdata==[]:
            raise ValueError, " data list missing"
        else:
            xtemp=[]
            ytemp=[]
            dytemp=[]
               
            for data in listdata:
                for i in range(len(data.x)):
                    xtemp.append(data.x[i])
                    ytemp.append(data.y[i])
                    if data.dy is not None and len(data.dy)==len(data.y):   
                        dytemp.append(data.dy[i])
                    else:
                        raise RuntimeError, "Fit._concatenateData: y-errors missinge"
            return xtemp, ytemp,dytemp
    
      
class Parameter:
    """
        Class to handle model parameters
    """
    def __init__(self, model, name, value=None):
            self.model = model
            self.name = name
            if not value==None:
                self.model.setParam(self.name, value)
           
    def set(self, value):
        """
            Set the value of the parameter
        """
        self.model.setParam(self.name, value)

    def __call__(self):
        """ 
            Return the current value of the parameter
        """
        return self.model.getParam(self.name)
    


    
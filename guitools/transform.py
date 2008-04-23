import math  
         
def toX(x,y=None):
    """
    This function is used to load value on Plottable.View
    @param x: Float value
    @return x,
    """
    return x

def toX2(x,y=None):
    """
        This function is used to load value on Plottable.View
        Calculate x^(2)
        @param x: float value
    """
    return x*x

def fromX2(x,y=None):
     """
         This function is used to load value on Plottable.View
        Calculate square root of x
        @param x: float value
     """
     if not x >=0 :
         raise ValueError, "square root of a negative value "
     else:
         return math.sqrt(x)
def toLogX(x,y=None):
    """
        This function is used to load value on Plottable.View
        calculate log x
        @param x: float value
    """
    if not x > 0:
        raise ValueError, "Log(X)of a negative value "
    else:
        return math.log(x)
    
def toOneOverX(x,y=None):
    if x !=0:
        return 1/x
    else:
        raise ValueError,"cannot divide by zero"
def toOneOverSqrtX(x=None,y=None):
    if y!=None:
        if y > 0:
            return 1/math.sqrt(y)
        else:
            raise ValueError,"cannot be computed"
    if x!= None:
        if x > 0:
            return 1/math.sqrt(x)
        else:
            raise ValueError,"cannot be computed"
    
def toLogYX2(x,y):
    if y*(x**2) >0:
        return math.log(y*(x**2))
    else:
         raise ValueError,"cannot be computed"
     

def toLogYX4(x, y):
    if math.pow(x,4)*y > 0:
        return math.log(math.pow(x,4)*y)

def toLogXY(x,y):
    """
        This function is used to load value on Plottable.View
        calculate log x
        @param x: float value
    """
    if not x*y > 0:
        raise ValueError, "Log(X*Y)of a negative value "
    else:
        return math.log(x*y)



def errToX(x,y=None,dx=None,dy=None):
    """
        calculate error of x**2
        @param x: float value
        @param dx: float value
    """
    return dx


def errToX2(x,y=None,dx=None,dy=None):
    """
        calculate error of x**2
        @param x: float value
        @param dx: float value
    """
    if  dx != None:
        err = 2*x*dx
        if math.fabs(err) >= math.fabs(x):
            err = 0.9*x
        return math.fabs(err)
    else:
        return 0.0
def errFromX2(x,y=None,dx=None,dy=None):
    """
        calculate error of sqrt(x)
        @param x: float value
        @param dx: float value
    """
    if (x > 0):
        if(dx != None):
            err = dx/(2*math.sqrt(x))
        else:
            err = 0
        if math.fabs(err) >= math.fabs(x):
            err = 0.9*x    
    else:
        err = 0.9*x
       
        return math.fabs(err)
    
def errToLogX(x,y=None,dx=None,dy=None):
    """
        calculate error of Log(x)
        @param x: float value
        @param dx: float value
    """
    if dx==None:
        dx = 0
    if x!=0:
        dx = dx/x
    else:
        raise ValueError, "errToLogX: divide by zero"
    
    if math.fabs(dx) >= math.fabs(x):
        dx = 0.9*x
    
    return dx

def errToXY(x, y, dx=None, dy=None):
    if dx==None:
        dx=0
    if dy==None:
        dy=0
    err =math.sqrt((y*dx)**2 +(x*dy)**2)
    if err >= math.fabs(x):
        err =0.9*x
    return err 

def errToYX2(x, y, dx=None, dy=None):
    if dx==None:
        dx=0
    if dy==None:
        dy=0
    err =math.sqrt((2*x*y*dx)**2 +((x**2)*dy)**2)
    if err >= math.fabs(x):
        err =0.9*x
    return err 
    
def errToLogXY(x,y,dx=None, dy=None):
    """
        calculate error of Log(xy)
    """
    if (x!=0) and (y!=0):
        if dx == None:
            dx = 0
        if dy == None:
            dy = 0
        err = (dx/x)**2 + (dy/y)**2
        if  math.sqrt(math.fabs(err)) >= math.fabs(x):
            err= 0.9*x
    else:
        raise ValueError, "cannot compute this error"
   
    return math.sqrt(math.fabs(err))
    
def errToLogYX2(x,y,dx=None, dy=None):
    """
        calculate error of Log(yx**2)
    """
    if (x > 0) and (y > 0):
        if (dx == None):
            dx = 0
        if (dy == None):
            dy = 0
        err = (2*dx/x)**2 + (dy/y)**2
        if math.fabs(err) >= math.fabs(x):
            err =0.9*x
    else:
         raise ValueError, "cannot compute this error"
     
    return math.sqrt(math.fabs(err)) 
        
def errOneOverX(x,y=None,dx=None, dy=None):
    """
         calculate error on 1/x
    """
    if (x != 0):
        if dx ==None:
            dx= 0
        err = -(dx)**2/x**2
    else:
        raise ValueError,"Cannot compute this error"
    
    if math.fabs(err)>= math.fabs(x):
        err= 0.9*x
    return math.fabs(err)

def errOneOverSqrtX(x,y=None, dx=None,dy=None):
    """
        Calculate error on 1/sqrt(x)
    """
    if (x >0):
        if dx==None:
            dx =0
        err= -1/2*math.pow(x, -3/2)* dx
        if math.fabs(err)>= math.fabs(x):
            err=0.9*x
    else:
        raise ValueError, "Cannot compute this error"
    
    return math.fabs(err)
def errToLogYX4(x,y=None,dx=None,dy=None):
    """
        error for ln(y*x^(4))
        @param x: float value
    """
    if dx==None:
        dx=0
    if dy==None:
        dy=0
    err =math.sqrt((4*dx/x)**2 +(dy/y)**2)
    if err >= math.fabs(x):
        err =0.9*x
    return err 

           
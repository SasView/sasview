
import time
import sys

from data_util.calcthread import CalcThread
from DataLoader.loader import Loader
        

class DataReader(CalcThread):
    """
    Load a data given a filename
    """
    def __init__(self, path, err_fct, msg_fct, parent=None,
                 completefn=None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.path = path
        self.parent = parent
        self.err_fct = err_fct
        self.msg_fct = msg_fct
        #Instantiate a loader 
        self.loader = Loader()
        self.starttime = 0  
        
    def isquit(self):
        """
        :raise KeyboardInterrupt: when the thread is interrupted
        """
        try:
            CalcThread.isquit(self)
        except KeyboardInterrupt:
            raise KeyboardInterrupt   
        
        
    def compute(self):
        """
        read some data
        """
        self.starttime = time.time()
        try:
            output =  self.loader.load(self.path)
            elapsed = time.time() - self.starttime
            self.complete(output=output, parent=self.parent, path=self.path)
        except RuntimeError:
            self.err_fct()
            self.msg_fct(parent=self.parent)
            return
        except:
            self.msg_fct(parent=self.parent)
            
   
      
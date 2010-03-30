
import time
import sys


from data_util.calcthread import CalcThread
from DataLoader.loader import Loader
        

class DataReader(CalcThread):
    """
            Load a data given a filename
    """
    def __init__(self, path, filename='',completefn=None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.filename = filename
        self.path = path
        #Instantiate a loader 
        self.loader = Loader()
        self.starttime = 0  
        
    def isquit(self):
        """
             @raise KeyboardInterrupt: when the thread is interrupted
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
            data =  self.loader.load(self.path)
            elapsed = time.time() - self.starttime
            self.complete(data=data, filename=self.filename)
        except KeyboardInterrupt:
            # Thread was interrupted, just proceed and re-raise.
            # Real code should not print, but this is an example...
            raise
      
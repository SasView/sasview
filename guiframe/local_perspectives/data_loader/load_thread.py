
import time
import sys

from data_util.calcthread import CalcThread

        

class DataReader(CalcThread):
    """
    Load a data given a filename
    """
    def __init__(self, path, loader,
                 completefn=None,
                 updatefn   = None,
                 yieldtime  = 0.01,
                 worktime   = 0.01
                 ):
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.list_path = path
        #Instantiate a loader 
        self.loader = loader
        self.message = ""
        self.starttime = 0  
        self.updatefn = updatefn
        
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
        output = []
        error_message = ""
        for path in self.list_path:
            try:
                temp =  self.loader.load(path)
                elapsed = time.time() - self.starttime
                if temp.__class__.__name__ == "list":
                    output += temp
                else:
                    output.append(temp)
                message = "Loading ..." + str(path) + "\n"
                if self.updatefn is not None:
                    self.updatefn(output=output, message=message)
            except:
                error_message = "Error while loading: %s\n" % str(path)
                error_message += str(sys.exc_value) + "\n"
                self.updatefn(output=output, message=error_message)
                
        message = "Loading Complete!"
        self.complete(output=output, error_message=error_message,
                       message=message, path=self.list_path)
            
   
      
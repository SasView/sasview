# class Loader  to load any king of file
import wx
import string,numpy
class Reader:
    """
        This class is loading values from given file or value giving by the user
    """
    
    def _init_(self,filename=None,x=None,y=None,dx=None,dy=None):
        # variable to store loaded values
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.filename = filename
        
    def read(self,path, format=None):
        """ Store the values loaded from file in local variables 
            can read 3 columns of data
        """
        if not path == None:
            input_f =  open(path,'r')
            buff = input_f.read()
            lines = buff.split('\n')
            self.x=[]
            self.y=[]
            self.dx = [] 
            self.dy=[]
            value="can't read" 
            for line in lines:
                toks = line.split()
                try:  
                    x = float(toks[0])
                    y = float(toks[1]) 
                    dy = float(toks[2])
                   
                    self.x.append(x)
                    self.y.append(y)
                    self.dy.append(dy)
               
                except:
                    print "READ ERROR", line
        
                self.dx = numpy.zeros(len(self.x))
                # Sanity check
                if not len(self.x) == len(self.dx):
                    raise ValueError, "x and dx have different length"
                if not len(self.y) == len(self.dy):
                    raise ValueError, "y and dy have different length"
           
            if (self.x==[] or self.y==[])and (self.dy==[]):
                raise ValueError, "txtReader can't read"
            else:
                #msg="txtReader  Reading:\n"+"this x :"+ str(self.x) +"\n"+"this y:"+str(self.y)+"\n"+"this dy :"+str(self.dy)+"\n"
                #return msg
                print "TXT3_Reader reading: \n"
                return self.x,self.y,self.dy
                
  
if __name__ == "__main__": 
    read= Reader()
    #read= Reader(filename="testdata_line.txt")
    print read.load("test.dat")
    
    
            
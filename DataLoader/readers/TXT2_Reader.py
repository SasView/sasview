# class Loader  to load any king of file
import wx
import string,numpy
class Reader:
    """
        This class is loading values from given file or value giving by the user
        should be able to read only 2 columns of data
    """
    
    def _init_(self,x=None,y=None,dx=None,dy=None):
        # variable to store loaded values
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
    
    def read(self,path, format=None):
        """ Store the values loaded from file in local variables """
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
                    self.x.append(x)
                except:
                    print "READ ERROR", line
                try:
                    y = float(toks[1])
                    self.y.append(y)
                except:
                    print "READ ERROR", line
                try:
                    dy=float(toks[2])
                    self.dy.append(dy)

                except:
                    print "READ ERROR", line

            if(( self.x==[])or (self.y==[])) or (self.dy !=[]):
                print "went here"
                #return value
                raise ValueError, "Reader1 can't read"
            else:
                #msg="R1 reading: \n"+"this x :"+ str(self.x) +"\n"+"this y:"+str(self.y)+"\n"+"this dy :"+str(self.dy)+"\n"
                #return msg
                print "TXT2_Reader reading: \n"
                return self.x,self.y,self.dy
                
   
       
    
if __name__ == "__main__": 
    read= Reader()
    read.load("testdata_line.txt")
    
            
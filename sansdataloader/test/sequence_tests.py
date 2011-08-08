from DataLoader.loader import Loader
from DataLoader.readers.IgorReader import Reader as igor_reader
from DataLoader.readers.abs_reader import Reader as abs_reader


def consecutive_loader():
    out1 =  Loader().load("jan08002.ABS")
    out2 = Loader().load("MAR07232_rest.ASC")
    if len(out2.detector)>1:
        print "Consecutive reads using Loader failed"

def consecutive_reader():
    out1 = abs_reader().read("jan08002.ABS")
    out2 = igor_reader().read("MAR07232_rest.ASC")
    if len(out2.detector)>1:
        print "Consecutive reads using Readers failed"
        print out1
        print out2

def single_abs():
    out1 = abs_reader().read("jan08002.ABS")
    
def single_igor():
    out1 = igor_reader().read("MAR07232_rest.ASC")

if __name__ == "__main__": 
    #consecutive_loader()
    #consecutive_reader()
    single_igor()
    single_abs()
    print "Test passed"

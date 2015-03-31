"""
    SESANS reader (based on ASCII reader)
    
    Reader for .ses or .sesans file format
    
    Jurrian Bakker 
"""
import numpy
import os
from sas.dataloader.data_info import SESANSData1D

# Check whether we have a converter available
has_converter = True
try:
    from sas.data_util.nxsunit import Converter
except:
    has_converter = False
_ZERO = 1e-16

class Reader:
    """
    Class to load sesans files (6 columns).
    """
    ## File type
    type_name = "SESANS"
    
    ## Wildcards
    type = ["SESANS files (*.ses)|*.ses",
            "SESANS files (*..sesans)|*.sesans"]
    ## List of allowed extensions
    ext = ['.ses', '.SES', '.sesans', '.SESANS']
    
    ## Flag to bypass extension check
    allow_all = True
    
    def read(self, path):
        
#        print "reader triggered"
        
        """
        Load data file
        
        :param path: file path
        
        :return: SESANSData1D object, or None
        
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        if os.path.isfile(path):
            basename = os.path.basename(path)
            _, extension = os.path.splitext(basename)
            if self.allow_all or extension.lower() in self.ext:
                try:
                    # Read in binary mode since GRASP frequently has no-ascii
                    # characters that brakes the open operation
                    input_f = open(path,'rb')
                except:
                    raise  RuntimeError, "sesans_reader: cannot open %s" % path
                buff = input_f.read()
#                print buff
                lines = buff.splitlines()
#                print lines
                #Jae could not find python universal line spliter:
                #keep the below for now
                # some ascii data has \r line separator,
                # try it when the data is on only one long line
#                if len(lines) < 2 :
#                    lines = buff.split('\r')
                 
                x  = numpy.zeros(0)
                y  = numpy.zeros(0)
                dy = numpy.zeros(0)
                lam  = numpy.zeros(0)
                dlam = numpy.zeros(0)
                dx = numpy.zeros(0)
                
               #temp. space to sort data
                tx  = numpy.zeros(0)
                ty  = numpy.zeros(0)
                tdy = numpy.zeros(0)
                tlam  = numpy.zeros(0)
                tdlam = numpy.zeros(0)
                tdx = numpy.zeros(0)
#                print "all good"
                output = SESANSData1D(x=x, y=y, lam=lam, dy=dy, dx=dx, dlam=dlam)
#                print output                
                self.filename = output.filename = basename
                
                
                data_conv_z = None
                data_conv_P = None
#                print "passing"
                if has_converter == True and output.x_unit != 'A':
                    data_conv_z = Converter('nm')
                    # Test it
                    data_conv_z(1.0, output.x_unit)
#                    print data_conv_z
#                    print data_conv_z(1.0, output.x_unit)
                if has_converter == True and output.y_unit != ' ':
                    data_conv_P = Converter('a.u.')
                    # Test it
                    data_conv_P(1.0, output.y_unit)
#                    print data_conv_P
#                    print data_conv_P(1.0, output.y_unit)
                # The first good line of data will define whether
                # we have 2-column or 3-column ascii
#                print output.x_unit
#                print output.y_unit
                
#                print "past output"
                
#                has_error_dx = None
#                has_error_dy = None
                
#                #Initialize counters for data lines and header lines.
#                is_data = False  # Has more than 5 lines
#                # More than "5" lines of data is considered as actual
#                # data unless that is the only data
#                mum_data_lines = 5
#                # To count # of current data candidate lines
#                i = -1
#                # To count total # of previous data candidate lines
#                i1 = -1
#                # To count # of header lines
#                j = -1
#                # Helps to count # of header lines
#                j1 = -1
#                #minimum required number of columns of data; ( <= 4).
#                lentoks = 2
                paramnames=[]
                paramvals=[]
                zvals=[]
                dzvals=[]
                lamvals=[]
                dlamvals=[]
                Pvals=[]
                dPvals=[]
#                print x
#                print zvals
                for line in lines:
                    # Initial try for CSV (split on ,)
#                    print line
                    line=line.strip()
#                    print line
                    toks = line.split('\t')
#                    print toks
                    if len(toks)==2:
                        paramnames.append(toks[0])
#                        print paramnames
                        paramvals.append(toks[1])
#                        print paramvals
                    if len(toks)>5:
                        zvals.append(toks[0])
                        dzvals.append(toks[1])
                        lamvals.append(toks[2])
                        dlamvals.append(toks[3])
                        Pvals.append(toks[4])
                        dPvals.append(toks[5])
                    else:
                        continue
#                print varheaders
#                print paramnames
#                print paramvals
#                print zvals  
#                print len(zvals)
                
                x=[]
                y=[]
                lam=[]
                dx=[]
                dy=[]
                dlam=[]
                varheader=[zvals[0],dzvals[0],lamvals[0],dlamvals[0],Pvals[0],dPvals[0]]
#                print varheader
                valrange=range(len(zvals)-1)
#                print valrange
                for i in valrange:
                    x.append(float(zvals[i+1]))
                    y.append(float(Pvals[i+1]))
                    lam.append(float(lamvals[i+1]))
                    dy.append(float(dPvals[i+1]))
                    dx.append(float(dzvals[i+1]))
                    dlam.append(float(dlamvals[i+1]))
                    
                x,y,lam,dy,dx,dlam = [
                   numpy.asarray(v, 'double')
                   for v in (x,y,lam,dy,dx,dlam)
                ]

#                print x
#                print y
#                print dx
#                print dy
#                print len(x)
#                print len(y)
#                print len(dx)
#                print len(dy)
                
                
                input_f.close()
                # Sanity check
#                if has_error_dy == True and not len(y) == len(dy):
#                    msg = "sesans_reader: y and dy have different length"
#                    raise RuntimeError, msg
#                if has_error_dx == True and not len(x) == len(dx):
#                    msg = "sesans_reader: y and dy have different length"
#                    raise RuntimeError, msg
#                # If the data length is zero, consider this as
#                # though we were not able to read the file.
#                if len(x) == 0:
#                    raise RuntimeError, "sesans_reader: could not load file"
#                print "alive"
                #Let's re-order the data to make cal.
                # curve look better some cases
#                ind = numpy.lexsort((ty, tx))
#                for i in ind:
#                    x[i] = tx[ind[i]]
#                    y[i] = ty[ind[i]]
#                    if has_error_dy == True:
#                        dy[i] = tdy[ind[i]]
#                    if has_error_dx == True:
#                        dx[i] = tdx[ind[i]]
                # Zeros in dx, dy
#                if has_error_dx:
#                    dx[dx == 0] = _ZERO
#                if has_error_dy:
#                    dy[dy == 0] = _ZERO
                #Data
                output.x = x #[x != 0]
#                print output.x
                output.y = y #[x != 0]
#                print output.y
#                output.dy = dy[x != 0] if has_error_dy == True\
#                    else numpy.zeros(len(output.y))
#                output.dx = dx[x != 0] if has_error_dx == True\
#                    else numpy.zeros(len(output.x))
                output.dy = dy
                output.dx = dx
                output.lam = lam
                output.dlam = dlam


#                print "still alive"                
#                if data_conv_z is not None:
#                    output.xaxis("\\rm{z}", output.x_unit)
#                else:
#                    output.xaxis("\\rm{z}", 'nm')
#                if data_conv_P is not None:
#                    output.yaxis("\\rm{P/P0}", output.y_unit)
#                else:
#                    output.yaxis("\\rm{P/P0}", "a.u.")
                output.xaxis("\\rm{z}", 'nm')   
                output.yaxis("\\rm{P/P0}", " ")
                # Store loading process information
                output.meta_data['loader'] = self.type_name
                output.sample.thickness = float(paramvals[6])
                output.sample.name = paramvals[1]
                output.sample.ID = paramvals[0]
                output.sample.zacceptance=float(paramvals[7])
                output.vars=varheader

#                print "sesans_reader end"
                
                if len(output.x) < 1:
                    raise RuntimeError, "%s is empty" % path
#                print output
#                print output.lam
                return output
            
        else:
            raise RuntimeError, "%s is not a file" % path
        return None

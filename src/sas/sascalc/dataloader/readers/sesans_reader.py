"""
    SESANS reader (based on ASCII reader)
    
    Reader for .ses or .sesans file format
    
    Jurrian Bakker 
"""
import numpy
import os
from sas.sascalc.dataloader.data_info import SESANSData1D

# Check whether we have a converter available
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
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
                    line=line.strip()
                    toks = line.split('\t')
                    if len(toks)==2:
                        paramnames.append(toks[0])
                        paramvals.append(toks[1])
                    if len(toks)>5:
                        zvals.append(toks[0])
                        dzvals.append(toks[1])
                        lamvals.append(toks[2])
                        dlamvals.append(toks[3])
                        Pvals.append(toks[4])
                        dPvals.append(toks[5])
                    else:
                        continue

                x=[]
                y=[]
                lam=[]
                dx=[]
                dy=[]
                dlam=[]
                lam_header = lamvals[0].split()
                data_conv_z = None
                default_z_unit = "A"
                data_conv_P = None
                default_p_unit = " "
                lam_unit = lam_header[1].replace("[","").replace("]","")
                for i,x_val in output.x:
                    output.x[i], output.x_unit = self._unit_conversion(x_val, lam_unit, default_z_unit)
                for i,y_val in output.y:
                    output.y[i], output.y_unit = self._unit_conversion(y_val, " ", default_p_unit)
                varheader=[zvals[0],dzvals[0],lamvals[0],dlamvals[0],Pvals[0],dPvals[0]]
                valrange=range(1, len(zvals))
                for i in valrange:
                    x.append(float(zvals[i]))
                    y.append(float(Pvals[i]))
                    lam.append(float(lamvals[i]))
                    dy.append(float(dPvals[i]))
                    dx.append(float(dzvals[i]))
                    dlam.append(float(dlamvals[i]))

                x,y,lam,dy,dx,dlam = [
                   numpy.asarray(v, 'double')
                   for v in (x,y,lam,dy,dx,dlam)
                ]

                input_f.close()

                #Data
                output.x = x #[x != 0]
                output.y = y #[x != 0]
                output.dy = dy
                output.dx = dx
                output.lam = lam
                output.dlam = dlam

                output.xaxis("\rm{z}", output.x_unit)
                output.yaxis("\\rm{P/P0}", output.y_unit)
                # Store loading process information
                output.meta_data['loader'] = self.type_name
                output.sample.thickness = float(paramvals[6])
                output.sample.name = paramvals[1]
                output.sample.ID = paramvals[0]
                output.sample.zacceptance=float(paramvals[7])
                output.vars=varheader

                if len(output.x) < 1:
                    raise RuntimeError, "%s is empty" % path
                return output

        else:
            raise RuntimeError, "%s is not a file" % path
        return None

    def _unit_conversion(self, value, value_unit, default_unit):
        if has_converter == True and value_unit != default_unit:
            data_conv_q = Converter(value_unit)
            value = data_conv_q(value, units=default_unit)
            new_unit = default_unit
        else:
            new_unit = value_unit
        return value, new_unit
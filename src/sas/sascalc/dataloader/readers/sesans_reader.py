"""
    SESANS reader (based on ASCII reader)
    
    Reader for .ses or .sesans file format
    
    Jurrian Bakker 
"""
import numpy as np
import os
from sas.sascalc.dataloader.data_info import Data1D

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
                lines = buff.splitlines()
                x  = np.zeros(0)
                y  = np.zeros(0)
                dy = np.zeros(0)
                lam  = np.zeros(0)
                dlam = np.zeros(0)
                dx = np.zeros(0)
                
               #temp. space to sort data
                tx  = np.zeros(0)
                ty  = np.zeros(0)
                tdy = np.zeros(0)
                tlam  = np.zeros(0)
                tdlam = np.zeros(0)
                tdx = np.zeros(0)
                output = Data1D(x=x, y=y, lam=lam, dy=dy, dx=dx, dlam=dlam, isSesans=True)
                self.filename = output.filename = basename

                paramnames=[]
                paramvals=[]
                zvals=[]
                dzvals=[]
                lamvals=[]
                dlamvals=[]
                Pvals=[]
                dPvals=[]

                for line in lines:
                    # Initial try for CSV (split on ,)
                    line=line.strip()
                    toks = line.split('\t')
                    if len(toks)==2:
                        paramnames.append(toks[0])
                        paramvals.append(toks[1])
                    if len(toks)>5:
                        zvals.append(toks[0])
                        dzvals.append(toks[3])
                        lamvals.append(toks[4])
                        dlamvals.append(toks[5])
                        Pvals.append(toks[1])
                        dPvals.append(toks[2])
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
                default_p_unit = " " # Adjust unit for axis (L^-3)
                lam_unit = lam_header[1].replace("[","").replace("]","")
                if lam_unit == 'AA':
                    lam_unit = 'A'
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
                    np.asarray(v, 'double')
                   for v in (x,y,lam,dy,dx,dlam)
                ]

                input_f.close()

                output.x, output.x_unit = self._unit_conversion(x, lam_unit, default_z_unit)
                output.y = y
                output.y_unit = r'\AA^{-2} cm^{-1}'  # output y_unit added
                output.dx, output.dx_unit = self._unit_conversion(dx, lam_unit, default_z_unit)
                output.dy = dy
                output.lam, output.lam_unit = self._unit_conversion(lam, lam_unit, default_z_unit)
                output.dlam, output.dlam_unit = self._unit_conversion(dlam, lam_unit, default_z_unit)
                
                output.xaxis(r"\rm{z}", output.x_unit)
                output.yaxis(r"\rm{ln(P)/(t \lambda^2)}", output.y_unit)  # Adjust label to ln P/(lam^2 t), remove lam column refs

                # Store loading process information
                output.meta_data['loader'] = self.type_name
                #output.sample.thickness = float(paramvals[6])
                output.sample.name = paramvals[1]
                output.sample.ID = paramvals[0]
                zaccept_unit_split = paramnames[7].split("[")
                zaccept_unit = zaccept_unit_split[1].replace("]","")
                if zaccept_unit.strip() == r'\AA^-1' or zaccept_unit.strip() == r'\A^-1':
                    zaccept_unit = "1/A"
                output.sample.zacceptance=(float(paramvals[7]),zaccept_unit)
                output.vars = varheader

                if len(output.x) < 1:
                    raise RuntimeError, "%s is empty" % path
                return output

        else:
            raise RuntimeError, "%s is not a file" % path
        return None

    def _unit_conversion(self, value, value_unit, default_unit):
        if has_converter and value_unit != default_unit:
            data_conv_q = Converter(value_unit)
            value = data_conv_q(value, units=default_unit)
            new_unit = default_unit
        else:
            new_unit = value_unit
        return value, new_unit
#####################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#See the license text in license.txt
#copyright 2012, University of Tennessee
######################################################################
"""
    Nexus reader for 2D data reduced by Mantid
"""
import os
from sans.dataloader.data_info import Data2D


class Reader:
    """
        Nexus reader for 2D data reduced by Mantid
    """
    ## File type
    type_name = "NXS"
    ## Wildcards
    type = ["Nexus files (*.nxs)|*.nxs"]
    ## Extension
    ext = ['.nxs']
        
    def read(self, filename=None):
        """
            Open and read the data in a file
        
            :param filename: path of the file
        """
        try:
            import nxs
        except:
            msg = "Error reading Nexus file: Nexus package is missing.\n"
            msg += "  Get it from http://http://www.nexusformat.org/"
            raise RuntimeError, msg
        
        # Instantiate data object
        output = Data2D()
        output.filename = os.path.basename(filename)

        fd = nxs.open(filename, 'rw')
        
        # Read in the 2D data
        fd.opengroup('mantid_workspace_1')
        fd.opengroup('workspace')
        fd.opendata('values')
        output.data = fd.getdata().copy()
        fd.closedata()
        
        # Read in the errors
        fd.opendata('errors')
        output.err_data = fd.getdata().copy()
        fd.closedata()
        
        # Read in the values on each axis
        fd.opendata('axis1')
        output.x_bins = fd.getdata().copy()
        fd.closedata()
        
        fd.opendata('axis2')
        output.y_bins = fd.getdata().copy()
        fd.closedata()
        fd.closegroup()
                
        output.xmin = min(output.x_bins)
        output.xmax = max(output.x_bins)
        output.ymin = min(output.y_bins)
        output.ymax = max(output.y_bins)
        
        output.xaxis("\\rm{Q_{x}}", 'A^{-1}')
        output.yaxis("\\rm{Q_{y}}", 'A^{-1}')
        output.zaxis("\\rm{Intensity}", "cm^{-1}")

        # Meta data
        fd.opendata('title')
        output.title = fd.getdata()
        fd.closedata()
        
        fd.opengroup('instrument')
        fd.opendata('name')
        output.instrument = fd.getdata()
        fd.closedata()
        fd.closegroup()

        fd.opengroup('logs')
        fd.opengroup('run_number')
        fd.opendata('value')
        output.run = fd.getdata()

        fd.close()

        # Store loading process information
        output.meta_data['loader'] = self.type_name
        return output

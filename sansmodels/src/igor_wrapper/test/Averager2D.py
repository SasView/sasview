"""
    Class to average an oriented model
    Options:
        - flat average in one or both coordinates (specified)
        - given distribution in one or both coordinates (specified)
        
    Uses DisperseModel to allow for polydispersity
"""

from sans.models.BaseComponent import BaseComponent
import copy, os, math
    
class Averager2D(BaseComponent):
    

    def __init__(self):
        BaseComponent.__init__(self)
        self.params = {}
        self.model      = None
        self.dispersed  = None
        self.phi_file   = None
        self.theta_file = None
        self.phi_name   = None
        self.theta_name = None
        self.phi_on     = False
        self.theta_on   = False
        
        self.phi_data   = None
        self.theta_data = None
        self.dispersion = []
        self.runXY      = self.run_oriented
        self.run        = self.run_oriented
        self.disp_model_run = None
        self.details    = None

    def __str__(self):
        info  = "%s (%s)\n" % (self.name, self.model.__class__.__name__)
        info += "Pars: %s\n" % self.model.params
        info += "Disp: %s\n" % self.dispersion
        info += "Disp: %s\n" % self.dispersed.params
        return info

    def clone(self):
        obj            = Averager2D()
        obj.params     = copy.deepcopy(self.params)
        obj.details    = copy.deepcopy(self.details)
        obj.model      = self.model.clone()
        obj.phi_file   = copy.deepcopy(self.phi_file)
        obj.theta_file = copy.deepcopy(self.theta_file)
        obj.phi_name   = copy.deepcopy(self.phi_name)
        obj.theta_name = copy.deepcopy(self.theta_name)
        obj.name       = copy.deepcopy(self.name)
        obj.phi_on = self.phi_on
        obj.theta_on = self.theta_on
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.update_functor()
        return obj   

    def set_model(self, model):
        self.name = model.name
        self.model = model
        self.params = model.params
        self.details = model.details
        retval = self._find_angles()
        self.update_functor()
        self.disp_model_run = self.model.runXY
        return retval
        
    def setParam(self, name, value):
        # Keep a local copy for badly implemented code
        # that access params directly
        #TODO: fix that!
        if name.lower() in self.params:
            self.params[name.lower()] = value
        return self.model.setParam(name, value)
        
    def getParam(self, name):
        return self.model.getParam(name)

    def _find_angles(self):
        """
            Find which model parameters represent
            theta and phi
            @return: True if at least one angle was found
        """
        self.theta_name = None
        self.phi_name   = None
        for item in self.model.params:
            if item.lower().count("theta")>0:
                self.theta_name = item
            elif item.lower().count("phi")>0:
                self.phi_name = item
                
        if self.theta_name == None and self.phi_name == None:
            return False
        return True
        
    def setPhiFile(self, path):
        """
            Check the validity of a path and store it
            @param path: file path
            @return: True if all OK, False if can't be set
        """
        
        # If it's the same file, do nothing
        if self.phi_file == path:
            return True
        
        if path==None or self.phi_name == None:
            self.phi_file = None
            self.phi_data = None
            self.phi_on   = False
            self.update_functor()
        elif os.path.isfile(path):
            self.phi_file = path
            #self.phi_data = self.read_file(path)
            self.phi_on = True
            self.update_functor()
        else:
            raise ValueError, "%s is not a file" % path
        
        if self.phi_name == None:
            return False
        else:
            return True

    def read_file(self, path):
        input_f = open(path, 'r')
        buff = input_f.read()
        lines = buff.split('\n')
        
        angles = []
        
        for line in lines:
            toks = line.split()
            if len(toks)==2:
                try:
                    angle = float(toks[0])
                    weight = float(toks[1])
                except:
                    # Skip non-data lines
                    pass
                angles.append([angle, weight])
        return angles
                

    def setThetaFile(self, path):
        """
            Check the validity of a path and store it
            @param path: file path
            @return: True if all OK, False if can't be set
        """
        
        # If it's the same file, do nothing
        if self.theta_file == path:
            return True
        
        if path==None or self.theta_name == None:
            self.theta_file = None
            self.theta_data = None
            self.theta_on   = False
            self.update_functor()
        elif os.path.isfile(path):
            self.theta_file = path
            #self.theta_data = self.read_file(path)
            self.theta_on = True
            self.update_functor()
        else:
            raise ValueError, "%s is not a file" % path

        if self.theta_name == None:
            return False
        else:
            return True

    def update_functor(self):
        # Protect against empty model
        if self.model==None:
            return
        
        self.set_dispersity(self.dispersion)
        #phi_points = [[self.model.getParam(self.phi_name), 1.0]]
        #theta_points = [[self.model.getParam(self.theta_name), 1.0]]
        
       # Initialize theta points to visit
        if self.theta_on:
            # Check whether we have the data
            if not self.theta_file == None and self.theta_data == None:
                self.theta_data = self.read_file(self.theta_file)
            elif not self.model == None:
                self.theta_data = [[self.model.getParam(self.phi_name), 1.0]]
            else:
                self.theta_data = []
            
        # Initialize phi points to visit
        if self.phi_on:
            # Check whether we have the data
            if not self.phi_file == None and self.phi_data == None:
                self.phi_data = self.read_file(self.phi_file)
            elif not self.model == None:
                self.phi_data = [[self.model.getParam(self.theta_name), 1.0]]
            else:
                self.phi_data = []
                
        if self.phi_on and self.theta_on:
            self.runXY = self.run_theta_phi
        elif not self.phi_on and self.theta_on:
            self.runXY = self.run_theta
        elif not self.theta_on and self.phi_on:
            self.runXY = self.run_phi
        else:
            self.runXY = self.run_oriented
                
    def get_dispersity(self):
        return self.dispersion
    
    def set_dispersity(self, disp):
        from sans.models.DisperseModel import DisperseModel
        
        if len(disp) == 0 and len(self.dispersion) == 0:
            self.disp_model_run = self.model.runXY
            return False
        
        self.dispersion = disp
        if len(self.dispersion)==0:
            self.disp_model_run = self.model.runXY
            self.dispersed = None
            
            return True
        
        
        name_list = []
        val_list  = []
        npts = 0
        for item in disp:
            name_list.append(item[0])
            val_list.append(item[1])
            # For now, us largest
            if item[2]>npts:
                npts = item[2]
            
        self.dispersed = DisperseModel(self.model, name_list, val_list)
        self.dispersed.setParam('n_pts', npts)
        self.disp_model_run = self.dispersed.runXY
        
        return True
                
    def run_oriented(self, x=0):
        return self.disp_model_run(x)
    
    def run_phi(self, x=0):
        sum  = 0
        norm = 0
        background = 0
        
        # If we have a background, perform the average
        # only with bck=0 and add it at the end
        if "background" in self.model.getParamList():
            background = self.model.getParam('background')
            self.model.setParam('background', 0.0)

        for ph_i in self.phi_data:
            self.model.setParam(self.phi_name, ph_i[0])
            sum += self.disp_model_run(x) * ph_i[1]
            norm += ph_i[1]
                
        # Restore original background value
        if "background" in self.model.getParamList():
            self.model.setParam('background', background)

        return sum / norm + background
    
    def run_theta(self, x=0):
        sum  = 0
        norm = 0
        background = 0
        
        # If we have a background, perform the average
        # only with bck=0 and add it at the end
        if "background" in self.model.getParamList():
            background = self.model.getParam('background')
            self.model.setParam('background', 0.0)
            
        for th_i in self.theta_data:
            self.model.setParam(self.theta_name, th_i[0])
            sum += self.disp_model_run(x) * math.sin(th_i[0]) * th_i[1]
            norm += th_i[1]
                
        # Restore original background value
        if "background" in self.model.getParamList():
            self.model.setParam('background', background)

        return sum / norm + background
    
    def run_theta_phi(self, x=0):
        sum  = 0
        norm = 0
        background = 0
        
        # If we have a background, perform the average
        # only with bck=0 and add it at the end
        if "background" in self.model.getParamList():
            background = self.model.getParam('background')
            self.model.setParam('background', 0.0)

        for th_i in self.theta_data:
            self.model.setParam(self.theta_name, th_i[0])
            
            for ph_i in self.phi_data:
                self.model.setParam(self.phi_name, ph_i[0])
                sum += self.disp_model_run(x) * math.sin(th_i[0]) * ph_i[1] * th_i[1]
                norm += ph_i[1] * th_i[1]
        
        # Restore original background value
        if "background" in self.model.getParamList():
            self.model.setParam('background', background)
       
        return sum / norm + background       

    
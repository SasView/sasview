"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import sans.realspace.VolumeCanvas as VolumeCanvas

class ShapeVisitor:
    """
        The shape visitor process a GUI object representing 
        a shape and returns a shape description that can be
        processed by the VolumeCanvas.
    """
    
    def __init__(self):
        """
            Initialize visitor
        """
        ## Place holder for the simulation canvas
        self.sim_canvas = None
    
    def fromCylinder(self, cyl):
        """
            Create a simulation cylinder descriptor (computation) 
            from the information produced by the GUI
            @param cyl: Cylinder object from the GUI canvas 
            @return: VolumeCanvas.CylinderDescriptor object
        """
        from sans.realspace.VolumeCanvas import CylinderDescriptor
        desc = CylinderDescriptor()
         
        desc.params["center"] = [cyl.x, cyl.y, cyl.z]
        # Orientation are angular offsets in degrees with respect to X, Y, Z
        desc.params["orientation"] = [cyl.theta_x, cyl.theta_y, cyl.theta_z]
        desc.params["order"] = cyl.params["order"]
        
        
        # Length of the cylinder
        desc.params["length"] = cyl.params["length"]
        # Radius of the cylinder
        desc.params["radius"] = cyl.params["radius"]
        # Constrast parameter
        desc.params["contrast"] = cyl.params["contrast"]
        
        return desc
    
    def fromSphere(self, sph):
        """
            Create a simulation sphere descriptor (computation) 
            from the information produced by the GUI
            @param sph: Sphere object from the GUI canvas 
            @return: VolumeCanvas.SphereDescriptor object
        """
        from sans.realspace.VolumeCanvas import SphereDescriptor
        desc = SphereDescriptor()
         
        desc.params["center"] = [sph.x, sph.y, sph.z]
        desc.params["order"] = sph.params["order"]
        # Radius of the sphere
        desc.params["radius"] = sph.params["radius"]
        # Constrast parameter
        desc.params["contrast"] = sph.params["contrast"]
        
        return desc
    
    def update_sphere(self, sph):
        """
            Update a shape description in the simulation canvas (computation)
            according to the new parameters of the GUI canvas.
            @param sph: Sphere object from the GUI canvas 
        """
        # Check class
        if self.sim_canvas.shapes[sph.name].__class__.__name__=="SphereDescriptor":
            desc = self.sim_canvas.shapes[sph.name]
            
            desc.params["center"] = [sph.x, sph.y, sph.z]
            desc.params["order"] = sph.params["order"]
            # Radius of the sphere
            desc.params["radius"] = sph.params["radius"]
            # Constrast parameter
            desc.params["contrast"] = sph.params["contrast"]
            
            self.sim_canvas._model_changed()
        else:
            raise ValueError, "SimShapeVisitor: Wrong class for visited object"
        
        
        
    def update_cylinder(self, cyl):
        """
            Update a shape description in the simulation canvas (computation)
            according to the new parameters of the GUI canvas.
            @param cyl: Cylinder object from the GUI canvas 
        """
        # Check class
        if self.sim_canvas.shapes[cyl.name].__class__.__name__=="CylinderDescriptor":
            desc = self.sim_canvas.shapes[cyl.name]
            
            desc.params["center"] = [cyl.x, cyl.y, cyl.z]
            # Orientation are angular offsets in degrees with respect to X, Y, Z
            desc.params["orientation"] = [cyl.theta_x, cyl.theta_y, cyl.theta_z]
            desc.params["order"] = cyl.params["order"]
            
            # Length of the cylinder
            desc.params["length"] = cyl.params["length"]
            # Radius of the cylinder
            desc.params["radius"] = cyl.params["radius"]
            # Constrast parameter
            desc.params["contrast"] = cyl.params["contrast"]
            
            self.sim_canvas._model_changed()
        else:
            raise ValueError, "SimShapeVisitor: Wrong class for visited object"
        
    
    def update(self, volCanvas, shape):
        """
            Update the shape descriptor in the VolumeCanvas
            corresponding to the given 'shape' parameter
            
            @param volCanvas: VolumeCanvas object
            @param shape: SimCanvas.BaseShape object
        """
        if shape.name in volCanvas.getShapeList():
            self.sim_canvas = volCanvas
            shape.accept_update(self)
        else:
            raise ValueError, "ShapeAdapter: Shape [%s] not in list" % shape.name


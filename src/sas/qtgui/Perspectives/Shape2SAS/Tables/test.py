from enum import Enum
class ExtendedEnum(Enum):
    """Extended Enum class to return all values"""

    #return all values in a list
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class OptionLayout(ExtendedEnum):
    """Option layout for the subunit table"""
    Subunit = 0
    ΔSLD = 1
    x = 2
    y = 3
    z = 4
    COM_x = 5
    COM_y = 6
    COM_z = 7
    RP_x = 8
    RP_y = 9
    RP_z = 10
    α = 11
    β = 12
    γ = 13
    Colour = 14


    def sphere(self):
        """sphere dimension layout"""
        dimensions = [self.x.value]
        name = ["R"]
        units = ["Å"]
        tooltip = ["Radius of the sphere"]  
        default_value = [50.0]

        return dimensions, name, default_value, units, tooltip


    def ellipsoid(self):
        """ellipsoid dimension layout"""
        dimensions = [self.x.value, self.y.value, self.z.value]
        name = ["a", "b", "c"]
        units = ["Å", "Å", "Å"]
        tooltip = ["Semi-axis a of the ellipsoid along the x-axis",
                   "Semi-axis b of the ellipsoid along the y-axis",
                   "Semi-axis c of the ellipsoid along the z-axis"]
        default_value = [50.0, 50.0, 200.0]

        return dimensions, name, default_value, units, tooltip
    

    def cylinder(self):
        """Return the cylinder dimensions"""
        dimensions = [self.x.value, self.y.value]
        name = ["R", "l"]
        units = ["Å", "Å"]
        tooltip = ["Radius of the cylinder", 
                   "Length of the cylinder"]
        default_value = [50.0, 50.0]

        return dimensions, name, default_value, units, tooltip
    
    def elliptical_cylinder(self):
        """Return the elliptical cylinder dimensions"""
        dimensions = [self.x.value, self.y.value, self.z.value]
        name = ["a", "b", "l"]
        units = ["Å", "Å", "Å"]
        tooltip = ["Semi-axis a of the elliptical cylinder along the x-axis",
                   "Semi-axis b of the elliptical cylinder along the y-axis",
                   "Length l of the elliptical cylinder along the z-axis"]
        default_value = [50.0, 50.0, 200.0]

        return dimensions, name, default_value, units, tooltip

    #more methods for other shapes

    def SLD(self):
        """Return ΔSLD dimensions"""
        dimensions = self.ΔSLD.value
        name = "ΔSLD"
        units = ""
        tooltip = "Contrast"
        default_value = 1.0

        return dimensions, name, default_value, units, tooltip

    def COMX(self):
        """Return COMX dimensions"""
        dimensions = self.COM_x.value
        name = "COMX"
        units = "Å"
        tooltip = "x-axis position of center of mass"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def COMY(self):
        """Return COMY dimensions"""
        dimensions = self.COM_y.value
        name = "COMY"
        units = "Å"
        tooltip = "y-axis position of center of mass"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def COMZ(self):
        """Return COMZ dimensions"""
        dimensions = self.COM_z.value
        name = "COMZ"
        units = "Å"
        tooltip = "z-axis position of center of mass"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def RPX(self):
        """Return RPX dimensions"""
        dimensions = self.RP_x.value
        name = "RPX"
        units = "Å"
        tooltip = "x-axis position of rotation point"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def RPY(self):
        """Return RPY dimensions"""
        dimensions = self.RP_y.value
        name = "RPY"
        units = "Å"
        tooltip = "y-axis position of rotation point"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def RPZ(self):
        """Return RPZ dimensions"""
        dimensions = self.RP_z.value
        name = "RPZ"
        units = "Å"
        tooltip = "z-axis position of rotation point"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def alpha(self):
        """Return α dimensions"""
        dimensions = self.α.value
        name = "α"
        units = "°"
        tooltip = "Angle around x-axis"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def beta(self):
        """Return β dimensions"""
        dimensions = self.β.value
        name = "β"
        units = "°"
        tooltip = "Angle around y-axis"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def gamma(self):
        """Return γ dimensions"""
        dimensions = self.γ.value
        name = "γ"
        units = "°"
        tooltip = "Angle around z-axis"
        default_value = 0.0

        return dimensions, name, default_value, units, tooltip
    
    def colour(self):
        """Return Colour dimensions"""
        dimensions = self.Colour.value
        name = "Colour"
        units = ""
        tooltip = "Colour to represent the subunit"
        default_value = "Green"

        return dimensions, name, default_value, units, tooltip


    def methods(self):
        """all available methods"""
        self.available_methods = {
            self.ΔSLD.value: self.SLD,
            self.COM_x.value: self.COMX,
            self.COM_y.value: self.COMY,
            self.COM_z.value: self.COMZ,
            self.RP_x.value: self.RPX,
            self.RP_y.value: self.RPY,
            self.RP_z.value: self.RPZ,
            self.α.value: self.alpha,
            self.β.value: self.beta,
            self.γ.value: self.gamma,
            self.Colour.value: self.colour
        }


    def AllColumnInfo(self, method: callable) -> tuple[list, list, list, list, list]:
        """Return all info from a column given a method"""
        dimensions, name, default_value, units, tooltip = method()

        allTooltip = []
        allUnits =  []
        allDefault = []
        names = []
        Layout = []

        for layout in OptionLayout.list():
            if layout in self.available_methods:
                dimensions, name, default_value, units, tooltip = self.available_methods[layout]()
                allTooltip.append(tooltip)
                allUnits.append(units)
                allDefault.append(default_value)
                names.append(name)
                Layout.append(dimensions)
            
        
        for layout in range(len(dimensions)):
            allTooltip.insert(dimensions[layout], tooltip[layout])
            allUnits.insert(dimensions[layout], units[layout])
            allDefault.insert(dimensions[layout], default_value[layout])
            names.insert(dimensions[layout], name[layout])
            Layout.insert(dimensions[layout], dimensions[layout])


        return Layout, names, allDefault, allUnits, allTooltip


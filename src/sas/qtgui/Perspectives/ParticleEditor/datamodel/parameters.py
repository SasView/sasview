class Parameter:
    is_function_parameter = False

    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value


class FunctionParameter(Parameter):
    """ Representation of an input parameter to the sld"""
    is_function_parameter = True


class SolventSLD(Parameter):
    """ Parameter representing the solvent SLD, always present"""
    def __init__(self):
        super().__init__("Solvent SLD", 0.0)


class Background(Parameter):
    """ Parameter representing the background intensity, always present"""
    def __init__(self):
        super().__init__("Background Intensity", 0.0001)


class Scale(Parameter):
    """ Parameter representing the scaling, always present"""
    def __init__(self):
        super().__init__("Intensity Scaling", 1.0)




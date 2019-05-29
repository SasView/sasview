class Constraint(object):
    """
    Internal representation of a single parameter constraint
    Currently just a data structure, might get expaned with more functionality,
    hence made into a class.
    """
    def __init__(self, parent=None, param=None, value=0.0,
                 min=None, max=None, func=None, value_ex=None,
                 operator="="):
        self._value = value
        self._param = param
        self._value_ex = value_ex
        self._func = func
        self._min = min
        self._max = max
        self._operator = operator
        self.validate = True
        self.active = True

    @property
    def value(self):
        # value/parameter to fit to (e.g. 1.0 or sld)
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @property
    def value_ex(self):
        # full parameter name to fit to (e.g. M1.sld)
        return self._value_ex

    @value_ex.setter
    def value_ex(self, val):
        self._value_ex = val

    @property
    def param(self):
        # parameter which is being fitted
        return self._param

    @param.setter
    def param(self, val):
        self._param = val

    @property
    def func(self):
        # Function to be used for constraint
        # e.g. sqrt(M1.sld+1.0)
        return self._func

    @func.setter
    def func(self, val):
        self._func = val

    @property
    def min(self):
        # min param value for single value constraints
        return self._min

    @min.setter
    def min(self, val):
        self._min = val

    @property
    def max(self):
        # max param value for single value constraints
        return self._max

    @max.setter
    def max(self, val):
        self._max = val

    @property
    def operator(self):
        # operator to use for constraint
        return self._operator

    @operator.setter
    def operator(self, val):
        self._operator = val


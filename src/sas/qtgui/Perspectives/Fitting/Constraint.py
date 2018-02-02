class Constraint(object):
    """
    Internal representation of a single parameter constraint
    Currently just a data structure, might get expaned with more functionality,
    hence made into a class.
    """
    def __init__(self, parent=None, param=None, value=0.0, min=None, max=None, func=None):
        self._value = value
        self._param = param
        self._func = func
        self.active = True
        self._min = min
        self._max = max

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @property
    def param(self):
        return self._param

    @param.setter
    def param(self, val):
        self._param = val

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, val):
        self._func = val

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, val):
        self._min = val

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, val):
        self._max = val


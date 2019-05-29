#!/usr/bin/env python
"""
Provide Line function (y= Ax + B). Until July 10, 2016 this function provided
(y= A + Bx).  This however was contrary to all the other code using it which 
assumed (y= mx+b) or in this nomenclature (y=Ax + B). This lead to some
contortions in the code and worse incorrect calculations until now for at least
some of the functions.  This seemed the easiest to fix particularly since this
function should disappear in a future iteration (see notes in fitDialog)

                -PDB   July 10, 2016
"""

import math

class LineModel(object):
    """
    Class that evaluates a linear model.

    f(x) = Ax + B

    List of default parameters:
    A = 1.0
    B = 1.0
    """

    def __init__(self):
        """ Initialization """
        # # Name of the model
        self.name = "LineModel"

        # # Define parameters
        self.params = {}
        self.params['A'] = 1.0
        self.params['B'] = 1.0

        # # Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', None, None]
        self.details['B'] = ['', None, None]

    def getParam(self, name):
        """
            Return parameter value
        """
        return self.params[name.upper()]

    def setParam(self, name, value):
        """
            Set parameter value
        """
        self.params[name.upper()] = value

    def _line(self, x):
        """
        Evaluate the function

        :param x: x-value

        :return: function value

        """
        return  (self.params['A'] * x) + self.params['B']

    def run(self, x=0.0):
        """
        Evaluate the model

        :note: This is the function called by fitDialog to calculate the
        the y(xmin) and y(xmax), but the only difference between this and
        runXY is when the if statement is true. I however cannot see what that
        function is for.  It needs to be documented here or removed.
        -PDB 7/10/16 

        :param x: simple value

        :return: (Line value)
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0] * math.cos(x[1])) * \
                                self._line(x[0] * math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            msg = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError(msg)
        else:
            return self._line(x)

    def runXY(self, x=0.0):
        """
        Evaluate the model.
        
        :note: This is to be what is called by fitDialog for the actual fit
        but the only difference between this and run is when the if 
        statement is true. I however cannot see what that function
        is for.  It needs to be documented here or removed. -PDB 7/10/16 

        :param x: simple value

        :return: Line value

        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0]) * self._line(x[1])
        elif x.__class__.__name__ == 'tuple':
            msg = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError(msg)
        else:
            return self._line(x)


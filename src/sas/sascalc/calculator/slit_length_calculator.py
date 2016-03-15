"""
This module is a small tool to allow user to quickly
determine the slit length value of data.
"""


class SlitlengthCalculator(object):
    """
    compute slit length from SAXSess beam profile (1st col. Q , 2nd col. I ,
    and 3rd col. dI.: don't need the 3rd)
    """
    def __init__(self):

        # x data
        self.x = None
        # y data
        self.y = None
        #default slit length
        self.slit_length = 0.0

        # The unit is unknown from SAXSess profile:
        # It seems 1/nm but it could be not fixed,
        # so users should be notified to determine the unit by themselves.
        self.slit_length_unit = "unknown"

    def set_data(self, x=None, y=None):
        """
         Receive two vector x, y and prepare the slit calculator for
         computation.

        :param x: array
        :param y: array
        """
        self.x = x
        self.y = y

    def calculate_slit_length(self):
        """
        Calculate slit length.

        :return: the slit length calculated value.
        """
        # None data do nothing
        if self.y == None or self.x == None:
            return
        # set local variable
        y = self.y
        x = self.x

        # find max y
        max_y = y.max()

        # initial values
        y_sum = 0.0
        y_max = 0.0
        ind = 0.0

        # sum 10 or more y values until getting max_y,
        while True:
            if ind >= 10 and y_max == max_y:
                break
            y_sum = y_sum + y[ind]
            if y[ind] > y_max:
                y_max = y[ind]
            ind += 1

        # find the average value/2 of the top values
        y_half = y_sum/(2.0*ind)

        # defaults
        y_half_d = 0.0
        ind = 0.0
        # find indices where it crosses y = y_half.
        while True:
            # no need to check when ind == 0
            ind += 1
            # y value and ind just after passed the spot of the half height
            y_half_d = y[ind]
            if y[ind] < y_half:
                break

        # y value and ind just before passed the spot of the half height
        y_half_u = y[ind-1]

        # get corresponding x values
        x_half_d = x[ind]
        x_half_u = x[ind-1]

        # calculate x at y = y_half using linear interpolation
        if y_half_u == y_half_d:
            x_half = (x_half_d + x_half_u)/2.0
        else:
            x_half = (x_half_u * (y_half - y_half_d)  \
                       + x_half_d * (y_half_u - y_half)) \
                        / (y_half_u - y_half_d)

        # Our slit length is half width, so just give half beam value
        slit_length = x_half

        # set slit_length
        self.slit_length = slit_length
        return self.slit_length

    def get_slit_length_unit(self):
        """
        :return: the slit length unit.
        """
        return self.slit_length_unit

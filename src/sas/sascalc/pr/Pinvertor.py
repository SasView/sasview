from py_invertor import pr_sphere

class Pinvertor:
    def __init__(self):
        pass
    def residuals(self, args):
        """
        Function to call to evaluate the residuals\n
	    for P(r) inversion\n
	    @param args: input parameters\n
	    @return: list of residuals
        """
        pass
    def set_x(self, args):
        """
        Function to set the x data
        Takes an array of the doubles as input
        Returns the number of entries found
        """
        pass
    def get_x(self, args):
        """
        Function to get the x data
        Takes an array of doubles as input
        @return: number of entries found
        """
        pass
    def set_y(self, args):
        pass
    def get_y(self, args):
        pass
    def set_err(self, args):
        pass
    def get_err(self, args):
        pass
    def set_dmax(self, args):
        pass
    def get_dmax(self, args):
        pass
    def set_qmin(self, args):
        pass
    def get_qmin(self, args):
        pass
    def set_qmax(self, args):
        pass
    def get_qmax(self, args):
        pass
    def set_alpha(self, args):
        pass
    def get_alpha(self, args):
        pass

if(__name__ == "__main__"):
    pr_sphere()

from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas


class IDFCanvas(CorfuncCanvas):
    """ Canvas for displaying real space representation"""

    def draw_data(self):
        """
        This function draws the real space data onto the plot

        The 1d correlation function in self.data, the 3d correlation function
        in self.data3, and the interface distribution function in self.data_idf
        are all draw in on the plot in linear cooredinates."""


        self.fig.clf()

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xscale("linear")
        self.axes.set_yscale("linear")
        self.axes.set_xlabel(r"Z [$\AA$]")
        self.axes.set_ylabel("IDF")
        self.axes.set_title("Interface Distribution Function")
        self.fig.tight_layout()

        if self.data is not None and len(self.data) > 0:
            self.axes.plot(self.data[0].x, self.data[0].y)
            self.axes.set_xlim(0, max(self.data[0].x) / 4)

        self.draw()


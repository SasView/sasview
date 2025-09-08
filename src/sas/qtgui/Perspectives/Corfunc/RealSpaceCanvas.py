
from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas
from sas.sascalc.corfunc.corfunc_calculator import SupplementaryParameters


class RealSpaceCanvas(CorfuncCanvas):
    """ Canvas for displaying real space representation"""

    def __init__(self, parent, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self._supplementary: SupplementaryParameters | None = None


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
        self.axes.set_ylabel("Correlation")
        self.axes.set_title("Real Space Correlations")
        self.fig.tight_layout()

        if self.data is not None and len(self.data) == 2:
            data1, data3 = self.data[0], self.data[1]
            self.axes.plot(data1.x, data1.y, label=r"$\Gamma_1(z)$")
            self.axes.plot(data3.x, data3.y, label=r"$\Gamma_3(z)$")

            self.axes.set_xlim(0, max(data1.x) / 4)
            self.legend = self.axes.legend()

        self.draw()


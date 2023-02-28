from typing import Optional
from sas.sascalc.corfunc.corfunc_calculator import SupplementaryParameters

from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas
from sas.qtgui.Perspectives.Corfunc.util import LineThroughPoints


class RealSpaceCanvas(CorfuncCanvas):
    """ Canvas for displaying real space representation"""

    def __init__(self, parent, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self._supplementary: Optional[SupplementaryParameters] = None

    @property
    def supplementary(self):
        return self._supplementary

    @supplementary.setter
    def supplementary(self, supplementary_data: SupplementaryParameters):
        self._supplementary = supplementary_data

        self.draw_data() # Is this needed?

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
        self.axes.set_xlabel("Z [$\AA$]")
        self.axes.set_ylabel("Correlation")
        self.axes.set_title("Real Space Correlations")
        self.fig.tight_layout()

        if self.supplementary is not None:

            print("Drawing tangent line")
            print(self.supplementary)

            #
            # Draw tangent line
            #
            if self.supplementary.tangent_gradient > 0:
                x_low = max([
                    self.supplementary.x_range[0],
                    self.supplementary.y_range[0]/self.supplementary.tangent_gradient])

                x_high = min([
                    self.supplementary.x_range[1],
                    self.supplementary.y_range[1]/self.supplementary.tangent_gradient])

            elif self.supplementary.tangent_gradient < 0:
                x_low = max([
                    self.supplementary.x_range[0],
                    self.supplementary.y_range[1] / self.supplementary.tangent_gradient])

                x_high = min([
                    self.supplementary.x_range[1],
                    self.supplementary.y_range[0] / self.supplementary.tangent_gradient])
            else:
                x_low = self.supplementary.x_range[0]
                x_high = self.supplementary.x_range[1]

            line = LineThroughPoints(
                [ self.supplementary.tangent_point_x,
                  self.supplementary.tangent_point_y],
                [ self.supplementary.tangent_point_x + 1,
                  self.supplementary.tangent_point_y + self.supplementary.tangent_gradient])

            y_start = line(x_low)
            y_end = line(x_high)

            print([x_low, x_high], [y_start, y_end])
            self.axes.plot([x_low, x_high], [y_start, y_end])

            self.axes.scatter(
                [self.supplementary.tangent_point_x],
                [self.supplementary.tangent_point_y])

        if self.data is not None and len(self.data) == 2:
            data1, data3 = self.data[0], self.data[1]
            self.axes.plot(data1.x, data1.y, label="1D Correlation")
            self.axes.plot(data3.x, data3.y, label="3D Correlation")

            if self.supplementary is None:
                self.axes.set_xlim(0, max(data1.x) / 4)
            else:
                self.axes.set_xlim(0, 2*self.supplementary.x_range[1])

            self.legend = self.axes.legend()

        self.draw()


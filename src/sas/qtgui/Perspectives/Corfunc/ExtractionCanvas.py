
from sas.qtgui.Perspectives.Corfunc.CorfuncCanvas import CorfuncCanvas
from sas.sascalc.corfunc.corfunc_calculator import SupplementaryParameters


class ExtractionCanvas(CorfuncCanvas):
    """ Canvas for displaying real space representation"""

    def __init__(self, parent, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self._supplementary: SupplementaryParameters | None = None

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
        self.axes.set_xlabel(r"Z [$\AA$]")
        self.axes.set_ylabel("Correlation")
        self.axes.set_title("Real Space Correlations")
        self.fig.tight_layout()

        if self.data is not None:
            data = self.data[0]
            self.axes.plot(data.x, data.y)

            if self.supplementary is not None:
                self.axes.axline(
                    (self.supplementary.tangent_point_z,
                     self.supplementary.tangent_point_gamma),
                    slope=self.supplementary.tangent_gradient,
                    color='k',
                    linestyle='--',
                    # transform=self.axes.transAxes,
                )

                # Interface properties
                self.axes.axvline(x=self.supplementary.interface_z, color='k', linestyle=':')
                self.axes.axvline(x=self.supplementary.core_z, color='k', linestyle=':')

                # Hard block estimation line
                self.axes.axhline(y=self.supplementary.hard_block_gamma, color='k', linestyle='--')

                x_points = [
                    self.supplementary.tangent_point_z,
                    self.supplementary.first_minimum_z,
                    self.supplementary.first_maximum_z,
                    self.supplementary.hard_block_z]

                y_points = [
                    self.supplementary.tangent_point_gamma,
                    self.supplementary.first_minimum_gamma,
                    self.supplementary.first_maximum_gamma,
                    self.supplementary.hard_block_gamma]

                self.axes.scatter(
                    x_points,
                    y_points,
                    color='k')

                y_size = max(data.y) - min(data.y)

                self.axes.set_xlim(0, 1.1*max(x_points))
                self.axes.set_ylim(min(y_points) - 0.1*y_size, max(data.y) + 0.1*y_size)

            else:
                self.axes.set_xlim(0, max(data.x) / 4)


        self.draw()


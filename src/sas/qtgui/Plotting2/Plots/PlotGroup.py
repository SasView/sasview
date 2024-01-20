from sas.qtgui.Plotting2.PlotManagement import Identifier, PlotRecord
from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot


class PlotGroup():
    """ MVC model for plot groups """

    def __init__(self):
        self.identifier = PlotRecord.new_plot_group_identifier()
        self._plot_identifiers: list[Identifier] = []

        PlotRecord.add_group(self)

    def add_plot(self, plot: NotionalPlot):
        identifier = plot.identifier
        self.add_plot_by_identifier(identifier)

    def add_plot_by_identifier(self, identifier: Identifier):

        if identifier in self._plot_identifiers:
            self._plot_identifiers.remove(identifier)

        self._plot_identifiers.append(identifier)

    def remove_plot(self, plot: NotionalPlot):
        self.remove_plot_by_identifier(plot.identifier)

    def remove_plot_by_identifier(self, identifier: Identifier):
        self._plot_identifiers = [i for i in self._plot_identifiers if i != identifier]

    def plots(self) -> list[NotionalPlot]:
        return [PlotRecord.plot(identifier) for identifier in self._plot_identifiers]

    def size(self) -> int:
        return len(self._plot_identifiers)


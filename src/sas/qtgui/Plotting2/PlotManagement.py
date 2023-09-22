from dataclasses import dataclass
from collections import defaultdict

from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup
from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot
from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot
from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
from sas.qtgui.Plotting2.Plots.PlotSeries import PlotSeries
from sas.qtgui.Plotting2.Plots.PlotSeriesComponent import PlotSeriesComponent


# What are we using to identify things?
Identifier = int

class NoParent(Exception):
    pass

@dataclass
class PlotLocationConcrete:
    plot_group: Identifier
    plot: Identifier
    subplot: Identifier
    axis: Identifier
    series_group: Identifier
    series: Identifier
    series_component: Identifier


class PlotRecord:
    _plot_groups: dict[Identifier, PlotGroup] = {}
    _plots: dict[Identifier, NotionalPlot] = {}
    _subplots: dict[Identifier, NotionalSubplot] = {}
    _axes: dict[Identifier, NotionalAxis] = {}
    _series_groups: dict[Identifier, PlotSeriesGroup] = {}
    _series: dict[Identifier, PlotSeries] = {}
    _series_components: dict[Identifier, PlotSeriesComponent] = {}

    _names: dict[Identifier, str] = {}

    _child_parent_links: dict[Identifier, Identifier] = {}
    _parent_child_links: dict[Identifier, list[Identifier]] = defaultdict(list[int])

    _identifiers: set[int] = set()

    # Unique ID stuff - maybe replace with UID system
    _current_identifier = 0

    @staticmethod
    def new_identifier():
        while PlotRecord._current_identifier in PlotRecord._identifiers:
            PlotRecord._current_identifier += 1

        PlotRecord._identifiers.add(PlotRecord._current_identifier)

        return PlotRecord._current_identifier

    @staticmethod
    def _iterate_plot_object_lookups():
        """ Helper method to iterate though all the different kinds of plot record"""
        yield PlotRecord._plot_groups
        yield PlotRecord._plots
        yield PlotRecord._subplots
        yield PlotRecord._axes
        yield PlotRecord._series_groups
        yield PlotRecord._series
        yield PlotRecord._series_components
        yield PlotRecord._names

    @staticmethod
    def remove(identifier: Identifier):
        # Remove from list
        PlotRecord._identifiers.remove(identifier)

        # Remove associated objects
        for dictionary in PlotRecord._iterate_plot_object_lookups():
            if identifier in dictionary:
                del dictionary[identifier]

        PlotRecord._current_identifier = identifier # Re-use

    #
    #
    #   Parent Getters
    #
    #


    @staticmethod
    def parentPlotGroup(identifier: Identifier) -> PlotGroup:
        """ Get the parent plot group from the identifier of a plot."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._plot_groups:
            return PlotRecord._plot_groups[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    @staticmethod
    def parentPlot(identifier: Identifier) -> NotionalPlot:
        """ Get the parent plot from the identifier of a subplot."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._plots:
            return PlotRecord._plots[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    @staticmethod
    def parentSubplot(identifier: Identifier) -> NotionalSubplot:
        """ Get the parent subplot from the identifier of an axis."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._subplots:
            return PlotRecord._subplots[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    @staticmethod
    def parentAxis(identifier: Identifier) -> NotionalAxis:
        """ Get the parent axis from the identifier of a series group."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._axes:
            return PlotRecord._axes[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")


    @staticmethod
    def parentSeriesGroup(identifier: Identifier) -> PlotSeriesGroup:
        """ Get the parent series group from the identifier of a series."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._series_groups:
            return PlotRecord._series_groups[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")


    @staticmethod
    def parentSeries(identifier: Identifier) -> PlotSeries:
        """ Get the parent series from the identifier of a series component."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._series:
            return PlotRecord._series[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    #
    #
    #    Child getters
    #
    #

    @staticmethod
    def childPlots(identifier: Identifier) -> list[NotionalPlot]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._plots[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def childSubplots(identifier: Identifier) -> list[NotionalSubplot]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._subplots[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def childAxes(identifier: Identifier) -> list[NotionalAxis]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._axes[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def childSeriesGroup(identifier: Identifier) -> list[PlotSeriesGroup]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series_groups[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def childSeries(identifier: Identifier) -> list[PlotSeries]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def childSeriesComponent(identifier: Identifier) -> list[PlotSeriesComponent]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series_components[child_identifier] for child_identifier in child_identifiers]


    def __new__(cls, *args, **kwargs):
        """Lock it down!!!!"""
        raise RuntimeError("Don't create me!")

class PlotLocationPattern:

    def get_matches(self) -> PlotLocationConcrete:
        pass

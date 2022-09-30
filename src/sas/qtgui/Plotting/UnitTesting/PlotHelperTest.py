# Tested module
import sas.qtgui.Plotting.PlotHelper as PlotHelper

class PlotHelperTest:

    def testDefaults(self):
        """ default method variables values """
        assert isinstance(PlotHelper._plots, dict)
        assert PlotHelper._plots == {}
        # could have leftovers from previous tests
        #self.assertEqual(PlotHelper._plot_id, 0)

    def testFunctions(self):
        """ Adding a plot """
        plot = "I am a plot. Really."
        PlotHelper.addPlot(plot)
        plot_id = PlotHelper.idOfPlot(plot)

        # We can't guarantee unique values for plot_id, as
        # the tests are executed in random order, so just
        # make sure we get consecutive values for 2 plots
        plot2 = "I am also a plot."
        PlotHelper.addPlot(plot2)
        plot_id_2 = PlotHelper.idOfPlot(plot2)
        id1 = int(plot_id[-1])
        id2 = int(plot_id_2[-1])
        assert id2 - id1 == 1

        # Other properties
        #self.assertEqual(PlotHelper.currentPlots(), [plot_id, plot_id_2])
        assert set(PlotHelper.currentPlotIds()).issubset([plot_id, plot_id_2])
        assert PlotHelper.plotById(plot_id) == plot
        assert PlotHelper.plotById(plot_id_2) == plot2

        # Delete a graph
        PlotHelper.deletePlot(plot_id)
        assert PlotHelper.currentPlotIds() == [plot_id_2]

        # Add another graph to see the counter
        plot3 = "Just another plot. Move along."
        PlotHelper.addPlot(plot3)
        #self.assertEqual(PlotHelper.idOfPlot(plot3), plot_id_2 + 1)

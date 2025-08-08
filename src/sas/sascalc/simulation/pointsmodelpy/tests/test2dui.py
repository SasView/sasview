#!/usr/bin/env python
"""
Demonstration of drawing a 2D image plot using the "hot" colormap
"""

#--------------------------------------------------------------------------------
#  Imports:
#--------------------------------------------------------------------------------

from math import sin, sqrt

from enthought.chaco.colormap_legend import ColormapLegend
from enthought.chaco.default_colormaps import hot
from enthought.chaco.demo.demo_base import PlotApplicationWindow
from enthought.chaco.image_plot_value import CmapImagePlotValue, ImageData
from enthought.chaco.plot_axis import PlotAxis
from enthought.chaco.plot_group import PlotGroup
from enthought.pyface import GUI
from enthought.util.numerix import arange


class ImagePlotApplicationWindow( PlotApplicationWindow ):

    ###########################################################################
    # PlotApplicationWindow interface.
    ###########################################################################

    def _create_plot( self ):
        """ Create the plot to be displayed. """

        # Create the image data and the index values
        #value_grid = zeros((100,100), NumericFloat)
        from testlores2d import get2d_2
        value_grid = get2d_2()
        #self._compute_function(value_grid)
        index_vals = (arange(value_grid.shape[0]), arange(value_grid.shape[1]))

        data = ImageData(value_grid, index_vals)
        print(value_grid, index_vals)

        # Create the index axes
        xaxis = PlotAxis(tick_visible=False, grid_visible=False)
                        # bound_low = index_vals[0][0], bound_high = index_vals[0][-1])
        yaxis = PlotAxis(tick_visible=False, grid_visible=False)
                     #bound_low = index_vals[1][0], bound_high = index_vals[1][-1])
        xaxis.visible = False
        yaxis.visible = False

        # Create the value axis (i.e. colormap)
        cmap = hot(0,1)

        # Create the Image PlotValue
#        image = CmapImagePlotValue(data, cmap, axis_index = xaxis, axis = yaxis, type='image')
        image = CmapImagePlotValue(data, cmap,type='image')
        image.weight = 10

        cmap_legend = ColormapLegend(cmap, margin_width=31, margin_height=31)
        cmap_legend.weight = 0.4

        group = PlotGroup(cmap_legend, image, orientation='horizontal')

        return group

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _compute_function(self, ary):
        "Fills in ary with the sin(r)/r function"

        width, height = ary.shape
        for i in range(width):
            for j in range(height):
                x = i - width / 2.0
                x = x / (width/2.0) * 15
                y = j - height / 2.0
                y = y / (height/2.0) * 15

                radius = sqrt(x*x + y*y)
                if radius == 0.0:
                    ary[i,j] = 1
                else:
                    ary[i,j] = sin(radius) / radius

        return

def main():

    # Create the GUI (this does NOT start the GUI event loop).
    gui = GUI()

    # Screen size:
    screen_width = gui.system_metrics.screen_width or 1024
    screen_height = gui.system_metrics.screen_height or 768

    # Create and open the main window.
    window = ImagePlotApplicationWindow( title = "Plot" )
    #window.plot_item = object
    window.size = ( 2 * screen_width / 3, 2 * screen_height / 3 )
    window.open()

    # Start the GUI event loop.
    gui.start_event_loop()


#===============================================================================
#  Program start-up:
#===============================================================================

if __name__ == '__main__':
    main()

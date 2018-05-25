# -*- coding: utf-8 -*-
import base64
import datetime
import re
import logging
from io import BytesIO
import urllib.parse

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from sas.qtgui.Plotting.Plotter import Plotter
from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities

class ReportPageLogic(object):
    """
    Logic for the Report Page functionality. Refactored from FittingWidget.
    """
    def __init__(self, parent=None, kernel_module=None, data=None, index=None, model=None):

        self.parent = parent
        self.kernel_module = kernel_module
        self.data = data
        self._index = index
        self.model = model

    @staticmethod
    def cleanhtml(raw_html):
        """Remove html tags from a document"""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def reportList(self):
        """
        Return the HTML version of the full report
        """
        if self.kernel_module is None:
            report_txt = "No model defined"
            report_html = HEADER % report_txt
            images = []
            return [report_html, report_txt, images]

        # Get plot image from plotpanel
        images = self.getImages()

        imagesHTML = ""
        if images is not None:
            imagesHTML = self.buildPlotsForReport(images)

        report_header = self.reportHeader()

        report_parameters = self.reportParams()

        report_html = report_header + report_parameters + imagesHTML

        report_txt = self.cleanhtml(report_html)

        report_list = [report_html, report_txt, images]

        return report_list

    def reportHeader(self):
        """
        Look at widget state and extract report header info
        """
        report = ""

        title = self.data.name
        current_time = datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y")
        filename = self.data.filename
        modelname = self.kernel_module.id
        if hasattr(self.data, 'xmin'):
            qrange_min = self.data.xmin
            qrange_max = self.data.xmax
        else:
            qrange_min = min(self.data.x)
            qrange_max = max(self.data.x)
        qrange = "min = {}, max = {}".format(qrange_min, qrange_max)

        title = title + " [" + current_time + "]"
        title_name = HEADER % title
        report = title_name
        report = report + CENTRE % "File name:{}\n".format(filename)
        report = report + CENTRE % "Model name:{}\n".format(modelname)
        report = report + CENTRE % "Q Range: {}\n".format(qrange)
        chi2_repr = GuiUtils.formatNumber(self.parent.chi2, high=True)
        report = report + CENTRE % "Chi2/Npts:{}\n".format(chi2_repr)

        return report

    def buildPlotsForReport(self, images):
        """ Convert Matplotlib figure 'fig' into a <img> tag for HTML use using base64 encoding. """
        html = FEET_1 % self.data.filename

        for fig in images:
            canvas = FigureCanvas(fig)
            png_output = BytesIO()
            canvas.print_png(png_output)
            data = png_output.getvalue()
            data64 = base64.b64encode(data)
            data_to_print = urllib.parse.quote(data64)
            html += '<img src="data:image/png;base64,{}">'.format(data_to_print)

        return html

    def reportParams(self):
        """
        Look at widget state and extract parameters
        """
        pars = FittingUtilities.getStandardParam(self.model)
        if pars is None:
            return ""

        report = ""
        plus_minus = " &#177; "
        for value in pars:
            try:
                par_name = value[1]
                par_fixed = not value[0]
                par_value = value[2]
                par_unit = value[7]
                # Convert units for nice display
                par_unit = GuiUtils.convertUnitToHTML(par_unit.strip())
                if par_fixed:
                    error = " (fixed)"
                else:
                    error = plus_minus + str(value[4][1])
                param = par_name + " = " + par_value + error + " " + par_unit
            except IndexError as ex:
                # corrupted model. Complain and skip the line
                logging.error("Error in parsing parameters: "+str(ex))
                continue
            report += CENTRE % param + "\n"

        return report

    def getImages(self):
        """
        Create MPL figures for the current fit
        """
        graphs = []
        modelname = self.kernel_module.name
        if not modelname or self._index is None:
            return None
        plots = GuiUtils.plotsFromModel(modelname, self._index)
        # Call show on requested plots
        # All same-type charts in one plot
        for plot_set in plots:
            if isinstance(plot_set, Data1D):
                if 'residuals' in plot_set.title.lower():
                    res_plot = Plotter(self, quickplot=True)
                    res_plot.plot(plot_set)
                    graphs.append(res_plot.figure)
                    continue
                if not 'new_plot' in locals():
                    new_plot = Plotter(self, quickplot=True)
                new_plot.plot(plot_set)
            elif isinstance(plot_set, Data2D):
                plot2D = Plotter2D(self, quickplot=True)
                plot2D.item = self._index
                plot2D.plot(plot_set)
                graphs.append(plot2D.figure)
            else:
                msg = "Incorrect data type passed to Plotting"
                raise AttributeError(msg)

        if 'new_plot' in locals() and isinstance(new_plot.data, Data1D):
            graphs.append(new_plot.figure)

        return graphs


# Simple html report template
HEADER = "<html>\n"
HEADER += "<head>\n"
HEADER += "<meta http-equiv=Content-Type content='text/html; "
HEADER += "charset=utf-8'> \n"
HEADER += "<meta name=Generator >\n"
HEADER += "</head>\n"
HEADER += "<body lang=EN-US>\n"
HEADER += "<div class=WordSection1>\n"
HEADER += "<p class=MsoNormal><b><span ><center><font size='4' >"
HEADER += "%s</font></center></span></center></b></p>"
HEADER += "<p class=MsoNormal>&nbsp;</p>"
PARA = "<p class=MsoNormal><font size='4' > %s \n"
PARA += "</font></p>"
CENTRE = "<p class=MsoNormal><center><font size='4' > %s \n"
CENTRE += "</font></center></p>"
FEET_1 = \
"""
<p class=MsoNormal>&nbsp;</p>
<br>
<p class=MsoNormal><b><span ><center> <font size='4' > Graph
</font></span></center></b></p>
<p class=MsoNormal>&nbsp;</p>
<center>
<br><font size='4' >Model Computation</font>
<br><font size='4' >Data: "%s"</font><br>
"""
FEET_2 = \
"""<img src="%s" width="540"></img>
"""
ELINE = """<p class=MsoNormal>&nbsp;</p>
"""


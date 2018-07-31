# -*- coding: utf-8 -*-
import base64
import datetime
import re
import sys
import tempfile

import logging
from io import BytesIO
import urllib.parse

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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

            # Create a "safe" location - system tmp
            tmp_file = tempfile.TemporaryFile(suffix=".png")
            try:
                fig.savefig(tmp_file.name, dpi=75)
                fig.savefig(png_output, dpi=75)
            except PermissionError:
                # sometimes one gets "permission denied" for temp files
                # mainly on Windows 7 *gasp*. Let's try local directory
                tmp_file = open("_tmp.png", "w+")
                try:
                    fig.savefig(tmp_file.name, dpi=75)
                    fig.savefig(png_output, dpi=75)
                except Exception as ex:
                    logging.error("Creating of the report failed: %s"%str(ex))
                    return

            data_to_print = png_output.getvalue() == open(tmp_file.name, 'rb').read()
            tmp_file.close()
            data64 = base64.b64encode(png_output.getvalue())
            data_to_print = urllib.parse.quote(data64)

            feet = FEET_2
            if sys.platform == "darwin":  # Mac
                feet = FEET_3
            html += feet.format(data_to_print)
            html += ELINE
            del canvas
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
        plot_ids = [plot.id for plot in GuiUtils.plotsFromModel(modelname, self._index)]

        # Active plots
        import sas.qtgui.Plotting.PlotHelper as PlotHelper
        shown_plot_names = PlotHelper.currentPlots()

        # current_plots = list of graph names of currently shown plots
        # which are related to this dataset
        current_plots = [name for name in shown_plot_names if PlotHelper.plotById(name).data.id in plot_ids]

        for name in current_plots:
            # get the plotter object first
            plotter = PlotHelper.plotById(name)
            graphs.append(plotter.figure)

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
'''<img src="data:image/png;base64,{}"></img>
'''
FEET_3 = \
'''<img width="540" src="data:image/png;base64,{}"></img>
'''
ELINE = """<p class=MsoNormal>&nbsp;</p>
"""


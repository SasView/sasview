import base64
import datetime
import logging
import sys
import urllib.parse
from io import BytesIO

import html2text
from bumps import options
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from sasmodels import __version__ as SASMODELS_VERSION

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.system.version import __version__ as SASVIEW_VERSION


# TODO: Integrate with other reports
class ReportPageLogic:
    """
    Logic for the Report Page functionality. Refactored from FittingWidget.
    """
    def __init__(self, parent=None, kernel_module=None, data=None, index=None, params=None):

        self.parent = parent
        self.kernel_module = kernel_module
        self.data = data
        self._index = index
        self.params = params


    def reportList(self) -> ReportData: # TODO: Rename to reference report object
        """
        Return the HTML version of the full report
        """
        if self.kernel_module is None:

            text = "No model defined"

            return ReportData(
                html=HEADER % text,
                text=text)

        # Get plot image from plotpanel
        images = self.getImages()

        imagesHTML = ""
        if images is not None:
            imagesHTML = self.buildPlotsForReport(images)

        report_header = self.reportHeader()

        report_parameters = self.reportParams()

        report_html = report_header + report_parameters + imagesHTML

        report_txt = html2text.html2text(GuiUtils.replaceHTMLwithASCII(report_html))

        # report_list = ReportData(html=report_html, text=report_txt, images=images)
        report_list = ReportData(html=report_html, text=report_txt)

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
        optimizer = options.FIT_CONFIG.selected_fitter.name
        if hasattr(self.data, 'xmin'):
            qrange_min = self.data.xmin
            qrange_max = self.data.xmax
        else:
            qrange_min = min(self.data.x)
            qrange_max = max(self.data.x)
        qrange = f"min = {qrange_min}, max = {qrange_max}"

        title = title + " [" + current_time + "]"
        title_name = HEADER % title
        report = title_name
        report += CENTRE % f"File name: {filename}\n"
        report += CENTRE % f"SasView version: {SASVIEW_VERSION}\n"
        report += CENTRE % f"SasModels version: {SASMODELS_VERSION}\n"
        report += CENTRE % f"Fit optimizer used: {optimizer}\n"
        report += CENTRE % f"Model name: {modelname}\n"
        report += CENTRE % f"Q Range: {qrange}\n"
        chi2_repr = GuiUtils.formatNumber(self.parent.chi2, high=True)
        report += CENTRE % f"Chi2/Npts: {chi2_repr}\n"

        return report

    def buildPlotsForReport(self, images): # TODO: Unify with other report image to html conversion
        """ Convert Matplotlib figure 'fig' into a <img> tag for HTML use using base64 encoding. """
        html = FEET_1 % self.data.name

        for fig in images:
            canvas = FigureCanvas(fig)
            png_output = BytesIO()
            try:
                if sys.platform == "darwin":
                    fig.savefig(png_output, format="png", dpi=150)
                else:
                    fig.savefig(png_output, format="png", dpi=75)
            except PermissionError as ex:
                logging.error("Creating of the report failed: %s"%str(ex))
                return
            data64 = base64.b64encode(png_output.getvalue())
            data_to_print = urllib.parse.quote(data64)
            feet = FEET_2
            if sys.platform == "darwin":  # Mac
                feet = FEET_3
            html += feet.format(data_to_print)
            html += ELINE
            png_output.close()
            del canvas
        return html

    def reportParams(self):
        """
        Look at widget state and extract parameters
        """
        if self.params is None:
            return ""

        report = ""
        plus_minus = " &#177; "
        for value in self.params:
            try:
                par_name = value[1]
                par_dispersion_type = ""
                if 'Distribution of' in par_name:
                    par_name_original = par_name.replace('Distribution of ', '')
                    par_dispersion_type = self.kernel_module.dispersion[
                        par_name_original.strip()]['type']
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
                if par_dispersion_type:
                    param += " Function: " + par_dispersion_type
            except IndexError as ex:
                # corrupted model. Complain and skip the line
                logging.error("Error in parsing parameters: "+str(ex))
                continue
            report += CENTRE % param + "\n"

        return report

    def getImages(self) -> list[PlotterBase]:
        """
        Create MPL figures for the current fit
        """
        graphs = []
        modelname = self.kernel_module.name
        if not modelname or self._index is None:
            return []
        plot_ids = [plot.id for plot in GuiUtils.plotsFromModel(modelname, self._index)]

        # Active plots
        import sas.qtgui.Plotting.PlotHelper as PlotHelper
        shown_plot_names = PlotHelper.currentPlotIds()

        # current_plots = list of graph names of currently shown plots
        # which are related to this dataset
        current_plots = [name for name in shown_plot_names if PlotHelper.plotById(name).data[0].id in plot_ids]

        for name in current_plots:
            # get the plotter object first
            plotter = PlotHelper.plotById(name)
            graphs.append(plotter.figure)

        return graphs


# Simple html report template
# TODO Remove microsoft based stuff - probably implicit in the refactoring to come
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


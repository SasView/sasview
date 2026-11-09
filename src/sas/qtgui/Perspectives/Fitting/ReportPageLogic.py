"""
The fit page report (FW-MVC-DESIGN.md §3.6.4, Phase 7): rendered from an explicit
``ReportContext``, which the page assembles from its document and results.
"""
import base64
import datetime
import logging
import sys
import urllib.parse
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

import html2text
from bumps import options
from matplotlib.figure import Figure

from sasmodels import __version__ as SASMODELS_VERSION

import sas.qtgui.Plotting.PlotHelper as PlotHelper
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.Reports.reportdata import ReportData
from sas.system.version import __version__ as SASVIEW_VERSION

logger = logging.getLogger(__name__)


@dataclass
class ReportContext:
    """Everything the report shows, gathered by the page."""
    model_id: str | None              # None: no model selected
    mnemonic: str
    data: Any                         # the active Data1D/Data2D (the theory grid without data)
    params: list                      # serializer.report_parameters
    dispersions: dict = field(default_factory=dict)   # {parameter: distribution type}
    qmin: float = 0.0
    qmax: float = 0.0
    chi2: float | None = None
    smearing: tuple = ("None", "", None, None)        # (mode, accuracy, d_down, d_up)
    resolution: str | None = None     # the resolution the data carries (services.theory.resolution_of)
    is_batch: bool = False
    index: Any = None                 # the Data Explorer item whose plots are shown
    results_panel: Any = None
    grid_window: Any = None
    optimizer: str = field(default_factory=lambda: options.FIT_CONFIG.selected_fitter.name)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y"))


class ReportPageLogic:
    """Renders a ReportContext as html and text."""
    def __init__(self, context: ReportContext):
        self.context = context
        self.data = context.data

    def reportList(self) -> ReportData:
        """Return the HTML version of the full report"""
        if self.context.model_id is None:
            text = "No model defined"
            return ReportData(
                html=HEADER.format(text),
                text=text)

        # Get plot image from plotpanel
        images = self.getImages()
        images_html = self.buildPlotsForReport(images) if images is not None and any(images) else ""
        report_header = self.reportHeader()
        report_parameters = self.reportParams()
        results_table = self.getResultsTable()
        batch_table = self.getBatchResults()

        report_html = report_header + report_parameters + images_html + results_table + batch_table
        report_txt = html2text.html2text(GuiUtils.replaceHTMLwithASCII(report_html))

        return ReportData(html=report_html, text=report_txt)

    def reportHeader(self) -> str:
        """Look at widget state and extract report header info"""
        context = self.context
        title = self.data.name
        current_time = context.timestamp
        filename = self.data.filename
        modelname = context.model_id
        optimizer = context.optimizer
        smear_format = self.getFitSmearing()
        if hasattr(self.data, 'xmin'):
            data_qrange_min = self.data.xmin
            data_qrange_max = self.data.xmax
        else:
            data_qrange_min = min(self.data.x)
            data_qrange_max = max(self.data.x)
        data_qrange = f"min = {data_qrange_min}, max = {data_qrange_max}"
        fit_qrange = f"min = {context.qmin}, max = {context.qmax}"

        report = HEADER.format(title + " [" + current_time + "]")
        report += CENTRE.format(f"File name: {filename}")
        report += CENTRE.format(f"SasView version: {SASVIEW_VERSION}")
        report += CENTRE.format(f"SasModels version: {SASMODELS_VERSION}")
        report += CENTRE.format(f"Fit optimizer used: {optimizer}")
        report += CENTRE.format(f"Model name: {modelname}")
        report += CENTRE.format(f"Q Range of the Data: {data_qrange}")
        report += CENTRE.format(f"Q Range of the Fit: {fit_qrange}")
        report += smear_format
        chi2_repr = GuiUtils.formatNumber(context.chi2, high=True)
        report += CENTRE.format(f"Chi2/Npts: {chi2_repr}")

        return report

    def buildPlotsForReport(self, images: list[Figure]) -> str:
        """ Convert Matplotlib figure 'fig' into a <img> tag for HTML use using base64 encoding. """
        html = FEET_1.format(self.data.name)

        for fig in images:
            png_output = BytesIO()
            try:
                dpi = 150 if sys.platform == "darwin" else 75
                fig.savefig(png_output, format="png", dpi=dpi)
            except PermissionError as ex:
                logger.error(f"Creating of the report failed: {str(ex)}")
                return ''
            data64 = base64.b64encode(png_output.getvalue())
            data_to_print = urllib.parse.quote(data64)
            feet = FEET_3 if sys.platform == "darwin" else FEET_2
            html += feet.format(data_to_print) + ELINE
            png_output.close()
        return html

    def reportParams(self) -> str:
        """Look at widget state and extract parameters"""
        if self.context.params is None:
            return ""

        report = ""
        plus_minus = " &#177; "
        for value in self.context.params:
            try:
                par_name = value[1]
                par_dispersion_type = ""
                if 'Distribution of' in par_name:
                    par_name_original = par_name.replace('Distribution of ', '')
                    par_dispersion_type = self.context.dispersions[par_name_original.strip()]
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
                logger.error("Error in parsing parameters: "+str(ex))
                continue
            report += CENTRE.format(param)

        return report

    def getFitSmearing(self) -> str:
        """Format the smearing information and return """
        smearing, accuracy, smearing_min, smearing_max = self.context.smearing
        smear_format = ""
        if smearing != "None":
            type = self.context.resolution if self.context.resolution else smearing
            smear_format = f"{type}"
            if accuracy:
                smear_format += f", Accuracy = {accuracy}"
            if "Slit" in type:
                # All slit smearing should be handled here
                smear_format += f", dQl = {smearing_max} Å, dQw = {smearing_min} Å"
            elif "Custom" in type:
                # Custom pinhole smearing should be handled here, because there is only one input
                smear_format += f", dQ/Q = {smearing_max}%"
            elif "Pinhole" in type:
                # The boxes are labelled backwards in the smearing widget.
                smear_format += f", dQ/Q range = {smearing_max}%  {smearing_min}%"
            smear_format = CENTRE.format(f"Smearing Information: {smear_format}")
        return smear_format

    def getResultsPlots(self) -> list[Figure]:
        """Gather the plots from the bumps results panel."""
        plots = []
        results_panel = self.context.results_panel
        if results_panel is not None:
            results_panels = [
                results_panel.convergenceView,
                results_panel.correlationView,
                results_panel.uncertaintyView,
                results_panel.traceView
            ]
            for panel in results_panels:
                # Only include the plot if it has recent results
                if panel.state is not None:
                    plots.append(panel.figure)

        return plots

    def getResultsTable(self) -> str:
        """Format the bumps results correlation table into html."""
        results_table = ''
        results_panel = self.context.results_panel
        if results_panel is not None:
            if results_panel.correlationTable.state:
                headers, rows = results_panel.correlationTable._parse_stats()
                results_table += '<table>\n<tr><th>' + '</th><th>'.join(headers) + '</th></tr>'
                for row in rows:
                    results_table += '<tr><td>' + '</td><td>'.join(row) + '</td></tr>'
                results_table += '</table>'
        return results_table

    def getBatchResults(self) -> str:
        """Format the batch results table into html."""
        batch_results_table = ''
        if self.context.is_batch:
            batch_results_table += CENTRE.format("Batch Results") + "<table>"
            batch_panel = self.context.grid_window
            if batch_table := batch_panel.dataFromTable(batch_panel.currentTable()):
                for row in batch_table:
                    batch_results_table += '<tr><td>' + '</td><td>'.join(row) + '</td></tr>'
                batch_results_table += '</table>'
        return batch_results_table

    def getImages(self) -> list[Figure]:
        """Create MPL figures for the current fit.

        Uses `PlotHelper.figures_for_plot_ids` to collect any live figures shown
        for the dataset, then appends result-panel figures.
        """
        modelname = self.context.mnemonic
        if not modelname or self.context.index is None:
            return []

        plot_ids = [plot.id for plot in GuiUtils.plotsFromModel(modelname, self.context.index)]
        graphs = PlotHelper.figures_for_plot_ids(plot_ids)
        graphs.extend(self.getResultsPlots())

        return graphs


# Simple html report template
HEADER = "<html>\n"
HEADER += "<head>\n"
HEADER += "<meta http-equiv=Content-Type content='text/html; charset=utf-8'> \n"
HEADER += "</head>\n"
HEADER += "<body lang=EN-US>\n"
HEADER += "<div>\n"
HEADER += "<p><b><span><center> {} </center></span></center></b></p>"
HEADER += "<p>&nbsp;</p>"
PARA = "<p> {} \n</p>"
CENTRE = "<p><center>{}</center></p>\n"
FEET_1 = \
"""
<p>&nbsp;</p>
<br>
<p><b><span><center>Graph</span></center></b></p>
<p>&nbsp;</p>
<center>
<br>Model Computation
<br>Data: "{}"<br>
"""
FEET_2 = '<img src="data:image/png;base64,{}"></img>\n'
FEET_3 = '<img width="540" src="data:image/png;base64,{}"></img>\n'
ELINE = "<p>&nbsp;</p>\n"


import base64
import datetime
import importlib.resources as pkg_resources
import logging
import os
import sys
from collections.abc import Iterable
from io import BytesIO
from typing import Any

import dominate
import html2text
from dominate import tags
from dominate.util import raw

import sasmodels

import sas.sasview
import sas.system.version
from sas.qtgui.Plotting.PlotterBase import Data1D
from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Utilities.Reports.reportdata import ReportData

#
# Utility classes
#

class pretty_units(tags.span):
    """ HTML tag for units, prettifies angstroms, inverse angstroms and inverse cm
    TODO: Should be replaced when there is a better way of handling units"""
    tagname = "span"

    def __init__(self, unit_string: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        clean_unit_string = unit_string.strip()

        if clean_unit_string == "A":
            text = raw("&#8491;") # Overring A
            do_superscript_power = False

        elif clean_unit_string == "1/A" or clean_unit_string == "A^{-1}":
            text = raw("&#8491;") # Overring A
            do_superscript_power = True

        elif clean_unit_string == "1/cm" or clean_unit_string == "cm^{-1}":
            text = "cm"
            do_superscript_power = True

        else:
            text = clean_unit_string
            do_superscript_power = False

        self.add(text)

        if do_superscript_power:
            with self:
                tags.span("-1", style="vertical-align:super;")



#
# Main report builder class
#

class ReportBase:
    def __init__(self,
                 title: str,
                 style_link: str | None=None,
                 show_figure_section_title=True,
                 show_param_section_title=True):

        """ Holds a (DOM) representation of a report, the details that need
         to go into the report can be added with reasonably simple calls, e.g. add_table, add_plot

         :param title: Report title
         :param style_link: If provided will set style in the html to the specified URL, rather than embedding contents
                            from local report_style.css
         :show_figure_section_title: Add h2 tag for figure section
         :show_figure_section_title: Add h2 tag for parameters section


         """

        #
        # Set up the html document and specify the general layout
        #

        self._html_doc = dominate.document(title=title)
        self.plots = []

        with self._html_doc.head:
            tags.meta(http_equiv="Content-Type", content="text/html; charset=utf-8")
            tags.meta(name="Generator", content=f"SasView {sas.system.version.__version__}")

            if style_link is not None:
                tags.link(rel="stylesheet", href=style_link)

            else:
                style_data = pkg_resources.read_text("sas.qtgui.Utilities.Reports", "report_style.css")
                tags.style(style_data)

        with self._html_doc.body:
            with tags.div(id="main"):

                with tags.div(id="sasview"):
                    tags.h1(title)
                    tags.p(datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y"))
                    with tags.div(id="version-info"):
                        tags.p(f"sasview {sas.system.version.__version__}, sasmodels {sasmodels.__version__}", cls="sasview-details")

                tags.div(id="perspective")
                with tags.div(id="data"):
                    tags.h2("Data")

                with tags.div(id="model"):

                    if show_param_section_title:
                        tags.h2("Details")

                    tags.div(id="model-details")
                    tags.div(id="model-parameters")

                with tags.div(id='figures-outer'):
                    if show_figure_section_title:
                        tags.h2("Figures")

                    tags.div(id="figures")

    def add_data_details(self, data: Data1D):
        """ Add details of input data to the report"""

        n_points = len(getattr(data, 'x', []))
        low_q = getattr(data, "xmin", min(data.x) if len(data.x) > 0 else None)
        high_q = getattr(data, "xmax", max(data.x) if len(data.x) > 0 else None)


        table_data = [
            ["File", os.path.basename(data.filename)],
            ["n Samples", n_points],
            ["Q min", tags.span(low_q, pretty_units(data.x_unit))],
            ["Q max", tags.span(high_q, pretty_units(data.x_unit))]
        ]

        self.add_table(table_data, target_tag="data", column_prefix="data-column")



    def add_plot(self, fig, image_type="png", figure_title: str | None=None):
        """ Add a plot to the report

        :param fig: matplotlib.figure.Figure, Matplotlib figure object to add
        :param image_type: str, type of embedded image - 'svg' or 'png', defaults to 'svg'
        :param figure_title: Optional[str] - Optionally add an html header tag, defaults to None

        :raises ValueError: if image_type is bad
        """

        if figure_title is not None:
            tags.h2(figure_title)

        if image_type == "svg":
            logging.warning("xhtml2pdf does not currently support svg export to pdf.")
            self._add_plot_svg(fig)
        elif image_type == "png":
            self._add_plot_png(fig)
        else:
            raise ValueError("image_type must be either 'svg' or 'png'")

    def _add_plot_svg(self, fig):
        try:
            with BytesIO() as svg_output:
                fig.savefig(svg_output, format="svg")
                self.add_image_from_bytes(svg_output, file_type='svg+xml')
                self.plots.append(fig)

        except PermissionError as ex:
            logging.error("Creating of report images failed: %s" % str(ex))
            return

    def _add_plot_png(self, fig):
        try:
            with BytesIO() as png_output:
                if sys.platform == "darwin":
                    fig.savefig(png_output, format="png", dpi=150)
                else:
                    fig.savefig(png_output, format="png", dpi=75)

                self.add_image_from_bytes(png_output, file_type='png')
                self.plots.append(fig)

        except PermissionError as ex:
            logging.error("Creating of report images failed: %s" % str(ex))
            return

    def add_image_from_file(self, filename: str):
        """ Add image to report from a source file"""
        extension = filename.split(".")[-1]

        with open(filename, 'rb') as fid:
            bytes = BytesIO(fid.read())
            self.add_image_from_bytes(bytes, extension)

    def add_image_from_bytes(self, bytes: BytesIO, file_type='png'):
        """ Add an image from a BytesIO object"""

        data64 = base64.b64encode(bytes.getvalue())
        with self._html_doc.getElementById("figures"):
            with tags.p():
                tags.img(src=f"data:image/{file_type};base64," + data64.decode("utf-8"),
                         style="width:100%")

    def add_table_dict(self, d: dict[str, Any], titles: tuple[str, str] | None=None):

        self.add_table([[key, d[key]] for key in d], titles=titles)

    def add_table(self,
                  data: list[list[Any]],
                  titles: Iterable[str] | None=None,
                  target_tag="model-parameters",
                  column_prefix="column"):

        """ Add a table of parameters to the report"""
        with self._html_doc.getElementById(target_tag):

            with tags.table():

                if titles is not None:
                    with tags.tr():
                        for title in titles:
                            tags.th(title)

                for row in sorted(data, key=lambda x: x[0]):
                    with tags.tr():
                        for i, value in enumerate(row):
                            tags.td(value, cls=f"{column_prefix}-{i}")

    @property
    def text(self) -> str:
        """ Text version of the document (actually RST)"""
        return html2text.html2text(GuiUtils.replaceHTMLwithASCII(self.html)).encode("ascii", "ignore").decode()

    @property
    def html(self) -> str:
        """ A string containing the html of the document"""
        return str(self._html_doc)

    @property
    def report_data(self) -> ReportData:
        return ReportData(
            self.html,
            self.text)

    def save_html(self, filename: str):
        with open(filename, 'w') as fid:
            print(self._html_doc, file=fid)

    def save_text(self, filename: str):
        with open(filename, 'w') as fid:
            print(self.text, file=fid)

    def save_pdf(self, filename: str):
        # import moved because of costly import time
        from xhtml2pdf import pisa
        with open(filename, 'w+b') as fid:
            try:
                pisa.CreatePDF(str(self._html_doc),
                               dest=fid,
                               encoding='UTF-8')

            except Exception as ex:
                import traceback
                logging.error("Error creating pdf: " + str(ex) + "\n" + traceback.format_exc())




def main():

    """ This can be run locally without sasview to make it easy to adjust the report layout/styling,
    it will generate a report with some arbitrary data"""

    import matplotlib.pyplot as plt
    import numpy as np

    from sasdata.dataloader.loader import Loader
    loader = Loader()


    # Constructor:

    # Select this one to use a link, not embedding, for the css - quicker messing about with styling with
    # rb = ReportBase("Test Report", "report_style.css")

    # Use this to embed
    rb = ReportBase("Test Report")

    # Arbitrary file used to add file info to the report
    fileanem = "100nmSpheresNodQ.txt"
    path_to_data = "../../../sasview/test/1d_data"
    filename = os.path.join(path_to_data, fileanem)
    data = loader.load(filename)[0]

    rb.add_data_details(data)

    # Some made up parameters
    rb.add_table_dict({"A": 10, "B": 0.01, "C": 'stuff', "D": False}, ("Parameter", "Value"))

    # A test plot
    x = np.arange(100)
    y = (x-50)**2
    plt.plot(x, y)
    rb.add_plot(plt.gcf(), image_type='png')

    # Save in the different formats
    rb.save_html("report_test.html")
    rb.save_pdf("report_test.pdf")
    rb.save_text("report_test.rst")

    print(rb._html_doc) # Print the HTML version
    print(rb.text) # Print the text version


if __name__ == "__main__":
    main()

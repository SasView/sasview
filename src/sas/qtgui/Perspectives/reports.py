from typing import Any, Dict, Optional

import sys
import os
import datetime
import base64

from io import BytesIO

import matplotlib.figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import dominate
from dominate.tags import *
from dominate.util import raw

import sas.sasview
import sasmodels
import logging

from sas.qtgui.Plotting.PlotterBase import Data1D, PlotterBase

class pretty_units(span):
    """ HTML tag for units, prettifies angstroms, inverse angstroms and inverse cm"""
    tagname = "span"

    def __init__(self, unit_string: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        clean_unit_string = unit_string.strip()

        if clean_unit_string == "A":
            text = raw("&#8491;")
            do_superscript_power = False

        elif clean_unit_string == "1/A" or clean_unit_string == "A^{-1}":
            text = raw("&#8491;")
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
                span("-1", style="vertical-align:super;")




class ReportBuilder:
    """ Holds a (DOM) representation of a report, the details that need
     to go into the report can be added to with reasonably simple calls"""
    def __init__(self, title: str):

        #
        # Set up the html document and specify the general layout
        #

        self.html_doc = dominate.document(title=title)

        with self.html_doc.head:
            meta(http_equiv="Content-Type", content="text/html; charset=utf-8")
            meta(name="Generator", content=f"SasView {sas.sasview.__version__}")

        with self.html_doc.body:
            with div(id="sasview"):
                h1(title)
                p(datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y"))
                with div(id="version-info"):
                    p(f"sasview {sas.sasview.__version__}, sasmodels {sasmodels.__version__}", cls="sasview-details")

            div(id="perspective")
            with div(id="data"):
                h2("Data")

            with div(id="model"):
                div(id="model-details")
                div(id="model-parameters")

            div(id="figures")

    def add_data_details(self, data: Data1D):
        """ Add details of input data to the report"""
        with self.html_doc.getElementById("data"):

            with div(cls="data-file"):
                h3(f"File: {os.path.basename(data.filename)}")

                with table():

                    with tr():
                        td("Q Samples")
                        td(str(len(getattr(data, 'x', []))))
                        td()

                    with tr():
                        td("Q low")
                        td(getattr(data, "xmin", min(data.x))) # TODO: remove dynamically assigned field, xmin
                        with td():
                            pretty_units(data.x_unit)


                    with tr():
                        td("Q high")
                        td(getattr(data, "xmax", max(data.x))) # TODO: remove dynamically assigned field, xmax
                        with td():
                            pretty_units(data.y_unit)

    def add_plot(self, fig: matplotlib.figure.Figure, figure_title: Optional[str]=None):
        """ Add a plot to the report """

        if figure_title is not None:
            h2(figure_title)

        try:
            with BytesIO() as png_output:
                if sys.platform == "darwin":
                    fig.savefig(png_output, format="png", dpi=150)
                else:
                    fig.savefig(png_output, format="png", dpi=75)

                self.add_image_from_bytes(png_output)

        except PermissionError as ex:
            logging.error("Creating of report images failed: %s" % str(ex))
            return

    def add_image_from_file(self, filename: str):
        """ Add image to report from a source file"""
        with open(filename, 'rb') as fid:
            bytes = BytesIO(fid.read())
            self.add_image_from_bytes(bytes)

    def add_image_from_bytes(self, bytes: BytesIO):
        """ Add an image from a BytesIO object"""

        data64 = base64.b64encode(bytes.getvalue())
        with self.html_doc.getElementById("figures"):
            img(src="data:image/png;base64," + data64.decode("utf-8"))


    def add_table(self, parameters: Dict[str, Any]):
        """ Add a table of parameters to the report"""
        with self.html_doc.getElementById("model-parameters"):
            with table():
                for key in sorted(parameters.keys()):
                    with tr():
                        th(key)
                        th(str(parameters[key])) # TODO decide on how to represent parameters


# Debugging tool
def main():
    from sas.sascalc.dataloader.loader import Loader
    import os
    loader = Loader()

    fileanem = "100nmSpheresNodQ.txt"
    path_to_data = "../../../sas/sasview/test/1d_data"

    filename = os.path.join(path_to_data, fileanem)
    data = loader.load(filename)[0]

    rb = ReportBuilder("Test Report")

    rb.add_data_details(data)
    rb.add_table({"A": 10, "B": 0.01, "C": 'stuff', "D": False})
    rb.add_image_from_file(os.path.join(path_to_data, "../../../qtgui/images/angles.png"))

    print(rb.html_doc)

    with open("report_test.html", 'w') as fid:
        print(rb.html_doc, file=fid)



if __name__ == "__main__":
    main()
import datetime

from typing import Any, Dict, Union


import dominate
from dominate.tags import *

import sas.sasview
import sasmodels

from sas.qtgui.Plotting.PlotterBase import Data1D

class ReportBuilder:
    def __init__(self, title: str):

        #
        # Set up the html document and general layout
        #

        self.html_doc = dominate.document(title=title)

        with self.html_doc.head:
            meta(http_equiv="Content-Type", content="text/html charset=utf-8")
            meta(name="Generator", content=f"SasView {sas.sasview.__version__}")

        with self.html_doc.body:
            with div(id="sasview"):
                h1(title)
                p(datetime.datetime.now().strftime("%I:%M%p, %B %d, %Y"))
                with div(id="version-info"):
                    p(f"sasview {sas.sasview.__version__}, sasmodels {sasmodels.__version__}", cls="sasview-details")

            div(id="perspective")
            div(id="data")
            h2("Data")

            with div(id="model"):
                div(id="model-details")
                div(id="model-parameters")

            div(id="figures")

    def add_data_details(self, data: Data1D):

        with self.html_doc.getElementById("data"):

            with div(cls="data-file"):
                h2(data.title)
                div(data.filename)

                with table():

                    with tr():
                        td("Q low")
                        td(getattr(data, "xmin", min(data.x))) # TODO: remove dynamically assigned field, xmin
                        td(data.x_unit)

                    with tr():
                        td("Q high")
                        td(getattr(data, "xmax", max(data.x))) # TODO: remove dynamically assigned field, xmax
                        td(data.x_unit)


    def add_table(self, parameters: Dict[str, Any]):
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

    print(rb.html_doc)

    with open("report_test.html", 'w') as fid:
        print(rb.html_doc, file=fid)



if __name__ == "__main__":
    main()
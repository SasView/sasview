import datetime

from typing import Any, Dict


import dominate
from dominate.tags import *

import sas.sasview
import sasmodels

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

            with div(id="model"):
                div(id="model-details")
                div(id="model-parameters")

            div(id="figures")

    def add_data_details(self, data):
        pass

    def add_table(self, parameters: Dict[str, Any]):
        with self.html_doc.getElementById("model-parameters"):
            with table():
                for key in sorted(parameters.keys()):
                    with tr():
                        th(key)
                        th(str(parameters[key])) # TODO decide on how to represent parameters


# Debugging tool
def main():
    rb = ReportBuilder("Test Report")
    rb.add_table({"A": 10, "B": 0.01, "C": 'stuff', "D": False})
    print(rb.html_doc)

    with open("report_test.html", 'w') as fid:
        print(rb.html_doc, file=fid)


if __name__ == "__main__":
    main()
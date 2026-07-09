import datetime

from ._resources import SAS_RESOURCES


class Legal:
    def __init__(self):
        year = datetime.datetime.now().year
        self.copyright = f"Copyright (c) 2009-{year}, SasView Developers"
        self.about = """
                <html>
                    <head/>
                    <body>
                        <p>
                            This work originally developed as part of the DANSE project funded by the NSF under
                             grant DMR-0520547, and currently maintained by UTK, NIST, UMD, ORNL, ISIS, ESS, ILL,
                             ANSTO, TU Delft, DLS, SciLifeLab, and the scattering community.
                        </p>
                        <p>
                            SasView also contains code developed with funding from the EU Horizon 2020 programme under
                             the SINE2020 project (Grant No 654000).
                        </p>
                    </body>
                </html>"""

    @property
    def credits_html(self) -> str:
        with SAS_RESOURCES.resource("system/credits.html") as res:
            # The data from pip-licenses should already be normalised to UTF-8
            # but it could have other encodings in it; here, we
            # - ensure that UTF-8 is used for the file regardless of the quirks
            #   of the underlying platform
            # - ensure reading the file is robust by coercing the data to
            #   UTF-8, replacing unknown codepoints with REPLACEMENT CHARACTER
            #   markers.
            return res.read_text(encoding='utf-8', errors='replace')


legal = Legal()

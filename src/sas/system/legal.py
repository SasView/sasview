import datetime


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



legal = Legal()

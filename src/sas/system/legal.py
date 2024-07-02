import datetime


class Legal:
    def __init__(self):
        year = datetime.datetime.now().year
        self.copyright = f"Copyright (c) 2009-{year}, SasView Developers"


legal = Legal()

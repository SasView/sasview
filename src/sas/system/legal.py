import datetime
from pathlib import Path

from ._resources import SAS_RESOURCES


class Legal:
    def __init__(self):
        year = datetime.datetime.now().year
        self.copyright = f"Copyright (c) 2009-{year}, SasView Developers"

    @property
    def credits_html(self) -> Path:
        return SAS_RESOURCES.resource("system/credits.html")


legal = Legal()

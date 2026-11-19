import logging

import requests
from packaging.version import Version, parse

from sas.system import config

logger = logging.getLogger("Web Configuration")

class WebLinks:
    def __init__(self):
        self.nist_url = "https://www.nist.gov/ncnr"
        self.umd_url = "https://www.umd.edu/"
        self.sns_url = "https://neutrons.ornl.gov/"
        self.nsf_url = "https://www.nsf.gov"
        self.isis_url = "https://www.isis.stfc.ac.uk/"
        self.ess_url = "https://europeanspallationsource.se/"
        self.ill_url = "https://www.ill.eu/"
        self.ansto_url = "https://www.ansto.gov.au/"
        self.bam_url = "https://www.bam.de/"
        self.delft_url = \
            "https://www.tudelft.nl/en/faculty-of-applied-sciences/business/facilities/reactor-institute-delft"
        self.inst_url = "https://www.utk.edu"
        self.diamond_url = "http://www.diamond.ac.uk"
        self.scilifelab_url = "https://www.scilifelab.se"

        self.homepage_url = "https://www.sasview.org"
        self.download_url = 'https://github.com/SasView/sasview/releases/latest'
        self.marketplace_url = "https://marketplace.sasview.org/"
        self.update_url = 'https://www.sasview.org/latestversion.json'

        self.help_email = "help@sasview.org"


def get_current_release_version() -> tuple[str, str, Version] | None:
    """ Get the current version from the server """
    try:
        response = requests.get(web.update_url, timeout=config.UPDATE_TIMEOUT)
        # Will throw Exception if the HTTP status code returned isn't success
        # (2xx)
        response.raise_for_status()
        version_info = response.json()
        logger.info("Connected to www.sasview.org. Received: %s", version_info)

        version_string = version_info["version"]
        url = version_info["download_url"]

        return version_string, url, parse(version_string)

    except Exception as ex:
        logger.info("Failed to get version number %s", ex)
        return None


web = WebLinks()


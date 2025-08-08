from logging import getLogger

from rest_framework.decorators import api_view

analysis_logger = getLogger(__name__)

@api_view(["GET"])
def list_analysis_done(request, version = None):
    return 0

#takes DataInfo and saves it into to specified file location

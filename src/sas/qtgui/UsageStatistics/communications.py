import json
import time

from sas.system.user import uid

from sas.system import config

def send_data(data: dict):
    """ Send usage data to the sasview server (and/or log locally)"""

    # Make sure we don't send if user has opted out
    if config.DO_USAGE_REPORT:

        message = {
            "uid": uid(),
            "time": time.time(),
            "data": data
        }

        message_data = json.dumps(message)

        # Save locally
        if config.LOCAL_REPORTING_FILENAME != "":
            with open(config.LOCAL_REPORTING_FILENAME, 'a') as fid:
                fid.write(message_data)
                fid.write("\n")

        # Send to server
        if config.REPORTING_SERVER != "":
            pass # TODO: send to server, implement server side first
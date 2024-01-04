from sas.qtgui.UsageStatistics.communications import send_data


def record_error(error_text: str):
    """ Send the record of an error to the server """
    data = {"error": error_text}
    send_data(data)
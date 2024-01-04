from sas.qtgui.UsageStatistics.communications import send_data

def record_usage(functionality: str, additional_info):
    """ Send a record of functionality being used to the server """
    data = {"usage-event": functionality,
            "data": additional_info}

    send_data(data)
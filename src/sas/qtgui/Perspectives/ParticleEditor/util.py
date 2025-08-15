def format_time_estimate(est_time_seconds):
    """Get easily understandable string for a computational time estimate"""
    # This is some silly code, but eh, why not
    #
    # I'm not even sure this is bad code, it's quite readable,
    # easily modifiable, relatively fast, and it is optimised for
    # smaller numbers, which is the bias we expect in the input

    est_time = est_time_seconds * 1_000_000
    time_units = "microsecond"

    if est_time < 1:
        # anything shorter than a microsecond, return as a decimal
        return "%.3g microseconds" % est_time

    # Everything else as an integer in nice units
    if est_time > 1000:
        est_time /= 1000
        time_units = "millisecond"

        if est_time > 1000:
            est_time /= 1000
            time_units = "second"

            if est_time > 60:
                est_time /= 60
                time_units = "minute"

                if est_time > 60:
                    est_time /= 60
                    time_units = "hour"

                    if est_time > 24:
                        est_time /= 24
                        time_units = "day"

                        if est_time > 7:
                            est_time /= 7
                            time_units = "week"

                            if est_time > 30 / 7:
                                est_time /= 30 / 7
                                time_units = "month"

                                if est_time > 365 / 30:
                                    est_time /= 365 / 30
                                    time_units = "year"

                                    if est_time > 100:
                                        est_time /= 100
                                        time_units = ("century", "centuries")

                                        if est_time > 10:
                                            est_time /= 10
                                            time_units = ("millennium", "millennia")

                                            if est_time > 1000:
                                                est_time /= 1000
                                                time_units = ("megaannum", "megaanna")

                                                if est_time > 230:
                                                    est_time /= 230
                                                    time_units = "galactic year"

                                                    if est_time > 13787 / 230:
                                                        est_time /= 13787 / 230
                                                        time_units = "universe age"

    rounded = int(est_time)
    if isinstance(time_units, str):
        if rounded == 1:
            unit = time_units
        else:
            unit = time_units + "s"
    else:
        if rounded == 1:
            unit = time_units[0]
        else:
            unit = time_units[1]

    return f"{rounded} {unit}"


if __name__ == "__main__":

    # time format demo
    t = 1e-9
    for i in range(100):
        t *= 2
        print(format_time_estimate(t))

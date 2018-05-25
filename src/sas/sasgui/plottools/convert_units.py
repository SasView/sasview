"""
    Convert units to strings that can be displayed
    This is a cleaned up version of unitConverter.py
"""


import re
import string

def convert_unit(power, unit):
    """
        Convert units to strings that can be displayed
    """
    if power != 0:
        if string.find(unit, "^") != -1:  # if the unit contains a powerer ^
            toks = re.split("\^", unit)
            if string.find(toks[0], "/") != -1 or \
                string.find(toks[0], "-") != -1:
                if power == 1:
                    unit = unit
                else:
                    unit = "(" + unit + ")" + "^{" + str(power) + "}"
            else:
                if string.find(toks[1], "{") != -1:  # if found a {
                    find_power_toks = re.split("{", toks[1])
                    if string.find(find_power_toks[1], "}") != -1:  # found }
                        unit_toks = re.split("}", find_power_toks[1])
                        if string.find(unit_toks[0], ".") != -1:
                            powerer = float(unit_toks[0]) * power
                        elif string.find(unit_toks[0], "/") != -1:
                            power_toks = re.split("/", unit_toks[0])
                            powerer = power * int(power_toks[0])\
                                            / int(power_toks[1])
                        else:
                            powerer = int(unit_toks[0]) * power

                        if powerer == 1.0:
                            unit = toks[0]
                        elif powerer == 0.5:
                            unit = toks[0] + "^{1/2}"
                        elif powerer == -0.5:
                            unit = toks[0] + "^{-1/2}"
                        else:
                            unit = toks[0] + "^{" + str(powerer) + "}"
                else:
                    raise ValueError("missing } in unit expression")
        else:  # no powerer
            if  power != 1:
                unit = "(" + unit + ")" + "^{" + str(power) + "}"
    else:
        raise ValueError("empty unit ,enter a powerer different from zero")
    return unit


if __name__ == "__main__":
    # pylint: disable=invalid-name
    # Input   ->  new scale  ->  Output
    unit1 = "A^{-1} "  #             x                    A^{-1}
    unit2 = "A"  #                   x                     A
    unit3 = "A"  #                   x^2                  A^{2}
    unit4 = "A "  #                  1/x                  A^{-1}
    unit5 = "A^{0.5} "  #        x^2                      A
    unit9 = "m^{1/2}"  #         x^2               m

    # If you don't recognize the pattern, give up
    # and just put some parentheses around the unit and write the transoformation:

    unit6 = "m/s"  #                x^2               (m/s)^{2}
    unit7 = "m/s^{2}"  #         1/x                 (m/s^{2})^{-1}
    unit8 = "m/s^{4}"  #         x^2               (m/s^{4})^{2}

    print("this unit1 %s ,its powerer %s , and value %s" % (unit1, 1, convert_unit(1, unit1)))
    print("this unit2 %s ,its powerer %s , and value %s" % (unit2, 1, convert_unit(1, unit2)))
    print("this unit3 %s ,its powerer %s , and value %s" % (unit3, 2, convert_unit(2, unit3)))
    print("this unit4 %s ,its powerer %s , and value %s" % (unit4, -1, convert_unit(-1, unit4)))
    print("this unit5 %s ,its powerer %s , and value %s" % (unit5, 2, convert_unit(2, unit5)))
    print("this unit6 %s ,its powerer %s , and value %s" % (unit6, 2, convert_unit(2, unit6)))
    print("this unit7 %s ,its powerer %s , and value %s" % (unit7, -1, convert_unit(-1, unit7)))
    print("this unit8 %s ,its powerer %s , and value %s" % (unit8, 2, convert_unit(2, unit8)))
    print("this unit9 %s ,its powerer %s , and value %s" % (unit9, 2, convert_unit(2, unit9)))

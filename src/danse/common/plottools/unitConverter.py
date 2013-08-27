import re
import string
#Input   ->  new scale  ->  Output

unit1 = "A^{-1} "  #             x                    A^{-1}
unit2 = "A"  #                   x                     A
unit3 = "A"  #                   x^2                  A^{2}
unit4 = "A "  #                  1/x                  A^{-1}
unit5 = "A^{0.5} "  #        x^2                      A
unit9 = "m^{1/2}"  #         x^2               m

#If you don't recognize the pattern, give up
# and just put some parentheses around the unit and write the transoformation:

unit6 = "m/s"  #                x^2               (m/s)^{2}
unit7 = "m/s^{2}"  #         1/x                 (m/s^{2})^{-1}
unit8 = "m/s^{4}"  #         x^2               (m/s^{4})^{2}


def UnitConvertion(pow, unit):
    """
    """
    if pow != 0:
        if string.find(unit, "^") != -1:  # if the unit contains a power ^
            unitSplitted = re.split("\^", unit)
            if string.find(unitSplitted[0], "/") != -1 or\
                string.find(unitSplitted[0], "-") != -1 :  # find slash /
                if pow == 1:
                    unit = unit
                else:
                    unit = "("+unit+")" + "^{"+ str(pow) + "}"
            else:
                if string.find(unitSplitted[1], "{") != -1:  # if found a {
                    findPower = re.split("{", unitSplitted[1])
                    if string.find(findPower[1], "}") != -1:  # found }
                        unitPower = re.split("}", findPower[1])
                        if(string.find(unitPower[0], ".") != -1):
                            power = float(unitPower[0]) * pow
                        elif(string.find(unitPower[0], "/") != -1):
                            #power is a float
                            poweSplitted = re.split("/", unitPower[0])
                            power = pow * int(poweSplitted[0])\
                                         /int(poweSplitted[1])
                        else:
                            power = int(unitPower[0]) * pow
                       
                        if power == 1.0:
                            unit = unitSplitted[0]
                        elif power == 0.5:
                            unit = unitSplitted[0] + "^{1/2}"
                        elif power == -0.5:
                            unit = unitSplitted[0] + "^{-1/2}"
                        else:
                            unit = unitSplitted[0] + "^{" + str(power) + "}"
                else:
                     raise ValueError, "missing } in unit expression"
        else:  # no power
            if  pow != 1:
                unit = "(" + unit + ")" + "^{" + str(pow) + "}"
    else:
        raise ValueError, "empty unit ,enter a power different from zero"
    return unit


if __name__ == "__main__": 
    print "this unit1 %s ,its power %s , and value %s" % (unit1,
                                                1, UnitConvertion(1, unit1))
    print "this unit2 %s ,its power %s , and value %s" % (unit2, 1,
                                                UnitConvertion(1, unit2))
    print "this unit3 %s ,its power %s , and value %s" % (unit3, 2,
                                                    UnitConvertion(2, unit3))
    print "this unit4 %s ,its power %s , and value %s" % (unit4, -1,
                                                UnitConvertion(-1, unit4))
    print "this unit5 %s ,its power %s , and value %s" % (unit5, 2,
                                                    UnitConvertion(2, unit5))
    print "this unit6 %s ,its power %s , and value %s" % (unit6, 2,
                                                    UnitConvertion(2, unit6))
    print "this unit7 %s ,its power %s , and value %s" % (unit7, -1,
                                                    UnitConvertion(-1, unit7))
    print "this unit8 %s ,its power %s , and value %s" % (unit8, 2,
                                                    UnitConvertion(2, unit8))
    print "this unit9 %s ,its power %s , and value %s" % (unit9, 2,
                                                    UnitConvertion(2, unit9))

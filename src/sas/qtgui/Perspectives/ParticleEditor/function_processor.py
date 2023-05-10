import inspect
from typing import Callable
import numpy as np

class FunctionDefinitionFailed(Exception):
    def __init__(self, *args):
        super()

# Valid parameterisataions of the sld function,
# because of how things are checked, the names of
# the fist parameter currently has to be distinct.
# things could be changed to make it otherwise, but
# at the moment this seems reasonble

parameter_sets = [["x", "y", "z"], ["r", "theta", "phi"]]


def cartesian_converter(x,y,z):
    return x,y,z


def spherical_converter(x,y,z):
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arccos(z/r)
    phi = np.sign(y)*np.arccos(x / np.sqrt(x**2 + y**2))

    return r, theta, phi

parameter_converters = [cartesian_converter, spherical_converter]

#
# Main processor
#

def process_text(input_text: str):
    new_locals = {}
    new_globals = {}

    exec(input_text, new_globals, new_locals)
    # print(ev)
    # print(new_globals)
    # print(new_locals)

    # look for function
    if "sld" not in new_locals:
        raise FunctionDefinitionFailed("No function called 'sld' found")

    sld_function = new_locals["sld"]

    if not isinstance(sld_function, Callable):
        raise FunctionDefinitionFailed("sld object exists, but is not Callable")

    # Check for acceptable signatures
    sig = inspect.signature(sld_function)

    params = list(sig.parameters.items())

    # check for first parameter being equal to one of the acceptable options
    # this assumes that there are only
    parameter_set_index = -1
    for index, parameter_set in enumerate(parameter_sets):
        if params[0][0] == parameter_set[0]:
            parameter_set_index = index

    if parameter_set_index < 0:
        s = " or ".join([("("+", ".join(v) + ")") for v in parameter_sets])
        raise FunctionDefinitionFailed("sld function not correctly parameterised, first three parameters must be "+s)

    parameter_set = parameter_sets[parameter_set_index]

    for i in range(3):
        if params[i][0] != parameter_set[i]:
            s = ", ".join(parameter_set)
            raise FunctionDefinitionFailed(f"Parameter {i+1} should be {parameter_set[i]} for ({s}) parameterisation")

    converter = parameter_converters[parameter_set_index]

    #
    # gather parameters
    #

    remaining_parameter_names = [x[0] for x in params[3:]]

    return sld_function, converter, remaining_parameter_names

test_text_valid_sld_xyz = """

print("test print string")

def sld(x,y,z,p1,p2,p3):
    print(x,y,z)

"""

test_text_valid_sld_radial = """
def sld(r,theta,phi,p1,p2,p3):
    print(x,y,z)

"""


test_text_invalid_start_sld = """
def sld(theta,phi,p1,p2,p3):
    print(x,y,z)

"""

test_text_invalid_rest_sld = """
def sld(r,p1,p2,p3):
    print(x,y,z)

"""

test_sld_class = """

class SLD:
    def __call__(self,x,y,z):
        print(x,y,z)

sld = SLD()

"""

test_bad_class = """

class SLD:
    def __call__(self,x,y,q):
        print(x,y,z)

sld = SLD()

"""


x = process_text(test_text_valid_sld_xyz)
# x = process_text(test_text_valid_sld_radial)
# x = process_text(test_text_invalid_start_sld)
# x = process_text(test_text_invalid_rest_sld)
# x = process_text(test_bad_class)

print(x)


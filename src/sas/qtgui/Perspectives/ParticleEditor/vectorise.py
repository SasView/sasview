import traceback
from collections.abc import Callable

import numpy as np

test_n = 7

def clean_traceback(trace: str):
    """ Tracebacks from vectorise contain potentially confusing information from the
    vectorisation infrastructure. Clean it up and replace empty filename with something else"""


    parts = trace.split('File "<string>"')[1:]

    return "".join(["Input data" + part for part in parts])


def vectorise_sld(fun: Callable,
                  warning_callback: Callable[[str], None],
                  error_callback: Callable[[str], None],
                  *args, **kwargs):
    """ Check whether an SLD function can handle numpy arrays properly,
    if not, create a wrapper that that can"""

    # Basically, the issue is with if statements,
    # and we're looking for a ValueError with certain text

    input_values = np.zeros((test_n,))

    try:
        output = fun(input_values, input_values, input_values, *args, **kwargs)

        if not isinstance(output, np.ndarray):
            return None

        elif output.shape != (test_n,):
            return None

        else:
            return fun

    except ValueError as ve:
        # Check for a string that signifies a problem with parallelisation
        if ve.args[0].startswith("The truth value of an array"):
            # check it works with basic values
            try:
                fun(0, 0, 0, *args, **kwargs)


                def vectorised(x,y,z,*args,**kwargs):
                    out = np.zeros_like(x)
                    for i, (xi,yi,zi) in enumerate(zip(x,y,z)):
                        out[i] = fun(xi, yi, zi, *args, **kwargs)
                    return out

                warning_callback("The specified SLD function does not handle vector values of coordinates, "
                                 "a vectorised version has been created, but is probably **much** slower than "
                                 "one that uses numpy (np.) functions. See the vectorisation example for "
                                 "more details.")

                return vectorised

            except:
                error_callback("Function raises error when executed:\n"+clean_traceback(traceback.format_exc()))

        else:
            error_callback("Function raises error when executed:\n"+clean_traceback(traceback.format_exc()))

    except Exception:
        error_callback("Function raises error when executed:\n"+clean_traceback(traceback.format_exc()))

def vectorise_magnetism(fun: Callable, warning_callback: Callable[[str], None], *args, **kwargs):
    """ Check whether a magnetism function can handle numpy arrays properly,
    if not, create a wrapper that that can"""
    pass

def main():

    def vector_sld(x, y, z):
        return x+y+z

    def non_vector_sld(x,y,z):
        if x > y:
            return 1
        else:
            return 0

    def bad_sld(x,y,z):
        return 7

    print(vectorise_sld(vector_sld, print, print))
    print(vectorise_sld(non_vector_sld, print, print))
    print(vectorise_sld(bad_sld, print, print))


if __name__ == "__main__":
    main()

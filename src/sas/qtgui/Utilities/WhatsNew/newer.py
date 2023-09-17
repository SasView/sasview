from typing import Tuple
import re

def reduced_version(version_string: str) -> Tuple[int, int, int]:
    """ Convert a version string into the three numbers we care about for the purposes
    of the WhatsNew dialog (i.e. strip a,b suffixes etc, make into three ints"""

    version_string = re.sub(r"[^\.0-9]+.*", "", version_string)
    
    parts = version_string.split(".")

    if len(parts) > 3:
        raise ValueError(f"{version_string} not a valid version string")


    parts = [int(part) for part in parts]

    return tuple(parts + [0]*(3-len(parts)))


def strictly_newer_than(version_a: str, version_b: str) -> bool:
    """ Is the version string "version_a" string strictly newer than "version_b" """

    numeric_a = reduced_version(version_a)
    numeric_b = reduced_version(version_b)

    for i in range(3):
        if numeric_a[i] > numeric_b[i]:
            return True
        elif numeric_a[i] < numeric_b[i]:
            return False

    return False

def newest(version_a: str, version_b: str) -> str:
    """Return the newest of two versions by the comparison used in the what's new box,
     if they are equally new, return the first one.
    """

    if strictly_newer_than(version_b, version_a):
        return version_b

    return version_a
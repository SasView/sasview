#!/usr/bin/env python
"""
Utilities for path manipulation. Not to be confused with the pathutils module
from the pythonutils package (http://groups.google.com/group/pythonutils).
"""

# NOTE: If enough of _that_ pathutils functionality is required, we can switch
# this module for that one.

# TODO: Make algorithm more robust and complete; consider using abspath.

__all__ = ['relpath']

from os.path import join, sep


def relpath(p1, p2):
    """Compute the relative path of p1 with respect to p2."""

    def commonpath(L1, L2, common=[]):
        if len(L1) < 1:
            return (common, L1, L2)
        if len(L2) < 1:
            return (common, L1, L2)
        if L1[0] != L2[0]:
            return (common, L1, L2)
        return commonpath(L1[1:], L2[1:], common=common+[L1[0]])

    # if the strings are equal, then return "."
    if p1 == p2:
        return "."
    (common,L1,L2) = commonpath(p2.split(sep), p1.split(sep))
    # if there is nothing in common, then return an empty string
    if not common:
        return ""
    # otherwise, replace the common pieces with "../" (or "..\")
    p = [(".."+sep) * len(L1)] + L2
    return join(*p)

def test():
    p1 = sep.join(["a","b","c","d"])
    p2 = sep.join(["a","b","c1","d1"])
    p3 = sep.join(["a","b","c","d","e"])
    p4 = sep.join(["a","b","c","d1","e"])
    p5 = sep.join(["w","x","y","z"])

    assert relpath(p1, p1) == "."
    assert relpath(p2, p1) ==  sep.join(["..", "..", "c1", "d1"])
    assert relpath(p3, p1) == "e"
    assert relpath(p4, p1) ==  sep.join(["..", "d1", "e"])
    assert relpath(p5, p1) == ""

if __name__ == '__main__':
    test()

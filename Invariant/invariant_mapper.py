"""
This module is a wrapper to a map function. It allows to loop through 
different invariant objects to call the same function
"""


def get_qstar(inv, extrapolation=None):
    """
    Get invariant value (Q*)
    """
    return inv.get_qstar(extrapolation)

def get_qstar_with_error(inv, extrapolation=None):
    """
    Get invariant value with uncertainty
    """
    return inv.get_qstar_with_error(extrapolation)

def get_volume_fraction(inv, contrast, extrapolation=None):
    """
    Get volume fraction
    """
    return inv.get_volume_fraction(contrast, extrapolation)

def get_volume_fraction_with_error(inv, contrast, extrapolation=None):
    """
    Get volume fraction with uncertainty
    """
    return inv.get_volume_fraction_with_error(contrast,
                                                    extrapolation)

def get_surface(inv, contrast, porod_const, extrapolation=None):
    """
    Get surface with uncertainty
    """
    return inv.get_surface(contrast=contrast,
                                      porod_const=porod_const,
                                      extrapolation=extrapolation)

def get_surface_with_error(inv, contrast, 
                           porod_const, extrapolation=None):
    """
    Get surface with uncertainty
    """
    return inv.get_surface_with_error(contrast=contrast,
                                      porod_const=porod_const,
                                      extrapolation=extrapolation)


from packaging.version import InvalidVersion, Version, parse


def reduced_version(version_string: str) -> tuple[int, int, int]:
    """ Convert a version string into the three numbers we care about for the purposes
    of the WhatsNew dialog (i.e. strip a,b suffixes etc, make into three ints"""

    try:
        version = parse(version_string)
    except InvalidVersion:
        raise ValueError(f"{version_string} not a valid version string")

    return (version.major, version.minor, version.micro)


def strictly_newer_than(version_a: str, version_b: str) -> bool:
    """ Is the version string "version_a" string strictly newer than "version_b" """

    return Version(version_a) > Version(version_b)


def newest(version_a: str, version_b: str) -> str:
    """Return the newest of two versions by the comparison used in the what's new box,
     if they are equally new, return the first one.
    """

    if strictly_newer_than(version_b, version_a):
        return version_b

    return version_a

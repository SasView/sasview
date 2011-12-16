__version__ = "2.0.1"

try:
    import pkg_resources
    d = pkg_resources.get_distribution("sansview")
    rev = int(d.parsed_version[5])
    __build__ = str(rev)
except:
    __build__ = "1"
from enum import Enum


class OS(Enum):
    WIN = 0
    LINUX = 1
    MAC = 2
    UNKNOWN = 3

def get_os():
    """
    Get the operating system of the current machine.
    """
    import platform
    if platform.system() == "Windows":
        return OS.WIN
    elif platform.system() == "Linux":
        return OS.LINUX
    elif platform.system() == "Darwin":
        return OS.MAC
    return OS.UNKNOWN

def get_shared_lib_extension():
    """
    Get the shared library extension for the current operating system, including the dot.
    If the operating system is unknown, return an empty string.
    """
    _os = get_os()
    if _os == OS.WIN:
        return ".dll"
    elif _os == OS.LINUX:
        return ".so"
    elif _os == OS.MAC:
        return ".dylib"
    return ""

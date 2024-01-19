import requests
import os

from enum import Enum
class OS(Enum):
    WIN = 0
    LINUX = 1
    MAC = 2
    UNKNOWN = 3

def determine_os():
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

def get_ausaxs():
    _os = determine_os()

    url = "https://github.com/SasView/ausaxs/releases/latest/download/"
    libs = None
    if _os == OS.WIN:
        libs = ["libausaxs_avx.dll", "libausaxs_sse.dll"]
    elif _os == OS.LINUX:
        libs = ["libausaxs_avx.so", "libausaxs_sse.so"]
    elif _os == OS.MAC:
        libs = ["libausaxs_avx.dylib", "libausaxs_sse.dylib"]
    if libs is not None:
        os.makedirs("external", exist_ok=True)
        for lib in libs:
            response = requests.get(url+lib)
            with open("external/"+lib, "wb") as f:
                f.write(response.content)
    print("##########################################################################")
    print("##########################################################################")
    print(f"downloaded ausaxs libraries to {os.getcwd()}/external")
    print("##########################################################################")
    print("##########################################################################")

def get_external_dependencies(): 
    # surround with try/except to avoid breaking the build if the download fails
 #   try:
    get_ausaxs()
#    except Exception as e:
        # print(e)
    return
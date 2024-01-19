import requests

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
#        base_loc = resources.files("sas.sascalc.calculator.ausaxs.lib")
        # we have to use a relative path since the package is not installed yet
        base_loc = "src/sas/sascalc/calculator/ausaxs/lib/"
        import os
        print("###CWD: ", os.getcwd())
        for lib in libs:
            response = requests.get(url+lib)
#            with resources.as_file(base_loc) as loc:
            with open(base_loc+lib, "wb") as f:
                f.write(response.content)
                print("PLACED AUSAXS LIBRARY AT: ", base_loc+lib)

def fetch_external_dependencies(): 
    #surround with try/except to avoid breaking the build if the download fails
    try:
        get_ausaxs()
    except Exception as e:    
        print("Download of external dependencies failed.", e)
        raise e
    return
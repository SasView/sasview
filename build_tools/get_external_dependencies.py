import requests
import os

def get_ausaxs():
    from sas.sascalc.calculator.ausaxs import architecture
    _os = architecture.determine_os()
    arch = architecture.determine_cpu_support()

    url = "https://github.com/SasView/ausaxs/releases/latest/download/"
    libs = None
    if _os == architecture.OS.WIN:
        libs = ["libausaxs_avx.dll", "libausaxs_sse.dll"]
    elif _os == architecture.OS.LINUX:
        libs = ["libausaxs_avx.so", "libausaxs_sse.so"]
    elif _os == architecture.OS.MAC:
        libs = ["libausaxs_avx.dylib", "libausaxs_sse.dylib"]
    if libs is not None:
        os.makedirs("external", exist_ok=True)
        for lib in libs:
            response = requests.get(url+lib)
            with open("external/"+lib, "wb") as f:
                f.write(response.content)

def get_external_dependencies(): 
    # surround with try/except to avoid breaking the build if the download fails
    try:
        get_ausaxs()
    except:
        return